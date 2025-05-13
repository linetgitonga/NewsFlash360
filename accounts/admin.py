from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserVerification

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_verified', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified', 'preferred_language')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'phone_number', 'bio', 'profile_picture'
        )}),
        (_('Preferences'), {'fields': (
            'preferred_language', 'county', 'town',
            'receive_email_notifications', 'receive_push_notifications'
        )}),
        (_('Permissions'), {'fields': (
            'is_active', 'is_staff', 'is_superuser', 'is_verified',
            'groups', 'user_permissions'
        )}),
        (_('Important dates'), {'fields': ('last_login', 'last_login_ip')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'created_at', 'expires_at', 'is_used')
    list_filter = ('type', 'is_used', 'created_at')
    search_fields = ('user__email', 'token')
    ordering = ('-created_at',)
    readonly_fields = ('token', 'created_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'type', 'token', 'is_used')
        }),
        (_('Timing'), {
            'fields': ('created_at', 'expires_at')
        }),
    )