"""URL configuration for the VikelaMine dashboard and backend."""
from django.urls import path
from dashboard import views as dashboard_views
from core import views as core_views

urlpatterns = [
    path('', dashboard_views.page, {'page_name': 'alerts'}, name='root'),
    path('login/', dashboard_views.page, {'page_name': 'login'}, name='login'),
    path('<str:page_name>.html', dashboard_views.page, name='page'),
    path('account/login/', core_views.login_view, name='account_login'),
    path('dashboard/', core_views.dashboard, name='dashboard'),
    path('reports/', core_views.reports, name='reports'),
    path('add-report/', core_views.add_report, name='add_report'),
    path('report-hazard/', core_views.report_hazard, name='report_hazard'),
    path('how-it-works/', core_views.how_it_works, name='how_it_works'),
    path('summaries/', core_views.summaries, name='summaries'),
    path('maps/', core_views.maps, name='maps'),
    path('contact/', core_views.contact, name='contact'),
    path('settings/', core_views.settings_page, name='settings'),
    path('admin/users/', core_views.admin_users, name='admin_users'),
    path('admin/sites/', core_views.admin_sites, name='admin_sites'),
    path('sos-alert/', core_views.sos_alert, name='sos_alert'),
    path('forgot_password/', core_views.forgot_password, name='forgot_password'),
    path('near-danger/', core_views.nearby_danger, name='near_danger'),
    path('check-nearby-hazards/', core_views.check_nearby_hazards, name='check_nearby_hazards'),
    path('hazard-map-data/', core_views.hazard_map_data, name='hazard_map_data'),
]
