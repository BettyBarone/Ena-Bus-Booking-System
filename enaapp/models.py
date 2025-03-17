from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings
from django.utils.timezone import now 


class CustomUserManager(BaseUserManager):
    """Custom manager to use email for authentication."""

    def create_user(self, email, password=None, username=None, **extra_fields):
        """Create a normal user with email authentication (no username required)."""
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)

        # Auto-generate a username for normal users
        if not extra_fields.get("is_superuser", False) and not username:
            username = email.split("@")[0]  # Extract email prefix as username

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """Create a superuser with email, username, and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not username:
            raise ValueError("Superuser must have a username.")
        if not password:
            raise ValueError("Superuser must have a password.")

        return self.create_user(email, password, username, **extra_fields)


class CustomUser(AbstractUser):
    """Custom User model with phone number."""
    email = models.EmailField(unique=True)  # Ensure email is unique
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)  # Allow blank for normal users

    objects = CustomUserManager()  # Use custom manager

    # Use email for authentication instead of username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # Superusers require a username

    def __str__(self):
        return self.username if self.username else self.email
    

class Bus(models.Model):
    """Model representing a bus."""
    bus_number = models.CharField(max_length=20, unique=True)
    route = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = "Buses"  # Correct pluralization

    def __str__(self):
        return f"{self.bus_number} - {self.route}"

class Trip(models.Model):
    """Model representing a bus trip (schedule)."""
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name="trips")
    route = models.CharField(max_length=255, default="Nairobi to Mombasa")  # Set default route
    departure_time = models.TimeField()
    departure_date = models.DateField()
    available_seats = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.bus.bus_number} - {self.route} - {self.departure_date} {self.departure_time}"



class Booking(models.Model):  
    """Model representing a user's booking."""  
    STATUS_CHOICES = [  
        ("pending", "Pending"),  
        ("confirmed", "Confirmed"),  
    ]  

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")  
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="bookings")  
    seat_number = models.CharField(max_length=5)  
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")  
    booking_date = models.DateTimeField(default=now)  # Use default instead of auto_now_add=True  

    def __str__(self):  
        return f"Booking {self.id} - {self.user.email} - {self.trip.bus.bus_number} - Seat {self.seat_number}"  


class Payment(models.Model):
    """Model representing a payment transaction."""
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_transaction_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.mpesa_transaction_id} - {self.user.email} - KES {self.amount}"


class Seat(models.Model):
    """Model representing an individual seat in a trip."""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=5)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.seat_number} - {self.trip.bus.bus_number} ({'Booked' if self.is_booked else 'Available'})"

    class Meta:
        unique_together = ("trip", "seat_number")
