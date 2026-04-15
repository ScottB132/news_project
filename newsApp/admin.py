"""
newsApp/admin.py

Django admin configuration for the Speedy Spectator news application.

Registers all models with the Django admin panel and configures the
custom User admin to expose the role field for viewing and editing.

Models registered:
    - User:        Registered with CustomUserAdmin to expose the role field
                   in the user list, filter sidebar, edit page, and create page.
    - Article:     Registered with default admin for basic CRUD management.
    - Newsletter:  Registered with default admin for basic CRUD management.
    - Publisher:   Registered with default admin for basic CRUD management.

Access the admin panel at: /admin/
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Article, Newsletter, Publisher, User


# ---------------------------------------------------------------------------
# Custom User Admin
# ---------------------------------------------------------------------------

class CustomUserAdmin(UserAdmin):
    """
    Custom admin configuration for the User model.

    Extends Django's built-in UserAdmin to expose the custom role field
    in the admin interface. Without this, the role field would not appear
    anywhere in the admin panel since it is not part of Django's default
    User model.

    Customisations:
        - list_display: Adds role to the user list table columns.
        - list_filter:  Adds role to the filter sidebar for quick filtering.
        - fieldsets:    Adds a Role section to the edit user page.
        - add_fieldsets: Adds a Role section to the create user page so
                         the role can be assigned at registration time.
    """

    # Columns displayed in the user list table in the admin panel
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')

    # Filter options shown in the right sidebar of the user list
    list_filter = ('role', 'is_staff', 'is_active')

    # Add a dedicated Role section to the edit user page
    # Extends the default fieldsets tuple with a new section
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )

    # Add a dedicated Role section to the create new user page
    # Extends the default add_fieldsets tuple with a new section
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


# ---------------------------------------------------------------------------
# Model Registration
# ---------------------------------------------------------------------------

# Register User with the custom admin class to expose the role field
admin.site.register(User, CustomUserAdmin)

# Register remaining models with default admin for basic CRUD management
admin.site.register(Article)
admin.site.register(Newsletter)
admin.site.register(Publisher)
