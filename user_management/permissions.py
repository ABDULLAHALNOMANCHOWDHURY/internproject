from rest_framework import permissions


def is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or user.user_type == user.UserType.ADMIN
    )


def is_staff_with_perm(user, codename):
    """True if user is an admin, or a staff member whose role grants `codename`
    (e.g. 'user_management.ban_user'), or a super_admin staff profile."""
    if is_admin(user):
        return True
    if not user.is_authenticated or user.user_type != user.UserType.STAFF:
        return False
    profile = getattr(user, "staff_profile", None)
    if profile and profile.is_super_admin:
        return True
    return user.has_perm(codename)


class IsAdminOnly(permissions.BasePermission):
    """Only Admin / superuser accounts may access this view."""

    def has_permission(self, request, view):
        return is_admin(request.user)


class CanManageCustomers(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return is_staff_with_perm(request.user, "user_management.view_user")
        return is_staff_with_perm(request.user, "user_management.change_user")


class CanManageSellers(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return is_staff_with_perm(request.user, "user_management.view_sellerprofile")
        return is_staff_with_perm(request.user, "user_management.change_sellerprofile")


class CanManageStaff(permissions.BasePermission):
    """Staff/role management is admin-only by default — staff shouldn't be
    able to grant themselves or each other more access."""

    def has_permission(self, request, view):
        return is_admin(request.user)
