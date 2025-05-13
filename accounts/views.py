import uuid
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserVerification
from .serializers import (
    UserSerializer, UserCreateSerializer, LoginSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, EmailVerificationSerializer
)

User = get_user_model()


class RegisterView(APIView):
    """API view for user registration."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate verification token
            token = uuid.uuid4().hex
            expiry = timezone.now() + timedelta(days=1)
            
            # Save verification token
            UserVerification.objects.create(
                user=user,
                token=token,
                expires_at=expiry,
                type='email'
            )
            
            # Send verification email
            verification_url = f"{request.scheme}://{request.get_host()}/api/auth/verify-email/?token={token}"
            send_mail(
                subject="NewsFlash360 - Verify Your Email",
                message=f"Please click on the link below to verify your email:\n\n{verification_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email]
            )
            
            return Response(
                {"message": "User registered successfully. Please verify your email."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """API view for user login."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                # Update last login IP
                user.last_login_ip = self.get_client_ip(request)
                user.save()
                
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            else:
                return Response(
                    {"error": "Invalid credentials"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserProfileView(APIView):
    """API view for user profile operations."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """API view for changing user password."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Check if current password is valid
            if not user.check_password(serializer.validated_data['current_password']):
                return Response(
                    {"error": "Current password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({"message": "Password changed successfully."})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """API view for requesting a password reset."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Generate reset token
                token = uuid.uuid4().hex
                expiry = timezone.now() + timedelta(hours=1)
                
                # Save reset token
                UserVerification.objects.create(
                    user=user,
                    token=token,
                    expires_at=expiry,
                    type='reset'
                )
                
                # Send reset email
                reset_url = f"{request.scheme}://{request.get_host()}/reset-password/?token={token}"
                send_mail(
                    subject="NewsFlash360 - Password Reset",
                    message=f"Please click on the link below to reset your password:\n\n{reset_url}\n\nThis link will expire in 1 hour.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email]
                )
                
            except User.DoesNotExist:
                # Don't reveal if email exists or not for security
                pass
            
            return Response({"message": "If your email exists in our system, you will receive a password reset link."})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """API view for confirming a password reset."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                verification = UserVerification.objects.get(
                    token=token,
                    type='reset',
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                
                # Update user password
                user = verification.user
                user.set_password(new_password)
                user.save()
                
                # Mark token as used
                verification.is_used = True
                verification.save()
                
                return Response({"message": "Password has been reset successfully."})
                
            except UserVerification.DoesNotExist:
                return Response(
                    {"error": "Invalid or expired token"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """API view for verifying user email."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response(
                {"error": "Token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            verification = UserVerification.objects.get(
                token=token,
                type='email',
                is_used=False,
                expires_at__gt=timezone.now()
            )
            
            # Mark email as verified
            user = verification.user
            user.is_verified = True
            user.save()
            
            # Mark token as used
            verification.is_used = True
            verification.save()
            
            return Response({"message": "Email verified successfully"})
            
        except UserVerification.DoesNotExist:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                verification = UserVerification.objects.get(
                    token=token,
                    type='email',
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                
                # Mark email as verified
                user = verification.user
                user.is_verified = True
                user.save()
                
                # Mark token as used
                verification.is_used = True
                verification.save()
                
                return Response({"message": "Email verified successfully"})
                
            except UserVerification.DoesNotExist:
                return Response(
                    {"error": "Invalid or expired token"},
                    status=status.HTTP_400_BAD_REQUEST
                )


class ResendVerificationEmailView(APIView):
    """API view for resending verification email."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_verified:
                return Response(
                    {"message": "Email is already verified"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate new verification token
            token = uuid.uuid4().hex
            expiry = timezone.now() + timedelta(days=1)
            
            # Save verification token
            UserVerification.objects.create(
                user=user,
                token=token,
                expires_at=expiry,
                type='email'
            )
            
            # Send verification email
            verification_url = f"{request.scheme}://{request.get_host()}/api/auth/verify-email/?token={token}"
            send_mail(
                subject="NewsFlash360 - Verify Your Email",
                message=f"Please click on the link below to verify your email:\n\n{verification_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email]
            )
            
            return Response({"message": "Verification email has been resent."})
            
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            return Response({"message": "If your email exists in our system, you will receive a verification link."})


class LogoutView(APIView):
    """API view for user logout."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Simply return a success message as JWT tokens are stateless
        # Client should delete the tokens from their storage
        return Response({"message": "Successfully logged out."})