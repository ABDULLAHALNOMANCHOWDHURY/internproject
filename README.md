# Pickymart Admin — User Management

A runnable Django project scaffolding the **User Management** section
(Customers, Sellers/Vendors, Admin Staff & Role Permissions) with:
- Django templates + Tailwind (CDN) admin UI
- Django REST Framework API
- SQLite by default (swap to Postgres/MySQL in `config/settings.py`)

## Run it

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then visit:
- `http://127.0.0.1:8000/` → redirects to the customers list (server-rendered admin UI)
- `http://127.0.0.1:8000/login/` → login page
- `http://127.0.0.1:8000/admin/` → Django's built-in admin (fallback)
- `http://127.0.0.1:8000/api/customers/` → browsable DRF API (once logged in)

## Make your superuser a full Admin

The custom `User` model has a `user_type` field (`ADMIN`/`STAFF`/`SELLER`/`CUSTOMER`).
`createsuperuser` sets `is_superuser=True`, which already bypasses all
permission checks in this app — but if you also want `user_type=ADMIN`
for consistency, open a shell:

```bash
python manage.py shell
```
```python
from user_management.models import User
u = User.objects.get(username="your_superuser")
u.user_type = User.UserType.ADMIN
u.save()
```

## Try the workflow

1. Log in as your superuser.
2. Go to **Roles & Permissions** → create a role (e.g. "Support Agent"),
   then click **Edit permissions** to grant it specific `user_management`
   permissions (view/change users, approve sellers, etc.).
3. Go to **Staff** → **Add Staff**, assign that role.
4. Go to **Sellers** → **Add Seller**, then open it and click **Approve**.
5. Go to **Customers**, open one, and try **Ban** / **Unban**.
6. Hit the same actions via the API, e.g.:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/customers/<id>/ban/ \
        -H "Content-Type: application/json" \
        -d '{"reason": "Fraudulent activity"}' \
        --cookie "sessionid=<your session cookie>"
   ```

## Project layout

```
pickymart_admin/
├── manage.py
├── config/                  # Django project (settings, root urls)
├── user_management/         # the app — see user_management/README.md for full details
│   ├── models.py            # User, CustomerProfile, SellerProfile, StaffProfile, StaffRole
│   ├── permissions.py       # role/permission checks shared by API + template views
│   ├── serializers.py / api_views.py / api_urls.py    # DRF
│   ├── forms.py / views.py / urls.py                  # server-rendered admin panel
│   ├── templates/user_management/                     # Tailwind templates
│   └── admin.py             # Django admin registrations
└── templates/registration/login.html
```

See **`user_management/README.md`** for the full API reference, the
roles/permissions model, and notes on integrating this into an existing
project that already has real customer/order data.
