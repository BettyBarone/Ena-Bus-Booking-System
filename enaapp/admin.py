from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Bus, Trip, Booking, Payment, Route

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("username", "first_name", "last_name", "email", "phone", "is_staff", "is_superuser")
    search_fields = ("email", "phone", "username", "first_name", "last_name")
    ordering = ("email",)

    # Extend fieldsets correctly
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("phone",)}),  
    )

    # Extend add_fieldsets correctly
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("first_name", "last_name", "email", "phone", "password1", "password2")}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(Bus)
admin.site.register(Trip)
admin.site.register(Booking)
admin.site.register(Route)
admin.site.register(Payment)


