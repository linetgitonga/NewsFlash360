from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of an object to edit it.
    Admin users can edit any object.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin users can edit any object
        if request.user.is_staff:
            return True
            
        # Write permissions are only allowed to the author
        return obj.author == request.user


class IsNotFlagged(permissions.BasePermission):
    """
    Custom permission to prevent editing of flagged content.
    Only admins can edit flagged content.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin users can edit any object
        if request.user.is_staff:
            return True
            
        # If object is flagged, only admins can edit
        if hasattr(obj, 'status') and obj.status == 'flagged':
            return False
            
        return True