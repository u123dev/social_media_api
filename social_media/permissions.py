from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerUserOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return request.method in SAFE_METHODS or obj == request.user


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return (
            request.method in SAFE_METHODS
            or obj == request.user
            or obj.user == request.user
        )
