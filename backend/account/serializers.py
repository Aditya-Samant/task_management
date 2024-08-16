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
    user_type = serializers.ChoiceField(choices=[('employee', 'Employee'), ('manager', 'Manager')], write_only=True)

    class Meta:
        model = UserData
        fields = ["id", "email", "name", "password", "user_type"]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        user = UserData.objects.create(
            email=validated_data["email"], 
            name=validated_data["name"]
        )
        user.set_password(validated_data["password"])
        if user_type == 'manager':
            user.is_staff = True  # Assuming is_staff indicates manager privileges
            user.is_active = False  # Manager needs approval
            user.is_approved = False  # Manager needs approval
        user.save()
        return user

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

class TodosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        exclude = ["assigned_by","assigned_to"]
        read_only_fields = ["id"]
