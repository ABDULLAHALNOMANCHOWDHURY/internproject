# User Management App (Django)

Drop-in Django app covering **Customers**, **Sellers/Vendors**, and **Admin
Staff & Role Permissions** — models, DRF API, and a server-rendered
(Tailwind) admin panel.

## 1. Install into your project

```bash
pip install djangorestframework django-filter
```

Copy the `user_management/` folder into your project root (next to
`manage.py`), then in **settings.py**:

```python
INSTALLED_APPS = [
    ...
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "user_management",
]

AUTH_USER_MODEL = "user_management.User"   # MUST be set before your first migration
```

> ⚠️ `AUTH_USER_MODEL` can only be set **before** you run your first
> `migrate`. If you already have a database with the default `auth.User`,
> see the "Existing project" note at the bottom.

In your project's root **urls.py**:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path("admin-panel/", include("user_management.urls")),        # server-rendered UI
    path("api/", include("user_management.api_urls")),            # DRF API
]
```

Then:

```bash
python manage.py makemigrations user_management
python manage.py migrate
python manage.py createsuperuser   # make it user_type=ADMIN via shell or /admin/
```

## 2. How it's organized

| File | Purpose |
|---|---|
| `models.py` | `User` (custom, `user_type`: ADMIN/STAFF/SELLER/CUSTOMER) + `CustomerProfile`, `SellerProfile`, `StaffProfile`, `StaffRole` |
| `permissions.py` | `is_admin()`, `is_staff_with_perm()` — shared logic used by both the API and the template views |
| `serializers.py` / `api_views.py` / `api_urls.py` | DRF: `/api/customers/`, `/api/sellers/`, `/api/staff/`, `/api/roles/`, each with list/detail/create/update/delete + action endpoints (`ban`, `unban`, `approve`, `reject`, `assign_role`) |
| `forms.py` / `views.py` / `urls.py` | Server-rendered admin panel at `/admin-panel/...` using Django templates + Tailwind CDN |
| `templates/user_management/` | List, detail, form, and confirm templates for each section |
| `admin.py` | Registers everything in Django's built-in `/admin/` too, as a fallback |

## 3. Roles & permissions model

- Every **staff** account gets a `StaffProfile` with an optional `role`
  (`StaffRole`), which wraps a Django `Group`.
- Assigning a role to staff (via `/admin-panel/roles/` or the
  `assign_role` API action) sets `user.groups = [role.group]`, so Django's
  own `user.has_perm(...)` and DRF's permission classes stay correct
  everywhere in your project, not just in this app.
- **Admins** (`user_type=ADMIN` or `is_superuser`) always bypass role
  checks. Only admins can create/edit staff accounts and role
  permissions — staff can't grant themselves more access.
- A `StaffProfile.is_super_admin` flag exists for staff who should behave
  like admins in this module without being full Django superusers.

## 4. Ban / approve workflows

- `User.ban(reason, by)` / `User.unban()` — sets `is_active=False`,
  `is_banned=True`, records reason + who banned them. Used by both the
  customer ban button and `POST /api/customers/{id}/ban/`.
- `SellerProfile.approve(by)` / `.reject(reason, by)` — same pattern for
  seller onboarding approval, used by the seller detail page and
  `POST /api/sellers/{id}/approve|reject/`.

## 5. API quick reference

```
GET/POST      /api/customers/
GET/PATCH/DEL /api/customers/{id}/
POST          /api/customers/{id}/ban/      {"reason": "..."}
POST          /api/customers/{id}/unban/

GET/POST      /api/sellers/
GET/PATCH/DEL /api/sellers/{id}/
POST          /api/sellers/{id}/approve/
POST          /api/sellers/{id}/reject/     {"reason": "..."}

GET/POST      /api/staff/
GET/PATCH/DEL /api/staff/{id}/
POST          /api/staff/{id}/assign_role/  {"role_id": 3}

GET/POST      /api/roles/
GET/PATCH/DEL /api/roles/{id}/
```

All endpoints support `?search=`, `?ordering=`, and filter fields
(`is_active`, `is_banned`, etc.) via `django-filter`.

## 6. Existing project with the default `auth.User`

If you already have data on Django's built-in `User` model, you can't
just swap `AUTH_USER_MODEL` after the fact. Two options:
1. **New project / no user data yet** → use this app's `User` directly
   (recommended, what's wired up above).
2. **Already in production** → instead drop the `user_type` field onto a
   `Profile` model that has a `OneToOneField(settings.AUTH_USER_MODEL)`
   and adjust `permissions.py` / views to read `user.profile.user_type`
   instead of `user.user_type`. I can generate that variant if this is
   your situation — just say so.

## 7. Next steps you'll likely want

- Wire `customer_profile.total_orders` / `total_spent` to your real
  Orders app (currently plain fields, not auto-computed).
- Add email notifications on ban / seller approval / rejection.
- Add a login/permission-denied template (`login_url="login"` in
  `views.py` assumes a `login` URL name exists in your project).
