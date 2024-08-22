import os
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets
from .serializers import *
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer
from .models import UserData
from .models import Todo
from .email import send_otp_via_mail
from django.dispatch import receiver
from django.db.models.signals import post_delete
from rest_framework import status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .permission import IsManagerOrReadOnly,IsManager

class MyTokenObtainPairViews(TokenObtainPairView):
    serializer_class=MyTokenObtainPairSerializer

class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            send_otp_via_mail(serializer.data['email'])
            if serializer.data['is_staff']:
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

class ManagerEmployeeListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsManager]
    def get(self, request):
        active_employees = UserData.objects.filter(is_active=True,is_staff=False)
        serializer = UserSerializer(active_employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AssignTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsManager]

    def post(self, request):
        if not request.user.is_staff:
            raise PermissionDenied("Only managers can assign tasks.")
        
        serializer = TodoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(assigned_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, user_id=None):
        if not request.user.is_staff:
            raise PermissionDenied("Only managers can view assigned tasks.")
        
        if user_id:
            todos = Todo.objects.filter(assigned_by=request.user, assigned_to=user_id)
            serializer = TodoSerializer(todos, many=True)
            return Response(serializer.data)
        else:
            return Response({"detail": "No user ID provided."}, status=status.HTTP_400_BAD_REQUEST)

class EmployeeTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        todos = Todo.objects.filter(assigned_to=request.user)
        serializer = TodoSerializer(todos, many=True)
        return Response(serializer.data)

    def patch(self, request, pk):
        todo = get_object_or_404(Todo, pk=pk, assigned_to=request.user)
        serializer = PartialTodoSerializer(todo, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

@receiver(post_delete, sender=Todo)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Todo` object is deleted.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
