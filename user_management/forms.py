from django import forms
from django.contrib.auth import get_user_model

from .models import CustomerProfile, SellerProfile, StaffProfile, StaffRole

User = get_user_model()

INPUT_CLS = (
    "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-blue-500"
)


class CustomerForm(forms.ModelForm):
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)
    date_of_birth = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLS
        if instance and hasattr(instance, "customer_profile"):
            self.fields["address"].initial = instance.customer_profile.address
            self.fields["date_of_birth"].initial = instance.customer_profile.date_of_birth

    def save(self, commit=True):
        user = super().save(commit=commit)
        profile, _ = CustomerProfile.objects.get_or_create(user=user)
        profile.address = self.cleaned_data.get("address", "")
        profile.date_of_birth = self.cleaned_data.get("date_of_birth")
        profile.save()
        return user


class BanUserForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "class": INPUT_CLS, "placeholder": "Reason for ban (optional)"}),
        required=False,
    )


class SellerForm(forms.ModelForm):
    shop_name = forms.CharField(max_length=150)
    business_email = forms.EmailField(required=False)
    business_phone = forms.CharField(max_length=20, required=False)
    business_address = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)
    commission_rate = forms.DecimalField(max_digits=5, decimal_places=2, required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLS
        if instance and hasattr(instance, "seller_profile"):
            p = instance.seller_profile
            self.fields["shop_name"].initial = p.shop_name
            self.fields["business_email"].initial = p.business_email
            self.fields["business_phone"].initial = p.business_phone
            self.fields["business_address"].initial = p.business_address
            self.fields["commission_rate"].initial = p.commission_rate

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.user_type = User.UserType.SELLER
        user.save(update_fields=["user_type"])
        profile, _ = SellerProfile.objects.get_or_create(user=user)
        for f in ["shop_name", "business_email", "business_phone", "business_address"]:
            setattr(profile, f, self.cleaned_data.get(f) or "")
        profile.commission_rate = self.cleaned_data.get("commission_rate") or profile.commission_rate
        profile.save()
        return user


class RejectSellerForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "class": INPUT_CLS}), required=False)


class StaffForm(forms.ModelForm):
    job_title = forms.CharField(max_length=100, required=False)
    department = forms.CharField(max_length=100, required=False)
    role = forms.ModelChoiceField(queryset=StaffRole.objects.all(), required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Leave blank to auto-generate")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone"]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLS
        if instance and hasattr(instance, "staff_profile"):
            p = instance.staff_profile
            self.fields["job_title"].initial = p.job_title
            self.fields["department"].initial = p.department
            self.fields["role"].initial = p.role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = User.UserType.STAFF
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        elif not user.pk:
            user.set_password(User.objects.make_random_password())
        user.save()
        profile, _ = StaffProfile.objects.get_or_create(user=user)
        profile.job_title = self.cleaned_data.get("job_title", "")
        profile.department = self.cleaned_data.get("department", "")
        role = self.cleaned_data.get("role")
        profile.role = role
        profile.save()
        if role:
            user.groups.set([role.group])
        return user


class StaffRoleForm(forms.ModelForm):
    class Meta:
        model = StaffRole
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLS}),
            "description": forms.Textarea(attrs={"rows": 2, "class": INPUT_CLS}),
        }
