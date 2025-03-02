from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.urls import reverse

# Create your views here.
def index(request): 
    
    return render(request, 'index.html')

def booking(request): 
    
    return render(request, 'booking.html')

def user_login(request): 
    
    return render(request, 'login.html')

def admin_login(request):
    if request.method == "POST":
        email = request.POST.get("admin-email")
        password = request.POST.get("admin-password")

        try:
            user = User.objects.get(email=email)  # Find user by email
        except User.DoesNotExist:
            user = None

        if user is not None:
            user = authenticate(request, username=user.username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                return redirect("admin_dash")  # Redirect admin to dashboard
            else:
                messages.error(request, "Invalid credentials or not an admin!")
        else:
            messages.error(request, "No admin found with this email.")

    return render(request, "login.html")

def register(request): 
    
    return render(request, 'register.html')
def contact(request): 
    
    return render(request, 'contact.html')

@login_required
def admin_dash(request):
    if not request.user.is_staff:  # Only allow staff users
        return redirect(reverse("admin_login"))  # Redirect to the correct login page
    
    return render(request, 'admin_dash.html')

def admin_logout(request):
    logout(request)
    return redirect(reverse("admin_login"))
