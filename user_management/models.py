import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model. Every account in the system — customer, seller,
    staff/admin — is a User row. What kind of account it is lives in
    `user_type`, and the extra fields for that kind of account live in a
    linked profile model (CustomerProfile / SellerProfile / StaffProfile).
    """

    class UserType(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        STAFF = "STAFF", "Staff"
        SELLER = "SELLER", "Seller"
        CUSTOMER = "CUSTOMER", "Customer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(
        max_length=10, choices=UserType.choices, default=UserType.CUSTOMER
    )
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    # Soft-ban support, separate from Django's own is_active so we can
    # distinguish "account disabled by system" from "admin banned this user"
    # and keep a reason/audit trail.
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True)
    banned_at = models.DateTimeField(null=True, blank=True)
    banned_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bans_issued",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.get_full_name() or self.username

    def ban(self, reason="", by=None):
        self.is_banned = True
        self.is_active = False
        self.ban_reason = reason
        self.banned_at = timezone.now()
        self.banned_by = by
        self.save(update_fields=[
            "is_banned", "is_active", "ban_reason", "banned_at", "banned_by"
        ])

    def unban(self):
        self.is_banned = False
        self.is_active = True
        self.ban_reason = ""
        self.banned_at = None
        self.banned_by = None
        self.save(update_fields=[
            "is_banned", "is_active", "ban_reason", "banned_at", "banned_by"
        ])


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile"
    )
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Customer: {self.user}"


class SellerProfile(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_profile"
    )
    shop_name = models.CharField(max_length=150)
    business_email = models.EmailField(blank=True)
    business_phone = models.CharField(max_length=20, blank=True)
    business_address = models.TextField(blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    approval_status = models.CharField(
        max_length=10, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sellers_approved",
    )
    rejection_reason = models.TextField(blank=True)
    document = models.FileField(upload_to="seller_documents/", blank=True, null=True)

    def __str__(self):
        return self.shop_name

    def approve(self, by=None):
        self.approval_status = self.ApprovalStatus.APPROVED
        self.approved_at = timezone.now()
        self.approved_by = by
        self.rejection_reason = ""
        self.save()

    def reject(self, reason="", by=None):
        self.approval_status = self.ApprovalStatus.REJECTED
        self.approved_at = None
        self.approved_by = by
        self.rejection_reason = reason
        self.save()


class StaffRole(models.Model):
    """
    A named role (e.g. 'Order Manager', 'Support Agent') that wraps a
    Django Group. Staff get assigned a role; the role carries a set of
    Django Permissions, so all of Django's built-in permission checks
    (has_perm, decorators, DRF DjangoModelPermissions, etc.) keep working.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="staff_role")

    def __str__(self):
        return self.name


class StaffProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile"
    )
    role = models.ForeignKey(
        StaffRole, on_delete=models.SET_NULL, null=True, blank=True, related_name="staff_members"
    )
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    is_super_admin = models.BooleanField(
        default=False, help_text="Full access, bypasses role permission checks."
    )

    def __str__(self):
        return f"Staff: {self.user}"
