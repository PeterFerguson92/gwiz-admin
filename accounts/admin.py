# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

# Unfold imports
from unfold.admin import ModelAdmin
from unfold.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

User = get_user_model()

# If the default User was already registered somewhere, make sure it's unregistered.
# (This is usually needed when using django.contrib.auth's default User,
# but it's safe to call for a custom one too.)
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """
    Custom User admin using Unfold's ModelAdmin for nice styling.
    """

    # Use Unfold’s forms so the styling matches the theme
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    # Columns in the user list
    list_display = (
        "id",
        "username",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
    )
    
    list_display_links = ("username",)
    
    list_filter = ("is_active", "is_staff", "is_superuser")

    # Fields shown on the detail page (edit user)
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Fields used when creating a new user from admin
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    search_fields = ("username", "email")
    ordering = ("id",)
