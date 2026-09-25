from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    WORKER, SUPERVISOR, ADMIN = 'worker', 'supervisor', 'admin'
    ROLE = [(WORKER,'Worker'),(SUPERVISOR,'Supervisor'),(ADMIN,'Administrator')]
    role = models.CharField(max_length=20, choices=ROLE, default=WORKER)
    phone = models.CharField(max_length=20, blank=True)
    preferred_language = models.CharField(max_length=30, default='English')
    assigned_site = models.ForeignKey('MiningSite', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')
    
    def is_worker(self): return self.role == self.WORKER
    def is_supervisor(self): return self.role == self.SUPERVISOR
    def is_admin(self): return self.role == self.ADMIN or self.is_superuser
    def is_miner(self): return self.is_worker()

class MiningSite(models.Model):
    name = models.CharField(max_length=120)
    latitude = models.FloatField()
    longitude = models.FloatField()
    status = models.CharField(max_length=20, choices=[('active','Active'),('inactive','Inactive')], default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

HAZARD_TYPES = [('open_hole','Open Hole'),('crack','Crack / Structural'),('gas','Gas / Fumes'),('equipment','Equipment Fault'),('fall','Fall Risk'),('flooding','Flooding / Water'),('unstable_ground','Unstable Ground'),('electrical','Electrical'),('other','Other')]

class Hazard(models.Model):
    hazard_type = models.CharField(max_length=30, choices=HAZARD_TYPES)
    description = models.TextField()
    photo = models.ImageField(upload_to='hazards/', blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    mining_site = models.ForeignKey(MiningSite, on_delete=models.SET_NULL, null=True, blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_hazards')
    reported_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=[('reported','Reported'),('investigating','Investigating'),('in_progress','In Progress'),('resolved','Resolved')], default='reported')
    priority = models.CharField(max_length=10, choices=[('low','Low'),('medium','Medium'),('high','High')], default='medium')
    resolved_at = models.DateTimeField(null=True, blank=True)
    class Meta: ordering = ['-reported_at']

class ChecklistItem(models.Model):
    hazard = models.ForeignKey(Hazard, on_delete=models.CASCADE, related_name='checklist')
    task = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

class HazardResponse(models.Model):
    hazard = models.ForeignKey(Hazard, on_delete=models.CASCADE, related_name='responses')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    evidence_photo = models.ImageField(upload_to='evidence/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PanicAlert(models.Model):
    worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='panic_alerts')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)