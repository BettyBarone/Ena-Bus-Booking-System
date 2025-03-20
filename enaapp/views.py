from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.urls import reverse
from enaapp.models import CustomUser  
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from .models import Bus, Booking, Trip, Payment, Route
from django.utils.timezone import now
from datetime import datetime
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

User = get_user_model()

def admin_dashboard_data(request):
    """Fetch statistics for the admin dashboard."""
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        total_buses = Bus.objects.count()
        total_users = User.objects.count()
        total_bookings = Booking.objects.count()
        total_revenue = Payment.objects.filter(status="completed").aggregate(total=Sum("amount"))["total"] or 0

        data = {
            "total_buses": total_buses,
            "total_users": total_users,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
        }
        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
# Fetch all buses
def get_buses(request):
    buses = Bus.objects.select_related("route").all()
    buses_data = [
        {"id": bus.id, "bus_number": bus.bus_number, "route": bus.route.route_name, "capacity": bus.capacity}
        for bus in buses
    ]
    return JsonResponse({"buses": buses_data})

def get_routes(request):
    routes = Route.objects.all().values("id", "route_name")
    return JsonResponse({"routes": list(routes)})


# Add new bus
@csrf_exempt  # Allow requests from frontend (not recommended for production)
def add_bus(request):
    if request.method == "POST":
        data = json.loads(request.body)
        bus_number = data.get("bus_number")
        route_name = data.get("route")
        capacity = data.get("capacity")

        # Get or create route
        route, _ = Route.objects.get_or_create(route_name=route_name, defaults={"departure": "Unknown", "arrival": "Unknown"})

        # Create bus
        bus = Bus.objects.create(bus_number=bus_number, route=route, capacity=capacity)

        return JsonResponse({"message": "Bus added successfully!", "bus": {"id": bus.id, "bus_number": bus.bus_number, "route": bus.route.route_name, "capacity": bus.capacity}}, status=201)

# Delete bus
@csrf_exempt
def delete_bus(request, bus_id):
    if request.method == "DELETE":
        try:
            bus = Bus.objects.get(id=bus_id)
            bus.delete()
            return JsonResponse({"message": "Bus deleted successfully!"}, status=200)
        except Bus.DoesNotExist:
            return JsonResponse({"error": "Bus not found"}, status=404)
        
# Fetch all users
def get_users(request):
    users = CustomUser.objects.values("id", "username", "first_name", "last_name", "email", "is_staff")
    
    user_list = []
    for user in users:
        # If user is admin, use `username`, otherwise use `first_name last_name`
        name = user["username"] if user["is_staff"] else f"{user['first_name']} {user['last_name']}".strip()
        user_list.append({
            "id": user["id"],
            "name": name,  
            "email": user["email"], 
            "role": "Admin" if user["is_staff"] else "User"
        })
    
    return JsonResponse({"users": user_list})


# Add a new user
@csrf_exempt
def add_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        name = data.get("name")
        email = data.get("email")
        role = data.get("role")

        if not name or not email or not role:
            return JsonResponse({"message": "All fields are required!"}, status=400)

        # Create the user
        is_staff = True if role.lower() == "admin" else False
        user = CustomUser.objects.create(username=name, email=email, is_staff=is_staff)
        return JsonResponse({"message": "User added successfully!", "user": {"id": user.id, "name": user.username, "email": user.email, "role": role}})

# Delete a user
@csrf_exempt
def delete_user(request, user_id):
    if request.method == "DELETE":
        user = get_object_or_404(CustomUser, id=user_id)
        user.delete()
        return JsonResponse({"message": "User deleted successfully!"})
    
def get_bookings(request):
    """Fetch all bookings with user details, bus, seat, and status."""
    bookings = Booking.objects.select_related("user", "trip").values(
        "id", "user__first_name", "user__last_name", "user__username", "user__is_staff",
        "trip__bus__bus_number", "seat_number", "status"
    )

    booking_list = [
        {
            "id": booking["id"],
            "user": booking["user__username"] if booking["user__is_staff"] else 
                    f"{booking['user__first_name']} {booking['user__last_name']}".strip(),
            "bus_number": booking["trip__bus__bus_number"],
            "seat_number": booking["seat_number"],
            "status": booking["status"].capitalize(),
        }
        for booking in bookings
    ]

    return JsonResponse({"bookings": booking_list})


@csrf_exempt
def delete_booking(request, booking_id):
    """Delete a booking by ID."""
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.delete()
        return JsonResponse({"message": "Booking deleted successfully!"})
    except Booking.DoesNotExist:
        return JsonResponse({"message": "Booking not found!"}, status=404)


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
        "email": request.user.email,
        "phone": request.user.phone,
    }
    
    return render(request, 'user_dash.html', context)

@csrf_protect
@login_required
def update_profile(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = request.user

            # Check if email has actually changed
            new_email = data.get("email", "").strip()
            if new_email and new_email != user.email:
                if CustomUser.objects.filter(email=new_email).exclude(id=user.id).exists():
                    return JsonResponse({"success": False, "message": "Email already in use by another user!"})
                user.email = new_email  # Update email only if changed

            # Check if phone number has actually changed
            new_phone = data.get("phone", "").strip()
            if new_phone and new_phone != user.phone:
                if CustomUser.objects.filter(phone=new_phone).exclude(id=user.id).exists():
                    return JsonResponse({"success": False, "message": "Phone number already in use by another user!"})
                user.phone = new_phone  # Update phone only if changed

            # Always update names (no uniqueness constraint)
            user.first_name = data.get("first_name", "").strip() or user.first_name
            user.last_name = data.get("last_name", "").strip() or user.last_name

            # Handle password update (only update if changed)
            new_password = data.get("password", "").strip()
            if new_password and new_password != "********":  # Ensure new password is not default masked value
                user.set_password(new_password)
                update_session_auth_hash(request, user)  # Keep user logged in

            user.save()

            return JsonResponse({"success": True, "message": "Profile updated successfully!"})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request!"})


@login_required
def get_profile(request):
    user = request.user
    return JsonResponse({
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "password": "********"  # Always masked
    })

@login_required
def get_available_buses(request):
    try:
        # Fetch only upcoming trips
        trips = Trip.objects.filter(status="Upcoming")

        data = [
            {
                "busNumber": trip.bus.bus_number,
                "route": trip.route.route_name,
                "departure_time": datetime.combine(trip.departure_date, trip.departure_time).strftime("%Y-%m-%d %I:%M %p"),
                "available_seats": trip.available_seats,
            }
            for trip in trips
        ]

        return JsonResponse({"buses": data})
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
# Fetch user bookings
@login_required
def get_user_bookings(request):
    user_bookings = Booking.objects.filter(user=request.user)
    data = [
        {
            "busNumber": booking.trip.bus.bus_number,  # Get bus number from Trip
            "route": f"{booking.trip.route.departure} - {booking.trip.route.arrival}",  # Correct route reference
            "seatNumber": booking.seat_number,
            "status": booking.status,  # e.g., "Confirmed", "Pending"
        }
        for booking in user_bookings
    ]
    return JsonResponse({"bookings": data})

@login_required
def get_bus_capacity(request, bus_number):
    try:
        bus = Bus.objects.get(bus_number=bus_number)  # Fetch the bus by bus_number
        return JsonResponse({"busNumber": bus.bus_number, "capacity": bus.capacity})
    except Bus.DoesNotExist:
        return JsonResponse({"error": "Bus not found"}, status=404)
    
@login_required
def get_booked_seats(request, bus_number):
    """API to return all booked seats for a given bus"""
    try:
        bookings = Booking.objects.filter(trip__bus__bus_number=bus_number).values_list("seat_number", flat=True)
        return JsonResponse({"busNumber": bus_number, "bookedSeats": list(bookings)})
    except Bus.DoesNotExist:
        return JsonResponse({"error": "Bus not found"}, status=404)

@csrf_exempt  # Only use if you handle CSRF via tokens
@login_required
def cancel_booking(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            bus_number = data.get("busNumber")
            seat_number = data.get("seatNumber")

            # Find the booking
            booking = Booking.objects.filter(user=request.user, bus__bus_number=bus_number, seat_number=seat_number).first()
            if booking:
                booking.delete()
                return JsonResponse({"success": True, "message": "Booking canceled successfully."})
            else:
                return JsonResponse({"success": False, "message": "Booking not found!"})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request!"})

@login_required
def reserve_seat(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            bus_number = data.get("busNumber")
            seat_number = data.get("seatNumber")

            # ✅ Get the trip using bus_number
            trip = Trip.objects.filter(bus__bus_number=bus_number, status="Upcoming").first()
            if not trip:
                return JsonResponse({"success": False, "message": "Trip not found for the given bus!"})

            # ✅ Check if seat is available in this trip (not bus)
            if Booking.objects.filter(trip=trip, seat_number=seat_number, status="confirmed").exists():
                return JsonResponse({"success": False, "message": "Seat already booked!"})

            # ✅ Create a pending booking (use trip instead of bus)
            booking = Booking.objects.create(
                user=request.user, 
                trip=trip,  # ✅ Corrected from 'bus' to 'trip'
                seat_number=seat_number, 
                status="pending"
            )

            return JsonResponse({
                "success": True,
                "message": f"Seat {seat_number} reserved temporarily! Please complete payment.",
                "booking_id": booking.id,
                "route": trip.route.route_name,  # Adjust according to your model
                "fare": trip.route.fare  # Adjust based on how you store fares
            })

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request!"})


@login_required
def process_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            booking_id = data.get("booking_id")
            mpesa_number = data.get("mpesa_number")

            # Validate booking
            booking = Booking.objects.filter(id=booking_id, user=request.user, status="Pending").first()
            if not booking:
                return JsonResponse({"success": False, "message": "Invalid or expired booking!"})

            # Process payment (mocked for now)
            payment = Payment.objects.create(
                user=request.user,
                booking=booking,
                amount=booking.bus.fare,
                status="Completed",
                payment_method="M-Pesa",
                mpesa_number=mpesa_number
            )

            # Confirm the booking
            booking.status = "Confirmed"
            booking.save()

            return JsonResponse({"success": True, "message": "Payment successful! Your seat is now confirmed."})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request!"})



def user_logout(request):
    logout(request)
    return redirect(reverse("user_login"))
