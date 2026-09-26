from rest_framework import permissions


class IsWorker(permissions.BasePermission):
    message = "Only workers can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_worker


class IsSupervisor(permissions.BasePermission):
    message = "Only supervisors can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_supervisor


class IsAdminRole(permissions.BasePermission):
    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin_role


class IsSupervisorOrAdmin(permissions.BasePermission):
    message = "Supervisors or administrators only."

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_supervisor or request.user.is_admin_role
        )


class CanChangeHazardStatus(permissions.BasePermission):
    """Only supervisors/admins can change status. Workers cannot."""

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if "status" in request.data and not (
            user.is_supervisor or user.is_admin_role
        ):
            return False
        return True