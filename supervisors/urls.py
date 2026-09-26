from django.urls import path
from . import views

app_name = "supervisors"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("hazards/", views.hazard_list, name="hazard_list"),
    path("hazards/<int:hazard_id>/", views.hazard_detail, name="hazard_detail"),
    path("hazards/<int:hazard_id>/resolve/", views.resolve_hazard, name="resolve_hazard"),
    path("hazards/<int:hazard_id>/status/<str:new_status>/", views.set_status, name="set_status"),
]
