from django.urls import path
from . import views

urlpatterns = [
    path('account/login/', views.login_view, name='account_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reports/', views.reports, name='reports'),
    path('add-report/', views.add_report, name='add_report'),
    path('report-hazard/', views.report_hazard, name='report_hazard'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('summaries/', views.summaries, name='summaries'),
    path('maps/', views.maps, name='maps'),
    path('contact/', views.contact, name='contact'),
    path('settings/', views.settings_page, name='settings'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/sites/', views.admin_sites, name='admin_sites'),
    path('sos-alert/', views.sos_alert, name='sos_alert'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('near-danger/', views.nearby_danger, name='near_danger'),
    path('check-nearby-hazards/', views.check_nearby_hazards, name='check_nearby_hazards'),
    path('hazard-map-data/', views.hazard_map_data, name='hazard_map_data'),
]
