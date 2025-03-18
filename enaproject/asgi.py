import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from enaapp.routing import websocket_urlpatterns  # Ensure this exists in enaapp

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "enaproject.settings")

# Initialize Django before importing models (needed for async compatibility)
django.setup()

# Define the ASGI application with WebSocket support
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # HTTP requests (Django views)
    "websocket": AuthMiddlewareStack(  # WebSocket requests (secured with auth middleware)
        URLRouter(websocket_urlpatterns)
    ),
})
