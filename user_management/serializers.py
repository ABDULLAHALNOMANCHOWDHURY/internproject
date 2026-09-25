from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import CustomerProfile, SellerProfile, StaffProfile, StaffRole

User = get_user_model()


class StaffRoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        source="group.permissions", many=True, read_only=True, slug_field="codename"
    )

    class Meta:
        model = StaffRole
        fields = ["id", "name", "description", "permissions"]


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ["address", "date_of_birth", "total_orders", "total_spent"]


class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = [
            "shop_name", "business_email", "business_phone", "business_address",
            "commission_rate", "approval_status", "approved_at", "rejection_reason",
            "document",
        ]
        read_only_fields = ["approval_status", "approved_at"]


class StaffProfileSerializer(serializers.ModelSerializer):
    role = StaffRoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        source="role", queryset=StaffRole.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = StaffProfile
        fields = ["role", "role_id", "job_title", "department", "is_super_admin"]


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views / tables."""

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email", "phone",
            "user_type", "is_active", "is_banned", "created_at",
        ]


class CustomerSerializer(serializers.ModelSerializer):
    profile = CustomerProfileSerializer(source="customer_profile")

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email", "phone",
            "is_active", "is_banned", "ban_reason", "created_at", "profile",
        ]
        read_only_fields = ["is_banned", "ban_reason"]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("customer_profile", None)
        instance = super().update(instance, validated_data)
        if profile_data:
            CustomerProfile.objects.filter(user=instance).update(**profile_data)
        return instance


class SellerSerializer(serializers.ModelSerializer):
    profile = SellerProfileSerializer(source="seller_profile")

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email", "phone",
            "is_active", "is_banned", "created_at", "profile",
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("seller_profile", None)
        instance = super().update(instance, validated_data)
        if profile_data:
            SellerProfile.objects.filter(user=instance).update(**profile_data)
        return instance


class StaffSerializer(serializers.ModelSerializer):
    profile = StaffProfileSerializer(source="staff_profile")

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email", "phone",
            "is_active", "created_at", "profile",
        ]

    def create(self, validated_data):
        profile_data = validated_data.pop("staff_profile", {})
        password = validated_data.pop("password", None) or User.objects.make_random_password()
        user = User(user_type=User.UserType.STAFF, **validated_data)
        user.set_password(password)
        user.save()
        StaffProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("staff_profile", None)
        instance = super().update(instance, validated_data)
        if profile_data:
            StaffProfile.objects.filter(user=instance).update(**profile_data)
        return instance


class BanUserSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class RejectSellerSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)
