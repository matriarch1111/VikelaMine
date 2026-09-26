"""URL configuration for the dashboard project."""
from django.urls import path
from dashboard import views

urlpatterns = [
	path('', views.page, {'page_name': 'alerts'}, name='root'),
	path('login/', views.page, {'page_name': 'login'}, name='login'),
    path('<str:page_name>.html', views.page, name='page'),
]
