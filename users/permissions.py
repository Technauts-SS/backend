from rest_framework import permissions
from .models import User

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.creator == request.user

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.creator == request.user

class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.MODERATOR, 
            User.Role.ADMIN
        ]

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.ADMIN

class IsModeratorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.MODERATOR,
            User.Role.ADMIN
        ]

class IsCampaignModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        if view.action in ['approve', 'reject']:
            return request.user.role in [User.Role.MODERATOR, User.Role.ADMIN]
        return True

class IsDonationOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

class IsSameUserOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or (
            request.user.is_authenticated and 
            request.user.role == User.Role.ADMIN
        )