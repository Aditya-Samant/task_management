from venv import logger, logging
from rest_framework import serializers
from .models import UserData, Todo
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["name"] = user.name
        token['is_staff'] = user.is_staff
        return token
    def validate(self, attrs):
        User = get_user_model()
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('No account found with the given credentials')

        if not user.is_active:
            raise serializers.ValidationError('User account is not active, please verify your email')

        if user.is_staff and not user.is_approved:
            raise serializers.ValidationError('Manager approval is pending, !!contact admin!! Token cannot be created.')

        if not check_password(password, user.password):
            raise serializers.ValidationError('Invalid password')

        logger.debug(f"Authentication successful for user: {user.email}")

        return super().validate(attrs)


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        fields = ["id", "email", "name", "password", "is_staff"]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = UserData(
            email=validated_data["email"], 
            name=validated_data["name"],
            is_staff=validated_data['is_staff']
        )
        user.set_password(validated_data["password"])
        if user.is_staff:
            user.is_approved = False  # Manager needs approval
        user.save()
        return user



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        fields = ['id',  'email', 'name', 'is_active']

class PartialTodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ['image', 'status']
        read_only_fields = [field.name for field in Todo._meta.fields if field.name not in ['image', 'status']]


class VerifyOtpSerializer(serializers.Serializer):
    email=serializers.EmailField()
    otp=serializers.CharField()

class ResendOtpSerializer(serializers.Serializer):
    email=serializers.EmailField()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField()

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        # fields = "__all__" 
        exclude = ["assigned_by"]
        # read_only_fields = ["id","assigned_by","assigned_to"]
    
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
    
    def save(self, **kwargs):
        request = self.context.get('request')
        if request and not self.instance:
            self.validated_data['assigned_by'] = request.user
        return super().save(**kwargs)