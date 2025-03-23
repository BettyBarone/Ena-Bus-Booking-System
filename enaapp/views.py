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
from django.db.models import Exists, OuterRef, Max
from django.db import IntegrityError
from .mpesa_credentials import MpesaAccessToken, LipanaMpesaPpassword
import requests
from django.http import FileResponse
from reportlab.pdfgen import canvas
import io




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


@login_required
def user_dash(request):
    if not request.user.is_authenticated:
        return redirect("user_login")

    # Determine full name
    full_name = request.user.username if request.user.is_superuser else f"{request.user.first_name} {request.user.last_name}".strip()

    # Get the next available booking ID (as integer, no formatting)
    next_booking_id = Booking.objects.aggregate(next_id=Max("id"))["next_id"]
    next_booking_id = (next_booking_id or 0) + 1  # Increment for next ID

    # Get routes with available upcoming trips
    upcoming_trips = Trip.objects.filter(
        departure_date__gt=now().date()
    ) | Trip.objects.filter(
        departure_date=now().date(), departure_time__gt=now().time()
    )

    available_routes = list(Route.objects.filter(
        Exists(upcoming_trips.filter(route=OuterRef("pk")))
    ).values("route_name", "fare"))  # Convert QuerySet to list

    # Pass user details to the template
    context = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
        "phone": request.user.phone,
        "full_name": full_name,
        "next_booking_id": next_booking_id,  # Return booking ID as is (integer)
        "routes": available_routes  # Ensure it's a JSON-serializable list
    }

    return render(request, "user_dash.html", context)



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
        current_time = now()  # Get current time

        # Fetch all trips that should be updated
        trips = Trip.objects.filter(status__in=["Upcoming", "Ongoing"])

        # Update statuses dynamically
        for trip in trips:
            new_status = trip.update_status()  # Call update_status() without 'save'
            if trip.status != new_status:
                trip.status = new_status
                trip.save()  # Explicitly save if status has changed

        # Get only trips that are still available for booking
        upcoming_trips = Trip.objects.filter(
            departure_date__gt=current_time.date()  # Future trips
        ) | Trip.objects.filter(
            departure_date=current_time.date(), departure_time__gt=current_time.time()  # Trips later today
        )

        # Ensure the queryset is not empty
        if not upcoming_trips.exists():
            return JsonResponse({"buses": []})  # Return an empty list instead of an error

        data = []
        for trip in upcoming_trips:
            try:
                data.append({
                    "busNumber": trip.bus.bus_number,
                    "route": trip.route.route_name,
                    "departure_time": datetime.combine(trip.departure_date, trip.departure_time).strftime("%Y-%m-%d %I:%M %p"),
                    "available_seats": trip.available_seats,
                })
            except Exception as e:
                return JsonResponse({"error": f"Data processing error: {str(e)}"}, status=500)

        return JsonResponse({"buses": data})

    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

    
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

            # Find the booking using the trip's bus
            booking = Booking.objects.filter(
                user=request.user, 
                trip__bus__bus_number=bus_number,  # Correct lookup path
                seat_number=seat_number
            ).first()

            if booking:
                booking.delete()  # Cancel the booking
                
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

            if not bus_number or not seat_number:
                return JsonResponse({"success": False, "message": "Bus number and seat number are required!"})

            # ✅ Get the trip using bus_number
            trip = Trip.objects.filter(bus__bus_number=bus_number, status="Upcoming").first()
            if not trip:
                return JsonResponse({"success": False, "message": "Trip not found for the given bus!"})

            # ✅ Check if seat is already reserved or booked
            existing_booking = Booking.objects.filter(trip=trip, seat_number=seat_number).first()
            if existing_booking:
                if existing_booking.status == "confirmed":
                    return JsonResponse({"success": False, "message": "This seat is already booked!"})
                elif existing_booking.status == "pending":
                    return JsonResponse({"success": False, "message": "This seat is temporarily reserved! Complete payment to confirm it."})


            # ✅ Create a pending booking (use trip instead of bus)
            booking = Booking.objects.create(
                user=request.user, 
                trip=trip,  
                seat_number=seat_number, 
                status="pending"
            )

            # ✅ Get user details
            full_name = request.user.get_full_name() or request.user.username  # Fallback to username
            email = request.user.email
            phone = getattr(request.user, "phone", "")  # Safer way to get phone attribute

            return JsonResponse({
                "success": True,
                "message": f"Seat {seat_number} reserved temporarily! Please complete payment.",
                "booking_id": booking.id,
                "route": trip.route.route_name,  # Ensure correct route retrieval
                "fare": trip.route.fare,  # Ensure correct fare retrieval
                "full_name": full_name,
                "email": email,
                "phone": phone
            })

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data!"})

        except IntegrityError:
            return JsonResponse({"success": False, "message": "This seat is already booked!"})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request!"})
    



@login_required
@csrf_exempt  # Remove this in production!
def process_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            booking_id = data.get("bookingId")
            mpesa_number = data.get("mpesaNumber")
            selected_route = data.get("selectedRoute")

            # Get trip details
            trip = Trip.objects.filter(route__route_name=selected_route, status="Upcoming").first()
            if not trip:
                return JsonResponse({"success": False, "message": "No upcoming trips found for this route."})

            # Fetch available seats
            booked_seats = Booking.objects.filter(trip=trip, status="confirmed").values_list("seat_number", flat=True)
            total_seats = trip.bus.capacity
            available_seats = [seat for seat in range(1, total_seats + 1) if seat not in booked_seats]

            return JsonResponse({
                "success": True,
                "message": "Payment successful!", 
                "busNumber": trip.bus.bus_number,
                "departureDate": trip.departure_date.strftime("%Y-%m-%d"),
                "availableSeats": available_seats
            })
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data."})
    
    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

@login_required
def reserve_seat2(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            bus_number = data.get("busNumber")
            seat_number = data.get("seatNumber")

            if not bus_number or not seat_number:
                return JsonResponse({"success": False, "message": "Bus number and seat number are required!"})

            # ✅ Get the trip using bus_number
            trip = Trip.objects.filter(bus__bus_number=bus_number, status="Upcoming").first()
            if not trip:
                return JsonResponse({"success": False, "message": "Trip not found for the given bus!"})

            # ✅ Check if seat is already booked (either confirmed or pending)
            if Booking.objects.filter(trip=trip, seat_number=seat_number).exists():
                return JsonResponse({"success": False, "message": "This seat is already booked!"})

            # ✅ Create a pending booking (use trip instead of bus)
            booking = Booking.objects.create(
                user=request.user, 
                trip=trip,  
                seat_number=seat_number, 
                status="pending"
            )

            # ✅ Get user details
            full_name = request.user.get_full_name() or request.user.username  # Fallback to username
            email = request.user.email
            phone = getattr(request.user, "phone", "")  # Safer way to get phone attribute

            return JsonResponse({
                "success": True,
                "message": f"Seat {seat_number} reserved temporarily! Please complete payment.",
                "booking_id": booking.id,
                "route": trip.route.route_name,  # Ensure correct route retrieval
                "fare": trip.route.fare,  # Ensure correct fare retrieval
                "full_name": full_name,
                "email": email,
                "phone": phone
            })

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data!"})

        except IntegrityError:
            return JsonResponse({"success": False, "message": "This seat is already booked!"})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request!"})

@csrf_exempt
def make_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            booking_id = data.get("bookingId")
            phone_number = data.get("mpesaNumber")

            if not booking_id or not phone_number:
                return JsonResponse({"success": False, "message": "Missing required fields."})

            # Convert phone number to international format (E.164)
            if phone_number.startswith("07"):
                phone_number = "254" + phone_number[1:]
            elif phone_number.startswith("+254"):
                phone_number = phone_number[1:]  # Remove "+"
            elif not phone_number.startswith("254"):
                return JsonResponse({"success": False, "message": "Invalid phone number format. Use 07XXXXXXXX or 2547XXXXXXXX."})

            # Retrieve booking
            booking = Booking.objects.get(id=booking_id)
            amount = float(booking.trip.route.fare)  # Convert Decimal to float

            # **Step 1: Create a Payment record before initiating payment**
            payment = Payment.objects.create(
                user=booking.user,
                booking=booking,
                amount=amount,
                mpesa_transaction_id="pending",  # Will be updated after STK push response
                status="pending",
            )

            # Get access token
            access_token = MpesaAccessToken.get_access_token()
            api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            # Payment request payload
            payload = {
                "BusinessShortCode": LipanaMpesaPpassword.BusinessShortCode,
                "Password": LipanaMpesaPpassword.encode_password(),
                "Timestamp": LipanaMpesaPpassword.get_timestamp(),
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone_number,
                "PartyB": LipanaMpesaPpassword.BusinessShortCode,
                "PhoneNumber": phone_number,
                "CallBackURL": "https://cded-197-155-73-19.ngrok-free.app/mpesa_callback/",
                "AccountReference": "ENA Coach",
                "TransactionDesc": f"Bus ticket payment for {booking.trip.route.route_name}"
            }

            response = requests.post(api_url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                # **Step 2: Update the Payment record with MerchantRequestID**
                merchant_request_id = response_data.get("MerchantRequestID")
                if merchant_request_id:
                    payment.mpesa_transaction_id = merchant_request_id
                    payment.save()

                return JsonResponse({"success": True, "message": "Payment request sent successfully!"})
            else:
                return JsonResponse({"success": False, "message": response_data.get("errorMessage", "Payment failed.")})

        except Booking.DoesNotExist:
            return JsonResponse({"success": False, "message": "Booking not found."})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})


@csrf_exempt
def mpesa_callback(request):
    try:
        print("Received MPESA Callback:", request.body)  # Debugging Line
        data = json.loads(request.body)

        result_code = data["Body"]["stkCallback"]["ResultCode"]
        merchant_request_id = data["Body"]["stkCallback"]["MerchantRequestID"]
        transaction_id = data["Body"]["stkCallback"].get("MpesaReceiptNumber")  # Get MPESA Receipt Number

        print("Transaction ID:", transaction_id)  # Debugging Line
        print("Merchant Request ID:", merchant_request_id)  # Debugging Line

        if result_code == 0:  # Payment Successful
            payment = Payment.objects.filter(mpesa_transaction_id=merchant_request_id, status="pending").first()
            if not payment:
                return JsonResponse({"success": False, "message": "Payment record not found."})

            # ✅ Fix: Update Payment model with actual transaction ID
            if transaction_id:
                payment.mpesa_transaction_id = transaction_id  # Save the real MPESA Transaction ID
            payment.status = "completed"
            payment.save()

            booking = payment.booking
            booking.status = "confirmed"
            booking.save()

            return JsonResponse({
                "success": True,
                "message": "Payment successful!",
                "transactionId": transaction_id,
                "bookingId": booking.id,
                "amount": payment.amount
            })
        else:
            return JsonResponse({"success": False, "message": "Payment failed!"})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})






@csrf_exempt
def generate_receipt(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        payment = Payment.objects.filter(booking=booking, status="completed").first()  # Get completed payment

        if not payment:
            return JsonResponse({"success": False, "message": "No completed payment found for this booking."})

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer)
        
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(100, 780, "ENA Coach Bus Ticket Payment Receipt")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(100, 750, f"Transaction ID: {payment.mpesa_transaction_id}")  # ✅ Updated Transaction ID
        pdf.drawString(100, 730, f"Booking ID: {booking.id}")
        pdf.drawString(100, 710, f"Phone Number: {booking.user.phone}")  # ✅ Use 'phone' field
        pdf.drawString(100, 690, f"Amount Paid: KES {payment.amount}")
        pdf.drawString(100, 670, "Thank you for choosing ENA Coach!")
        
        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"Payment_Receipt_{booking_id}.pdf")

    except Booking.DoesNotExist:
        return JsonResponse({"success": False, "message": "Booking not found."})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})

@csrf_exempt
def check_payment_status(request, booking_id):
    try:
        payment = Payment.objects.filter(booking_id=booking_id, status="completed").first()

        if payment:
            return JsonResponse({
                "success": True,
                "status": "completed",
                "amount": payment.amount,
                "transactionId": payment.mpesa_transaction_id
            })
        else:
            return JsonResponse({"success": False, "status": "pending"})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})





def user_logout(request):
    logout(request)
    return redirect(reverse("user_login"))
