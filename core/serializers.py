from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    User, MiningSite, Hazard, HazardResponse,
    Checklist, HazardStatusLog, Notification, 
)
from .models import AlertLog 

User = get_user_model()




class AlertLogSerializer(serializers.ModelSerializer):
    hazard_type = serializers.CharField(
        source="hazard.get_hazard_type_display", read_only=True
    )

    class Meta:
        model = AlertLog
        fields = [
            "id", "user", "hazard", "hazard_type", "distance_m",
            "alert_method", "user_latitude", "user_longitude", "created_at",
        ]
        read_only_fields = ["created_at"]


# ---------- User / Auth ----------

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "role",
            "phone_number", "preferred_language",
            "alert_method", "alert_radius_m", "alerts_enabled",
            "is_active", "password", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "phone_number"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)


# ---------- Mining Site ----------

class MiningSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiningSite
        fields = "__all__"


# ---------- Checklist ----------

class ChecklistSerializer(serializers.ModelSerializer):
    completed_by_name = serializers.CharField(
        source="completed_by.get_full_name", read_only=True
    )

    class Meta:
        model = Checklist
        fields = [
            "id", "hazard", "task", "is_completed",
            "completed_by", "completed_by_name",
            "completed_at", "order",
        ]
        read_only_fields = ["completed_by", "completed_at"]


# ---------- Hazard Response ----------

class HazardResponseSerializer(serializers.ModelSerializer):
    supervisor_name = serializers.CharField(
        source="supervisor.get_full_name", read_only=True
    )

    class Meta:
        model = HazardResponse
        fields = [
            "id", "hazard", "supervisor", "supervisor_name",
            "comment", "evidence_photo", "actions_taken",
            "created_at", "updated_at",
        ]
        read_only_fields = ["supervisor", "created_at", "updated_at"]



class HazardListSerializer(serializers.ModelSerializer):
    hazard_type_display = serializers.CharField(
        source="get_hazard_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    reported_by_name = serializers.CharField(
        source="reported_by.get_full_name", read_only=True
    )
    mining_site_name = serializers.CharField(
        source="mining_site.name", read_only=True
    )
    distance_m = serializers.SerializerMethodField()

    class Meta:
        model = Hazard
        fields = [
            "id", "hazard_type", "hazard_type_display",
            "description", "photo", "latitude", "longitude",
            "mining_site", "mining_site_name",
            "reported_by", "reported_by_name",
            "reported_date", "reported_time",
            "status", "status_display", "risk_level",
            "distance_m",
        ]

    def get_distance_m(self, obj):
        return getattr(obj, "distance_m", None)

class HazardDetailSerializer(serializers.ModelSerializer):
    hazard_type_display = serializers.CharField(
        source="get_hazard_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    reported_by_name = serializers.CharField(
        source="reported_by.get_full_name", read_only=True
    )
    mining_site_name = serializers.CharField(
        source="mining_site.name", read_only=True
    )
    response = HazardResponseSerializer(read_only=True)
    checklists = ChecklistSerializer(many=True, read_only=True)
    status_logs = serializers.SerializerMethodField()

    class Meta:
        model = Hazard
        fields = "__all__"
        read_only_fields = [
            "reported_by", "reported_date", "reported_time",
            "resolved_at", "resolved_by", "created_at", "updated_at",
        ]

    def get_status_logs(self, obj):
        return [
            {
                "from": log.from_status,
                "to": log.to_status,
                "by": log.changed_by.get_full_name() or log.changed_by.email,
                "at": log.timestamp,
                "note": log.note,
            }
            for log in obj.status_logs.all()[:20]
        ]


class HazardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hazard
        fields = [
            "hazard_type", "description", "photo",
            "latitude", "longitude", "mining_site",
            "ai_suggested_type", "ai_confidence",
            "ai_suggested", "risk_level",
        ]

    def validate(self, attrs):
        site = attrs.get("mining_site")
        if site and site.status != MiningSite.Status.ACTIVE:
            raise serializers.ValidationError(
                {"mining_site": "Cannot report a hazard for an inactive site."}
            )
        return attrs


# ---------- Notifications ----------

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "hazard", "title", "message", "is_read", "created_at"]
        read_only_fields = ["created_at"]


        


class AlertLogSerializer(serializers.ModelSerializer):
    hazard_type = serializers.CharField(
        source="hazard.get_hazard_type_display", read_only=True
    )
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = AlertLog
        fields = [
            "id", "user", "user_email", "hazard", "hazard_type",
            "distance_m", "alert_method",
            "user_latitude", "user_longitude", "created_at",
        ]
        read_only_fields = ["created_at"]