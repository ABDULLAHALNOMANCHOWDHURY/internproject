from rest_framework.routers import DefaultRouter

from .api_views import CustomerViewSet, SellerViewSet, StaffRoleViewSet, StaffViewSet

router = DefaultRouter()
router.register("customers", CustomerViewSet, basename="api-customers")
router.register("sellers", SellerViewSet, basename="api-sellers")
router.register("staff", StaffViewSet, basename="api-staff")
router.register("roles", StaffRoleViewSet, basename="api-roles")

urlpatterns = router.urls
