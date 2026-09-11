# core/urls_geotech.py
from django.urls import path
from . import views_geotech

urlpatterns = [
    path('map/', views_geotech.map_view, name='map_view'),
    path('api/hazards/nearby/', views_geotech.check_nearby_hazards, name='check_nearby_hazards'),
    path('api/hazards/map-data/', views_geotech.hazard_map_data, name='hazard_map_data'),
]