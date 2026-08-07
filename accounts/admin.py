from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CognizeUserAdmin(UserAdmin):
    list_display = ("username", "get_full_name", "cargo", "departamento", "is_active")
    list_filter = ("cargo", "departamento", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Cognize", {"fields": ("cargo", "departamento", "telefone")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Cognize", {"fields": ("cargo", "departamento", "telefone")}),
    )
