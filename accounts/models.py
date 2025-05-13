from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with email as the unique identifier instead of username."""
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    # Language preferences for content
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('sw', 'Swahili'),
        ('sheng', 'Sheng'),
    ]
    preferred_language = models.CharField(
        max_length=10, 
        choices=LANGUAGE_CHOICES,
        default='en'
    )
    
    # Geographical preferences for news
    county = models.CharField(max_length=50, blank=True)
    town = models.CharField(max_length=50, blank=True)
    
    # Notification settings
    receive_email_notifications = models.BooleanField(default=True)
    receive_push_notifications = models.BooleanField(default=True)
    
    # User analytics
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


class UserVerification(models.Model):
    """Model for verifying user email and password reset."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    type = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email Verification'),
            ('reset', 'Password Reset'),
        ]
    )
    
    def __str__(self):
        return f"{self.user.email} - {self.type} - {self.created_at}"
    
    class Meta:
        verbose_name = _('user verification')
        verbose_name_plural = _('user verifications')