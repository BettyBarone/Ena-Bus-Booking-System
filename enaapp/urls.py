from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('booking/', views.booking, name='booking'),
    path('user_login/', views.user_login, name='user_login'),  # Regular users login
    path('admin_login/', views.admin_login, name='admin_login'),  # Admin login
    path('register/', views.register, name='register'),
    path('contact/', views.contact, name='contact'),
    path('admin_dash/', views.admin_dash, name='admin_dash'),
    path("admin_logout/", views.admin_logout, name="admin_logout"),
    path('user_dash/', views.user_dash, name='user_dash'),
    path("user_logout/", views.user_logout, name="user_logout"),
]