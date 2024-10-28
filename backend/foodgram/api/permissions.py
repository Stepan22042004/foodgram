from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user


class UserPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'me':
            return request.user.is_authenticated
        else:
            return True
