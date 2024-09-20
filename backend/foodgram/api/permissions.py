from rest_framework import permissions
from rest_framework.permissions import (BasePermission,
                                        IsAuthenticatedOrReadOnly)


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение на обновление и удаление объекта только для его автора.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class UserPermission(BasePermission):
    """
    Разрешение для доступа к списку пользователей без аутентификации,
    но требующее аутентификацию для /users/me/.
    """
    def has_permission(self, request, view):
        if view.action == 'me':
            return request.user.is_authenticated
        return True
