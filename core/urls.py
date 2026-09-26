from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, MeView, ChangePasswordView,
    UserViewSet, MiningSiteViewSet, HazardViewSet,
    HazardResponseViewSet, ChecklistViewSet, NotificationViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("sites", MiningSiteViewSet, basename="site")
router.register("hazards", HazardViewSet, basename="hazard")
router.register("responses", HazardResponseViewSet, basename="response")
router.register("checklists", ChecklistViewSet, basename="checklist")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("auth/change-password/", ChangePasswordView.as_view()),
    path("", include(router.urls)),
]