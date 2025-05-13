from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserVerification

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number', 
            'bio', 'profile_picture', 'date_joined', 'is_verified', 
            'preferred_language', 'county', 'town', 
            'receive_email_notifications', 'receive_push_notifications'
        ]
        read_only_fields = ['id', 'date_joined', 'is_verified']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user."""
    
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'confirm_password', 'first_name', 
            'last_name', 'phone_number', 'preferred_language', 
            'county', 'town'
        ]
    
    def validate(self, data):
        """Validate that the passwords match."""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate password strength
        try:
            validate_password(data['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': list(e)})
        
        return data
    
    def create(self, validated_data):
        """Create a new user with encrypted password."""
        # Remove confirm_password from the data as it's not part of the User model
        validated_data.pop('confirm_password')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            **{k: v for k, v in validated_data.items() if k != 'password'}
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)
    
    def validate(self, data):
        """Validate that the new passwords match."""
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match.")
        
        # Validate password strength
        try:
            validate_password(data['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e)})
        
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset."""
    
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset."""
    
    token = serializers.CharField()
    new_password = serializers.CharField()
    confirm_new_password = serializers.CharField()
    
    def validate(self, data):
        """Validate that the new passwords match."""
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match.")
        
        # Validate password strength
        try:
            validate_password(data['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e)})
        
        return data


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for verifying user email."""
    
    token = serializers.CharField()