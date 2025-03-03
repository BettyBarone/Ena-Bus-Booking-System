from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


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
