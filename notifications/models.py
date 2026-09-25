from django.db import models


class Notification(models.Model):
    """
    Simple shared notification feed for admin/staff — not per-user targeted
    (any staff/admin sees the same feed and can mark items read). That's a
    deliberate simplification; if you need per-user read state later, add a
    NotificationRead(user, notification) join table instead of changing this.
    """

    class Kind(models.TextChoices):
        SELLER_PENDING = "SELLER_PENDING", "Seller pending approval"
        NEW_ORDER = "NEW_ORDER", "New order"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
