from .models import Notification


def notification_bell(request):
    if not request.user.is_authenticated:
        return {}
    recent = Notification.objects.all()[:6]
    unread_count = Notification.objects.filter(is_read=False).count()
    return {"bell_notifications": recent, "bell_unread_count": unread_count}
