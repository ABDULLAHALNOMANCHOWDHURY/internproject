from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from orders.models import Order
from user_management.models import SellerProfile

from .models import Notification


@receiver(post_save, sender=SellerProfile)
def notify_seller_pending(sender, instance, created, **kwargs):
    if created and instance.approval_status == SellerProfile.ApprovalStatus.PENDING:
        Notification.objects.create(
            kind=Notification.Kind.SELLER_PENDING,
            message=f"New seller “{instance.shop_name}” is awaiting approval",
            url=reverse("user_management:seller_detail", args=[instance.user_id]),
        )


@receiver(post_save, sender=Order)
def notify_new_order(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            kind=Notification.Kind.NEW_ORDER,
            message=f"New order #{instance.pk} placed by {instance.customer}",
            url=reverse("admin:orders_order_change", args=[instance.pk]),
        )
