from django.shortcuts import redirect
from django.urls import reverse

class CustomLoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        protected_routes = ["/admin_dash/", "/user_dash/"]  # Add all protected pages here

        if request.path in protected_routes and not request.user.is_authenticated:
            # Redirect to the appropriate login page
            if request.path.startswith("/admin"):
                return redirect(reverse("admin_login"))
            else:
                return redirect(reverse("user_login"))

        return self.get_response(request)
