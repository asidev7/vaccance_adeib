from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'telephone', 'est_actif', 'is_staff')
    list_filter = ('role', 'est_actif', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telephone')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'telephone', 'photo', 'est_actif'),
        }),
    )
