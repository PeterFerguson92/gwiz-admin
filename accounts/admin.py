# accounts/admin.py

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

User = get_user_model()

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """
    Custom User admin styled by Unfold.
    """

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "full_name",
        "provider",
        "is_social_login",
        "is_active",
        "is_staff",
        "last_login",
    )
    list_display_links = ("username",)
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "provider",
        "is_social_login",
    )

    fieldsets = (
        (
            "Profile",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    ("username", "email"),
                    ("first_name", "last_name"),
                    "full_name",
                    ("avatar_url", "phone_number"),
                ),
            },
        ),
        (
            "Social login",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("is_social_login", "provider"),
            },
        ),
        (
            "Permissions",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    ("is_active", "is_staff", "is_superuser"),
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("last_login", "date_joined"),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide", "gwiz-card", "gwiz-grid"),
                "fields": ("username", "email", "full_name", "password1", "password2"),
            },
        ),
    )

    search_fields = ("username", "email", "full_name")
    ordering = ("id",)
