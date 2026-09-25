from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Permission
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView, View

from .forms import BanUserForm, RejectSellerForm, SellerForm, StaffForm, StaffRoleForm, CustomerForm
from .models import CustomerProfile, SellerProfile, StaffProfile, StaffRole
from .permissions import is_admin, is_staff_with_perm

User = get_user_model()


def staff_required(codename):
    """View decorator: admins always pass; staff pass if their role grants
    `codename` (dotted, e.g. 'user_management.change_user')."""

    def check(user):
        return is_staff_with_perm(user, codename)

    return user_passes_test(check, login_url="login")


# ---------------------------------------------------------------- customers

@login_required
@staff_required("user_management.view_user")
def customer_list(request):
    qs = User.objects.filter(user_type=User.UserType.CUSTOMER).select_related("customer_profile")
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )
    if status == "banned":
        qs = qs.filter(is_banned=True)
    elif status == "active":
        qs = qs.filter(is_active=True, is_banned=False)
    page_obj = Paginator(qs.order_by("-created_at"), 25).get_page(request.GET.get("page"))
    return render(request, "user_management/customer_list.html", {
        "page_obj": page_obj, "q": q, "status": status,
    })


@login_required
@staff_required("user_management.view_user")
def customer_detail(request, pk):
    customer = get_object_or_404(User, pk=pk, user_type=User.UserType.CUSTOMER)
    CustomerProfile.objects.get_or_create(user=customer)
    return render(request, "user_management/customer_detail.html", {"customer": customer})


@login_required
@staff_required("user_management.change_user")
def customer_edit(request, pk):
    customer = get_object_or_404(User, pk=pk, user_type=User.UserType.CUSTOMER)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated.")
            return redirect("user_management:customer_detail", pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, "user_management/customer_form.html", {"form": form, "customer": customer})


@login_required
@staff_required("user_management.change_user")
def customer_ban_toggle(request, pk):
    customer = get_object_or_404(User, pk=pk, user_type=User.UserType.CUSTOMER)
    if customer.is_banned:
        customer.unban()
        messages.success(request, f"{customer} has been unbanned.")
    else:
        if request.method == "POST":
            form = BanUserForm(request.POST)
            if form.is_valid():
                customer.ban(reason=form.cleaned_data["reason"], by=request.user)
                messages.success(request, f"{customer} has been banned.")
                return redirect("user_management:customer_detail", pk=customer.pk)
        else:
            form = BanUserForm()
        return render(request, "user_management/ban_confirm.html", {"target": customer, "form": form})
    return redirect("user_management:customer_detail", pk=customer.pk)


@login_required
@staff_required("user_management.delete_user")
def customer_delete(request, pk):
    customer = get_object_or_404(User, pk=pk, user_type=User.UserType.CUSTOMER)
    if request.method == "POST":
        customer.delete()
        messages.success(request, "Customer deleted.")
        return redirect("user_management:customer_list")
    return render(request, "user_management/delete_confirm.html", {"target": customer})


# ------------------------------------------------------------------ sellers

@login_required
@staff_required("user_management.view_sellerprofile")
def seller_list(request):
    qs = User.objects.filter(user_type=User.UserType.SELLER).select_related("seller_profile")
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(seller_profile__approval_status=status.upper())
    page_obj = Paginator(qs.order_by("-created_at"), 25).get_page(request.GET.get("page"))
    return render(request, "user_management/seller_list.html", {"page_obj": page_obj, "status": status})


@login_required
@staff_required("user_management.view_sellerprofile")
def seller_detail(request, pk):
    seller = get_object_or_404(User, pk=pk, user_type=User.UserType.SELLER)
    return render(request, "user_management/seller_detail.html", {
        "seller": seller, "reject_form": RejectSellerForm(),
    })


@login_required
@staff_required("user_management.add_sellerprofile")
def seller_create(request):
    if request.method == "POST":
        form = SellerForm(request.POST)
        if form.is_valid():
            seller = form.save()
            messages.success(request, "Seller created.")
            return redirect("user_management:seller_detail", pk=seller.pk)
    else:
        form = SellerForm()
    return render(request, "user_management/seller_form.html", {"form": form})


@login_required
@staff_required("user_management.change_sellerprofile")
def seller_edit(request, pk):
    seller = get_object_or_404(User, pk=pk, user_type=User.UserType.SELLER)
    if request.method == "POST":
        form = SellerForm(request.POST, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, "Seller updated.")
            return redirect("user_management:seller_detail", pk=seller.pk)
    else:
        form = SellerForm(instance=seller)
    return render(request, "user_management/seller_form.html", {"form": form, "seller": seller})


@login_required
@staff_required("user_management.change_sellerprofile")
def seller_approve(request, pk):
    seller = get_object_or_404(User, pk=pk, user_type=User.UserType.SELLER)
    seller.seller_profile.approve(by=request.user)
    messages.success(request, f"{seller.seller_profile.shop_name} approved.")
    return redirect("user_management:seller_detail", pk=seller.pk)


@login_required
@staff_required("user_management.change_sellerprofile")
def seller_reject(request, pk):
    seller = get_object_or_404(User, pk=pk, user_type=User.UserType.SELLER)
    if request.method == "POST":
        form = RejectSellerForm(request.POST)
        if form.is_valid():
            seller.seller_profile.reject(reason=form.cleaned_data["reason"], by=request.user)
            messages.success(request, f"{seller.seller_profile.shop_name} rejected.")
    return redirect("user_management:seller_detail", pk=seller.pk)


@login_required
@staff_required("user_management.delete_sellerprofile")
def seller_delete(request, pk):
    seller = get_object_or_404(User, pk=pk, user_type=User.UserType.SELLER)
    if request.method == "POST":
        seller.delete()
        messages.success(request, "Seller deleted.")
        return redirect("user_management:seller_list")
    return render(request, "user_management/delete_confirm.html", {"target": seller})


# --------------------------------------------------- staff & role permissions
# Admin-only: staff shouldn't be able to grant themselves/each other access.

admin_required = user_passes_test(is_admin, login_url="login")


@login_required
@admin_required
def staff_list(request):
    qs = User.objects.filter(user_type=User.UserType.STAFF).select_related("staff_profile__role")
    page_obj = Paginator(qs.order_by("-created_at"), 25).get_page(request.GET.get("page"))
    return render(request, "user_management/staff_list.html", {"page_obj": page_obj})


@login_required
@admin_required
def staff_create(request):
    if request.method == "POST":
        form = StaffForm(request.POST)
        if form.is_valid():
            staff = form.save()
            messages.success(request, "Staff account created.")
            return redirect("user_management:staff_list")
    else:
        form = StaffForm()
    return render(request, "user_management/staff_form.html", {"form": form})


@login_required
@admin_required
def staff_edit(request, pk):
    staff = get_object_or_404(User, pk=pk, user_type=User.UserType.STAFF)
    if request.method == "POST":
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff account updated.")
            return redirect("user_management:staff_list")
    else:
        form = StaffForm(instance=staff)
    return render(request, "user_management/staff_form.html", {"form": form, "staff": staff})


@login_required
@admin_required
def staff_delete(request, pk):
    staff = get_object_or_404(User, pk=pk, user_type=User.UserType.STAFF)
    if request.method == "POST":
        staff.delete()
        messages.success(request, "Staff account deleted.")
        return redirect("user_management:staff_list")
    return render(request, "user_management/delete_confirm.html", {"target": staff})


@login_required
@admin_required
def role_list(request):
    roles = StaffRole.objects.all().select_related("group")
    return render(request, "user_management/role_list.html", {"roles": roles, "form": StaffRoleForm()})


@login_required
@admin_required
def role_create(request):
    if request.method == "POST":
        form = StaffRoleForm(request.POST)
        if form.is_valid():
            from django.contrib.auth.models import Group
            group = Group.objects.create(name=form.cleaned_data["name"])
            role = form.save(commit=False)
            role.group = group
            role.save()
            messages.success(request, "Role created.")
    return redirect("user_management:role_list")


@login_required
@admin_required
def role_permissions(request, pk):
    role = get_object_or_404(StaffRole, pk=pk)
    all_perms = Permission.objects.filter(
        content_type__app_label="user_management"
    ).select_related("content_type")
    if request.method == "POST":
        selected_ids = request.POST.getlist("permissions")
        role.group.permissions.set(selected_ids)
        messages.success(request, f"Permissions updated for {role.name}.")
        return redirect("user_management:role_list")
    current_ids = set(role.group.permissions.values_list("id", flat=True))
    return render(request, "user_management/role_permissions.html", {
        "role": role, "all_perms": all_perms, "current_ids": current_ids,
    })
