from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, MiningSite, Hazard, HazardResponse,
    Checklist, HazardStatusLog, Notification, AlertLog,   
)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, MiningSite, Hazard, HazardResponse,
    Checklist, HazardStatusLog, Notification,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "phone_number", "preferred_language")}),
        ("Role", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
    )

@admin.register(AlertLog)
class AlertLogAdmin(admin.ModelAdmin):
    list_display = ("user", "hazard", "distance_m", "alert_method", "created_at")
    list_filter = ("alert_method", "created_at")
    search_fields = ("user__email",)


admin.site.register(MiningSite)
admin.site.register(Hazard)
admin.site.register(HazardResponse)
admin.site.register(Checklist)
admin.site.register(HazardStatusLog)
admin.site.register(Notification)