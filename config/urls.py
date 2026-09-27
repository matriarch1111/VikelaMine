"""URL configuration for the VikelaMine dashboard and backend."""
from django.urls import include, path
from dashboard import views as dashboard_views

urlpatterns = [
    path('', dashboard_views.page, {'page_name': 'alerts'}, name='root'),
    path('login/', dashboard_views.page, {'page_name': 'login'}, name='login'),
    path('<str:page_name>.html', dashboard_views.page, name='page'),
    path('', include('core.urls')),
]
