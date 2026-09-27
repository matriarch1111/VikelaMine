from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sw.js', views.service_worker, name='service_worker'),

    # Authentication and role dashboards
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('supervisor/dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('add-report/', views.add_report, name='add_report'),
    path('report-hazard/', views.report_hazard, name='report_hazard'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),

    # Other pages
    path('summaries/', views.summaries, name='summaries'),
    path('maps/', views.maps, name='maps'),
    path('contact/', views.contact, name='contact'),
    path('settings/', views.settings_page, name='settings'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/sites/', views.admin_sites, name='admin_sites'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('near-danger/', views.nearby_danger, name='near_danger'),
    path('check-nearby-hazards/', views.check_nearby_hazards, name='check_nearby_hazards'),
    path('hazard-map-data/', views.hazard_map_data, name='hazard_map_data'),

    # Emergency and APIs
    path('sos-alert/', views.sos_alert, name='sos_alert'),
    path('ai-assistance/', views.redirect_ai_assistance, name='ai_assistance'),
    path('api/ai-chat/', views.ai_chat, name='ai_chat'),
    path('api/translate-report/', views.translate_report_text, name='translate_report_text'),
    path('api/translate-interface/', views.translate_interface, name='translate_interface'),
    path('api/transcribe-voice/', views.transcribe_voice_note, name='transcribe_voice_note'),
    path('api/text-to-speech/', views.text_to_speech, name='text_to_speech'),
    path('api/sync-report/', views.sync_report, name='sync_report'),
    path('api/translate-page/', views.translate_page_api, name='translate_page_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
