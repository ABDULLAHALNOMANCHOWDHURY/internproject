from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SellerProfile, StaffRole
from .permissions import CanManageCustomers, CanManageSellers, CanManageStaff
from .serializers import (
    BanUserSerializer,
    CustomerSerializer,
    RejectSellerSerializer,
    SellerSerializer,
    StaffRoleSerializer,
    StaffSerializer,
)

User = get_user_model()


class BaseUserViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "first_name", "last_name", "email", "phone"]
    ordering_fields = ["created_at", "username", "email"]
    lookup_field = "id"


class CustomerViewSet(BaseUserViewSet):
    """
    /api/customers/                 GET list, POST create
    /api/customers/{id}/            GET, PATCH, DELETE
    /api/customers/{id}/ban/        POST {"reason": "..."}
    /api/customers/{id}/unban/      POST
    """

    serializer_class = CustomerSerializer
    permission_classes = [CanManageCustomers]
    filterset_fields = ["is_active", "is_banned"]

    def get_queryset(self):
        return User.objects.filter(user_type=User.UserType.CUSTOMER).select_related(
            "customer_profile"
        )

    @action(detail=True, methods=["post"])
    def ban(self, request, id=None):
        user = self.get_object()
        serializer = BanUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.ban(reason=serializer.validated_data.get("reason", ""), by=request.user)
        return Response(CustomerSerializer(user).data)

    @action(detail=True, methods=["post"])
    def unban(self, request, id=None):
        user = self.get_object()
        user.unban()
        return Response(CustomerSerializer(user).data)


class SellerViewSet(BaseUserViewSet):
    """
    /api/sellers/                   GET list, POST create
    /api/sellers/{id}/               GET, PATCH, DELETE
    /api/sellers/{id}/approve/       POST
    /api/sellers/{id}/reject/        POST {"reason": "..."}
    """

    serializer_class = SellerSerializer
    permission_classes = [CanManageSellers]
    filterset_fields = ["is_active", "is_banned"]

    def get_queryset(self):
        return User.objects.filter(user_type=User.UserType.SELLER).select_related(
            "seller_profile"
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, id=None):
        user = self.get_object()
        profile = user.seller_profile
        profile.approve(by=request.user)
        return Response(SellerSerializer(user).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, id=None):
        user = self.get_object()
        serializer = RejectSellerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.seller_profile.reject(
            reason=serializer.validated_data.get("reason", ""), by=request.user
        )
        return Response(SellerSerializer(user).data)


class StaffViewSet(BaseUserViewSet):
    """
    /api/staff/                     GET list, POST create
    /api/staff/{id}/                 GET, PATCH, DELETE
    /api/staff/{id}/assign_role/     POST {"role_id": 3}
    """

    serializer_class = StaffSerializer
    permission_classes = [CanManageStaff]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        return User.objects.filter(user_type=User.UserType.STAFF).select_related(
            "staff_profile__role"
        )

    @action(detail=True, methods=["post"])
    def assign_role(self, request, id=None):
        user = self.get_object()
        role_id = request.data.get("role_id")
        role = StaffRole.objects.filter(id=role_id).first()
        if role is None:
            return Response({"detail": "role_id not found."}, status=status.HTTP_400_BAD_REQUEST)
        profile = user.staff_profile
        profile.role = role
        profile.save(update_fields=["role"])
        # Keep Django's own group membership (and therefore permission
        # checks) in sync with the assigned role.
        user.groups.set([role.group])
        return Response(StaffSerializer(user).data)


class StaffRoleViewSet(viewsets.ModelViewSet):
    """
    /api/roles/                     GET list, POST create {"name", "description", "permission_codenames": [...]}
    /api/roles/{id}/                GET, PATCH, DELETE
    """

    queryset = StaffRole.objects.all().select_related("group").order_by("name")
    serializer_class = StaffRoleSerializer
    permission_classes = [CanManageStaff]

    def perform_create(self, serializer):
        group = Group.objects.create(name=serializer.validated_data["name"])
        serializer.save(group=group)
