from rest_framework import permissions
from rest_framework.permissions import (BasePermission,
                                        IsAuthenticatedOrReadOnly)


class UserPermission(BasePermission):

    def has_permission(self, request, view):
        if view.action == 'me':
            return request.user.is_authenticated
        return True


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
