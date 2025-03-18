from django.urls import path
from enaapp.consumers import DashboardConsumer

websocket_urlpatterns = [
    path("ws/dashboard/", DashboardConsumer.as_asgi()),  # WebSocket route
]
