from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.urls import reverse
from enaapp.models import CustomUser  

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
    if request.method == "POST":
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']
        phone = request.POST['phone']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        if CustomUser.objects.filter(username=email).exists():
            messages.error(request, "Email already exists!")
            return redirect("register")

        if CustomUser.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already exists!")
            return redirect("register")

        # Create a normal user with phone number
        user = CustomUser.objects.create_user(
            username=email, first_name=firstname, last_name=lastname,
            email=email, phone=phone, password=password
        )
        user.save()

        # Authenticate and login
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect("user_dash")

        messages.error(request, "Something went wrong, please try logging in.")
        return redirect("user_login")

    return render(request, "register.html")


def contact(request): 
    
    return render(request, 'contact.html')

@login_required(login_url='admin_login')
def admin_dash(request):
    if not request.user.is_staff:  # Only allow staff users
        return redirect(reverse("admin_login"))  # Redirect to the correct login page
    
    return render(request, 'admin_dash.html')

def admin_logout(request):
    logout(request)
    return redirect(reverse("admin_login"))

# @login_required(login_url='user_login')
def user_dash(request):
    
    return render(request, 'user_dash.html')

def user_logout(request):
    logout(request)
    return redirect(reverse("user_login"))
