from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        WORKER = "WORKER", "Worker"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        ADMIN = "ADMIN", "Administrator"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.WORKER)
    phone_number = models.CharField(max_length=20, blank=True)
    preferred_language = models.CharField(max_length=10, default="en")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_worker(self):
        return self.role == self.Role.WORKER

    @property
    def is_supervisor(self):
        return self.role == self.Role.SUPERVISOR

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN


class MiningSite(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    supervisors = models.ManyToManyField(
        User,
        blank=True,
        related_name="supervised_sites",
        limit_choices_to={"role": User.Role.SUPERVISOR},
    )

    def __str__(self):
        return self.name


class Hazard(models.Model):
    class HazardType(models.TextChoices):
        OPEN_HOLE = "OPEN_HOLE", "Open Hole"
        ROCKFALL = "ROCKFALL", "Rockfall"
        GAS = "GAS", "Gas Exposure"
        FLOODING = "FLOODING", "Flooding"
        DUST = "DUST", "Dust"
        INJURY_RISK = "INJURY_RISK", "Injury Risk"
        EQUIPMENT = "EQUIPMENT", "Equipment Failure"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        REPORTED = "REPORTED", "Reported"
        INVESTIGATING = "INVESTIGATING", "Investigating"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"

    class RiskLevel(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    hazard_type = models.CharField(max_length=30, choices=HazardType.choices)
    description = models.TextField()
    photo = models.ImageField(upload_to="hazards/photos/", blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    mining_site = models.ForeignKey(
        MiningSite, on_delete=models.PROTECT, related_name="hazards"
    )
    reported_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="reported_hazards"
    )

    reported_date = models.DateField(auto_now_add=True)
    reported_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.REPORTED
    )

    ai_suggested_type = models.CharField(max_length=30, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    ai_suggested = models.BooleanField(default=False)

    risk_level = models.CharField(
        max_length=10, choices=RiskLevel.choices, blank=True
    )

    assigned_supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_hazards",
        limit_choices_to={"role": User.Role.SUPERVISOR},
    )

    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_hazards",
    )

    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-reported_time"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["mining_site", "status"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return f"Hazard #{self.id} - {self.get_hazard_type_display()} ({self.status})"

    @property
    def is_resolved(self):
        return self.status == self.Status.RESOLVED


class HazardResponse(models.Model):
    hazard = models.OneToOneField(
        Hazard, on_delete=models.CASCADE, related_name="response"
    )
    supervisor = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="hazard_responses"
    )
    comment = models.TextField(blank=True)
    evidence_photo = models.ImageField(
        upload_to="hazards/evidence/", blank=True, null=True
    )
    actions_taken = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Response to Hazard #{self.hazard.id}"


class Checklist(models.Model):
    hazard = models.ForeignKey(
        Hazard, on_delete=models.CASCADE, related_name="checklists"
    )
    task = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.task} (Hazard #{self.hazard.id})"


class HazardStatusLog(models.Model):
    hazard = models.ForeignKey(
        Hazard, on_delete=models.CASCADE, related_name="status_logs"
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Hazard #{self.hazard.id}: {self.from_status} -> {self.to_status}"


class Notification(models.Model):
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    hazard = models.ForeignKey(
        Hazard, on_delete=models.CASCADE, null=True, blank=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"-> {self.recipient.email}: {self.title}"