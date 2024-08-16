from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets
from .serializers import *
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer
from .models import Todo,UserData
from .email import send_otp_via_mail
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .permission import IsManagerOrReadOnly,IsManager

class MyTokenObtainPairViews(TokenObtainPairView):
    serializer_class=MyTokenObtainPairSerializer
    
    
class AssignTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsManager]

    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only managers can assign tasks.")
        
        serializer = TodosSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(assigned_by=request.user)
        return Response(serializer.data)

# view for registering users
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            send_otp_via_mail(serializer.data['email'])
            if serializer.validated_data['user_type'] == 'manager':
                return Response({"message": "Manager registration request submitted. Awaiting approval."}, status=status.HTTP_201_CREATED)
            return Response({"message": "Employee registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ResendOtp(APIView):
    def post(self,request):
        serializer=ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email=serializer.data['email']
        user=UserData.objects.filter(email=email)
        if not user.exists():
            return Response({
                    "message":"invalid user "
                },status=status.HTTP_400_BAD_REQUEST)
        send_otp_via_mail(email)
        return Response({
                    "message":"otp sent successfully"
                },status=status.HTTP_200_OK)
    
class VerifyOTPView(APIView):
    def post(self,request):
        data=request.data 
        serializer=VerifyOtpSerializer(data=data)
        if serializer.is_valid():
            email=serializer.data['email']
            otp=serializer.data['otp']
            user=UserData.objects.filter(email=email)
            if not user.exists():
                return Response({
                    "message":"invalid user "
                },status=status.HTTP_400_BAD_REQUEST)
            if not otp==user[0].otp:
                return Response({
                    "message":"invalid otp "
                },status=status.HTTP_400_BAD_REQUEST)
            expiration_time = timezone.now() - timezone.timedelta(minutes=10)  # OTP expires after 10 minutes
            if user[0].otp_created_at < expiration_time:
                send_otp_via_mail(email)
                return Response({
                    "message": "OTP expired!!! New opt has been sent"
                },status=status.HTTP_400_BAD_REQUEST)
            user=user.first()
            if user.is_active==True:
                return Response({
                    "message":"user is already verified"
                },status=status.HTTP_200_OK)
            user.is_active=True
            user.otp = None
            user.otp_created_at = None
            user.save()
            return Response({
                    "message":"user verified successfully"
                })
        return Response({
                    "status":400,
                    "message":serializer.errors
                },status=status.HTTP_200_OK) 

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = UserData.objects.filter(email=email).first()
            if user:
                send_otp_via_mail(email)
                return Response({
                    "message": "OTP sent to your email for password reset"
                },status=status.HTTP_200_OK)
            return Response({
                "message": "User with this email does not exist"
            },status=status.HTTP_404_NOT_FOUND)
        return Response({
            "message": serializer.errors
        },status=status.HTTP_400_BAD_REQUEST)
    
class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            user = UserData.objects.filter(email=email).first()
            if not user:
                return Response({
                    "message": "User with this email does not exist"
                },status=status.HTTP_404_NOT_FOUND)
            
            if user.otp != otp:
                return Response({
                    "message": "Invalid OTP"
                },status=status.HTTP_400_BAD_REQUEST)
            expiration_time = timezone.now() - timezone.timedelta(minutes=10)  # OTP expires after 10 minutes
            if user.otp_created_at < expiration_time:
                return Response({
                    "message": "OTP expired"
                },status=status.HTTP_400_BAD_REQUEST)
            subject="Your password change request"
            message=f"password changed successfully"
            email_from=settings.EMAIL_HOST
            send_mail(subject,message,email_from,[email])
            user.set_password(new_password)
            user.otp = None  # Clear the OTP after successful password reset
            user.save()
            
            return Response({
                "message": "Password reset successful"
            },status=status.HTTP_200_OK)
        
        return Response({
            "message": serializer.errors
        },status=status.HTTP_400_BAD_REQUEST)

class TodosViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsManagerOrReadOnly]
    serializer_class = TodosSerializer

    def get_queryset(self):
        return Todo.objects.filter(assigned_to=self.request.user)

    def perform_create(self, serializer):
        serializer.save(assigned_to=self.request.user)

    def check_object_permissions(self, request, obj):
        if obj.assigned_to != request.user:
            raise PermissionDenied("You do not have permission to access this todo.")
    
