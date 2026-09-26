from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, MiningSite, Hazard, ChecklistItem, HazardResponse


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("VikelaMine", {"fields": ("role", "mining_sites")}),
    )


admin.site.register(MiningSite)
admin.site.register(Hazard)
admin.site.register(ChecklistItem)
admin.site.register(HazardResponse)