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
    path("update_profile/", views.update_profile, name="update_profile"),
    path("get_profile/", views.get_profile, name="get_profile"),  # New API to get user data
    path("get_available_buses/", views.get_available_buses, name="get_available_buses"),
    path("get_user_bookings/", views.get_user_bookings, name="get_user_bookings"),
    path("reserve_seat/", views.reserve_seat, name="reserve_seat"),
    path("process_payment/", views.process_payment, name="process_payment"),
    path("cancel_booking/", views.cancel_booking, name="cancel_booking"),
    path("user_logout/", views.user_logout, name="user_logout"),
    path("get_bus_capacity/<str:bus_number>/", views.get_bus_capacity, name="get_bus_capacity"),
    path("get_booked_seats/<str:bus_number>/", views.get_booked_seats, name="get_booked_seats"),
    path("dashboard-data/", views.admin_dashboard_data, name="admin-dashboard-data"),
    path("buses/", views.get_buses, name="get-buses"),
    path("buses/add/", views.add_bus, name="add-bus"),
    path("buses/delete/<int:bus_id>/", views.delete_bus, name="delete-bus"),
    path("routes/", views.get_routes, name="get-routes"),
    path("users/", views.get_users, name="get-users"),
    path("users/add/", views.add_user, name="add-user"),
    path("users/delete/<int:user_id>/", views.delete_user, name="delete-user"),
    path("bookings/", views.get_bookings, name="get_bookings"),
    path("bookings/delete/<int:booking_id>/", views.delete_booking, name="delete_booking"),

]