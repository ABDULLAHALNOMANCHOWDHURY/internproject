from django.urls import path

from . import views

app_name = "user_management"

urlpatterns = [
    # Customers
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/<uuid:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<uuid:pk>/edit/", views.customer_edit, name="customer_edit"),
    path("customers/<uuid:pk>/ban/", views.customer_ban_toggle, name="customer_ban_toggle"),
    path("customers/<uuid:pk>/delete/", views.customer_delete, name="customer_delete"),

    # Sellers
    path("sellers/", views.seller_list, name="seller_list"),
    path("sellers/new/", views.seller_create, name="seller_create"),
    path("sellers/<uuid:pk>/", views.seller_detail, name="seller_detail"),
    path("sellers/<uuid:pk>/edit/", views.seller_edit, name="seller_edit"),
    path("sellers/<uuid:pk>/approve/", views.seller_approve, name="seller_approve"),
    path("sellers/<uuid:pk>/reject/", views.seller_reject, name="seller_reject"),
    path("sellers/<uuid:pk>/delete/", views.seller_delete, name="seller_delete"),

    # Staff & roles
    path("staff/", views.staff_list, name="staff_list"),
    path("staff/new/", views.staff_create, name="staff_create"),
    path("staff/<uuid:pk>/edit/", views.staff_edit, name="staff_edit"),
    path("staff/<uuid:pk>/delete/", views.staff_delete, name="staff_delete"),
    path("roles/", views.role_list, name="role_list"),
    path("roles/new/", views.role_create, name="role_create"),
    path("roles/<int:pk>/permissions/", views.role_permissions, name="role_permissions"),
]
