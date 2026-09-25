from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CustomerProfile, SellerProfile, StaffProfile, StaffRole, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "user_type", "is_active", "is_banned", "created_at"]
    list_filter = ["user_type", "is_active", "is_banned"]
    search_fields = ["username", "email", "first_name", "last_name"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Account type & status", {
            "fields": ("user_type", "phone", "is_banned", "ban_reason", "banned_at", "banned_by")
        }),
    )


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "total_orders", "total_spent"]
    search_fields = ["user__username", "user__email"]


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ["shop_name", "user", "approval_status", "commission_rate"]
    list_filter = ["approval_status"]
    search_fields = ["shop_name", "user__username", "user__email"]


@admin.register(StaffRole)
class StaffRoleAdmin(admin.ModelAdmin):
    list_display = ["name", "group"]


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "job_title", "department", "is_super_admin"]
    list_filter = ["role", "is_super_admin"]
