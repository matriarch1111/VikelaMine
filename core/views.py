from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    User, MiningSite, Hazard, HazardResponse,
    Checklist, HazardStatusLog, Notification,
)
from .serializers import (
    UserSerializer, RegisterSerializer, ChangePasswordSerializer,
    MiningSiteSerializer, HazardListSerializer, HazardDetailSerializer,
    HazardCreateSerializer, HazardResponseSerializer, ChecklistSerializer,
    NotificationSerializer,
)
from .permissions import (
    IsAdminRole, IsSupervisorOrAdmin, CanChangeHazardStatus,
)

User = get_user_model()


# ============================================================
# AUTHENTICATION
# ============================================================

class RegisterView(generics.CreateAPIView):
    """Public registration - always creates a WORKER."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Email + password login, returns JWT and role."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"detail": "Account disabled."},
                status=status.HTTP_403_FORBIDDEN,
            )
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "role": user.role,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        })


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"detail": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Password updated."})


# ============================================================
# USER MANAGEMENT (Admin only)
# ============================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({"detail": "User disabled."})

    @action(detail=True, methods=["post"])
    def enable(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({"detail": "User enabled."})

    @action(detail=True, methods=["post"])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get("new_password")
        if not new_password or len(new_password) < 6:
            return Response(
                {"detail": "Provide a new_password of at least 6 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password reset."})


# ============================================================
# MINING SITES
# ============================================================

class MiningSiteViewSet(viewsets.ModelViewSet):
    queryset = MiningSite.objects.all().order_by("name")
    serializer_class = MiningSiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminRole()]
        return [permissions.IsAuthenticated()]


# ============================================================
# HAZARDS
# ============================================================

class HazardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanChangeHazardStatus]

    def get_queryset(self):
        user = self.request.user
        qs = Hazard.objects.select_related(
            "reported_by", "mining_site", "assigned_supervisor"
        ).prefetch_related("checklists", "status_logs")

        if user.is_admin_role:
            pass
        elif user.is_supervisor:
            site_ids = user.supervised_sites.values_list("id", flat=True)
            qs = qs.filter(mining_site_id__in=site_ids)
        elif user.is_worker:
            qs = qs.filter(reported_by=user)
        else:
            qs = qs.none()

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        site_param = self.request.query_params.get("site")
        if site_param:
            qs = qs.filter(mining_site_id=site_param)
        unresolved = self.request.query_params.get("unresolved")
        if unresolved in ["true", "1"]:
            qs = qs.exclude(status=Hazard.Status.RESOLVED)

        return qs.order_by("-reported_time")

    def get_serializer_class(self):
        if self.action == "list":
            return HazardListSerializer
        if self.action == "create":
            return HazardCreateSerializer
        return HazardDetailSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_worker or user.is_admin_role):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only workers can create hazard reports.")

        hazard = serializer.save(reported_by=user)

        supervisor = hazard.mining_site.supervisors.first()
        if supervisor:
            hazard.assigned_supervisor = supervisor
            hazard.save(update_fields=["assigned_supervisor"])

        HazardStatusLog.objects.create(
            hazard=hazard,
            from_status="",
            to_status=Hazard.Status.REPORTED,
            changed_by=user,
            note="Hazard reported.",
        )

        self._create_default_checklist(hazard)
        self._notify_supervisors(hazard)

    def _create_default_checklist(self, hazard):
        templates = {
            Hazard.HazardType.OPEN_HOLE: [
                "Inspect location", "Restrict access", "Secure area",
                "Repair/cover hole", "Verify repair",
                "Upload evidence", "Mark resolved",
            ],
            Hazard.HazardType.GAS: [
                "Evacuate area", "Ventilate", "Test air quality",
                "Identify source", "Upload evidence", "Mark resolved",
            ],
            Hazard.HazardType.ROCKFALL: [
                "Inspect rock stability", "Barricade area",
                "Scale loose rock", "Upload evidence", "Mark resolved",
            ],
            Hazard.HazardType.DUST: [
                "Identify dust source", "Apply water suppression",
                "Provide PPE", "Upload evidence", "Mark resolved",
            ],
        }
        default = [
            "Inspect hazard", "Take corrective action",
            "Upload evidence", "Mark resolved",
        ]
        tasks = templates.get(hazard.hazard_type, default)
        for i, task in enumerate(tasks):
            Checklist.objects.create(hazard=hazard, task=task, order=i)

    def _notify_supervisors(self, hazard):
        supervisors = hazard.mining_site.supervisors.all()
        for sup in supervisors:
            Notification.objects.create(
                recipient=sup,
                hazard=hazard,
                title=f"New {hazard.get_hazard_type_display()} reported",
                message=(
                    f"Hazard #{hazard.id} at {hazard.mining_site.name} "
                    f"reported by {hazard.reported_by.get_full_name() or hazard.reported_by.email}."
                ),
            )

    @action(detail=True, methods=["patch"])
    def change_status(self, request, pk=None):
        hazard = self.get_object()
        user = request.user

        if not (user.is_supervisor or user.is_admin_role):
            return Response(
                {"detail": "Only supervisors can change hazard status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get("status")
        valid = [c[0] for c in Hazard.Status.choices]
        if new_status not in valid:
            return Response(
                {"detail": f"Invalid status. Choose from {valid}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = {
            Hazard.Status.REPORTED: 0,
            Hazard.Status.INVESTIGATING: 1,
            Hazard.Status.IN_PROGRESS: 2,
            Hazard.Status.RESOLVED: 3,
        }
        if not user.is_admin_role and order[new_status] < order[hazard.status]:
            return Response(
                {"detail": "Cannot move a hazard backwards in the lifecycle."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = hazard.status
        hazard.status = new_status
        if new_status == Hazard.Status.RESOLVED:
            hazard.resolved_at = timezone.now()
            hazard.resolved_by = user
        hazard.save()

        HazardStatusLog.objects.create(
            hazard=hazard,
            from_status=old_status,
            to_status=new_status,
            changed_by=user,
            note=request.data.get("note", ""),
        )

        if new_status == Hazard.Status.RESOLVED:
            Notification.objects.create(
                recipient=hazard.reported_by,
                hazard=hazard,
                title=f"Hazard #{hazard.id} resolved",
                message="Your reported hazard has been marked resolved.",
            )

        return Response(HazardDetailSerializer(hazard).data)

    @action(detail=False, methods=["get"])
    def nearby(self, request):
        """Find unresolved hazards near a lat/lng within a radius (metres)."""
        from math import radians, sin, cos, sqrt, atan2

        try:
            lat = float(request.query_params.get("lat"))
            lng = float(request.query_params.get("lng"))
            radius = float(request.query_params.get("radius", 200))
        except (TypeError, ValueError):
            return Response(
                {"detail": "Provide lat, lng, and optional radius (metres)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = (
                sin(dlat / 2) ** 2
                + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
            )
            return 2 * R * atan2(sqrt(a), sqrt(1 - a))

        qs = Hazard.objects.exclude(status=Hazard.Status.RESOLVED)
        results = []
        for h in qs:
            dist = haversine(lat, lng, float(h.latitude), float(h.longitude))
            if dist <= radius:
                data = HazardListSerializer(h).data
                data["distance_m"] = round(dist, 1)
                results.append(data)

        results.sort(key=lambda x: x["distance_m"])
        return Response(results)


# ============================================================
# HAZARD RESPONSE
# ============================================================

class HazardResponseViewSet(viewsets.ModelViewSet):
    queryset = HazardResponse.objects.all()
    serializer_class = HazardResponseSerializer
    permission_classes = [IsSupervisorOrAdmin]

    def perform_create(self, serializer):
        serializer.save(supervisor=self.request.user)


# ============================================================
# CHECKLIST
# ============================================================

class ChecklistViewSet(viewsets.ModelViewSet):
    serializer_class = ChecklistSerializer
    permission_classes = [IsSupervisorOrAdmin]

    def get_queryset(self):
        qs = Checklist.objects.select_related("hazard", "completed_by")
        hazard_id = self.request.query_params.get("hazard")
        if hazard_id:
            qs = qs.filter(hazard_id=hazard_id)
        return qs

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        item = self.get_object()
        item.is_completed = True
        item.completed_by = request.user
        item.completed_at = timezone.now()
        item.save()
        return Response(ChecklistSerializer(item).data)

    @action(detail=True, methods=["post"])
    def uncomplete(self, request, pk=None):
        item = self.get_object()
        item.is_completed = False
        item.completed_by = None
        item.completed_at = None
        item.save()
        return Response(ChecklistSerializer(item).data)


# ============================================================
# NOTIFICATIONS
# ============================================================

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response({"detail": "Marked as read."})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({"detail": "All marked as read."})
