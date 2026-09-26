from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("worker", "Worker"),
        ("supervisor", "Supervisor"),
        ("admin", "Administrator"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="worker")
    mining_sites = models.ManyToManyField(
        "MiningSite", blank=True, related_name="supervisors"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class MiningSite(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    def __str__(self):
        return self.name


class Hazard(models.Model):
    STATUS_CHOICES = [
        ("REPORTED", "Reported"),
        ("INVESTIGATING", "Investigating"),
        ("IN_PROGRESS", "In Progress"),
        ("RESOLVED", "Resolved"),
    ]
    HAZARD_TYPES = [
        ("OPEN_HOLE", "Open Hole"),
        ("CRACK", "Crack"),
        ("GAS", "Gas-related"),
        ("UNSTABLE_GROUND", "Unstable Ground"),
        ("OTHER", "Other"),
    ]

    hazard_type = models.CharField(max_length=30, choices=HAZARD_TYPES)
    description = models.TextField()
    photo = models.ImageField(upload_to="hazards/", blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    mining_site = models.ForeignKey(
        MiningSite, on_delete=models.CASCADE, related_name="hazards"
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reported_hazards",
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="REPORTED"
    )

    class Meta:
        ordering = ["-reported_at"]

    def __str__(self):
        return f"Hazard #{self.id} – {self.get_hazard_type_display()}"


class ChecklistItem(models.Model):
    hazard = models.ForeignKey(
        Hazard, on_delete=models.CASCADE, related_name="checklist_items"
    )
    text = models.CharField(max_length=200)
    done = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.hazard_id} – {self.text}"


class HazardResponse(models.Model):
    hazard = models.ForeignKey(
        Hazard, on_delete=models.CASCADE, related_name="responses"
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    comment = models.TextField(blank=True)
    evidence_photo = models.ImageField(
        upload_to="evidence/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Response to #{self.hazard_id} by {self.supervisor}"