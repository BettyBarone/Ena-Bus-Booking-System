from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.urls import reverse
from enaapp.models import CustomUser  
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Booking, Payment
from django.db.models import Sum


# Create your views here.
def index(request): 
    
    return render(request, 'index.html')

def booking(request): 
    
    return render(request, 'booking.html')

User = get_user_model()  # Get the CustomUser model


def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Authenticate user (email-based)
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect(reverse("user_dash"))  # Redirect to user dashboard
        else:
            return render(request, "login.html", {"error": "Invalid email or password"})  # Pass user error

    return render(request, "login.html")


def admin_login(request):
    if request.method == "POST":
        email = request.POST.get("admin-email")
        password = request.POST.get("admin-password")

        try:
            user = User.objects.get(email=email)  # Find user by email
        except User.DoesNotExist:
            return render(request, "login.html", {"admin_error": "No admin found with this email."})  # Pass error

        # Authenticate using email and password
        user = authenticate(request, email=email, password=password)

        # Ensure user is an admin (both is_staff and is_superuser)
        if user is not None and user.is_staff and user.is_superuser:
            login(request, user)
            response = redirect("admin_dash")  # Redirect to admin dashboard

            # **Clear localStorage on login**
            response.set_cookie("clear_local_storage", "true")

            return response
        else:
            return render(request, "login.html", {"admin_error": "Invalid credentials or not an admin!"})  # Pass error

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

def admin_dash(request):
    if not request.user.is_authenticated or not request.user.is_staff:  # Ensure user is authenticated and staff
        return redirect(reverse("admin_login"))

    return render(request, 'admin_dash.html')

def admin_logout(request):
    logout(request)
    return redirect(reverse("admin_login"))

def user_dash(request):
    if not request.user.is_authenticated:  # Ensure user is logged in
        return redirect(reverse("user_login"))

    # Pass user details to the template
    context = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
    }
    
    return render(request, 'user_dash.html', context)

# @login_required
# def dashboard_data(request):
#     user = request.user

#     # Fetch relevant data
#     total_bookings = Booking.objects.filter(user=user).count()
#     upcoming_trips = Booking.objects.filter(user=user, status='Upcoming').count()
#     total_payments = Payment.objects.filter(user=user).aggregate(total_amount=Sum('amount'))['total_amount'] or 0


#     recent_bookings = list(Booking.objects.filter(user=user)
#     .select_related('trip', 'trip__bus')
#     .order_by('-booking_date')[:5]
#     .values('trip__bus__bus_number', 'trip__route', 'trip__departure_time', 'seat_number', 'status', 'booking_date'))


#     recent_payments = list(Payment.objects.filter(user=user).order_by('-transaction_date')[:5].values(
#     'amount', 'mpesa_transaction_id', 'status', 'transaction_date'
# ))


#     return JsonResponse({
#         'totalBookings': total_bookings,
#         'upcomingTrips': upcoming_trips,
#         'totalPayments': total_payments,
#         'recentBookings': recent_bookings,
#         'recentPayments': recent_payments,
#     })

def user_logout(request):
    logout(request)
    return redirect(reverse("user_login"))
