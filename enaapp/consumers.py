import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Sum
from asgiref.sync import sync_to_async
from enaapp.models import Booking, Payment

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handles WebSocket connection"""
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"✅ WebSocket connected for user {self.user}")

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"⚠️ WebSocket disconnected for user {self.user}")

    async def receive(self, text_data):
        """Handles messages received from frontend"""
        data = json.loads(text_data)

        if data.get("type") == "fetch_dashboard":
            await self.send_dashboard_data()
        elif data.get("type") == "ping":
            await self.send(json.dumps({"type": "pong"}))  # Keep-alive response

    async def send_dashboard_data(self):
        """Fetch and send updated dashboard data to the frontend."""
        total_bookings = await sync_to_async(Booking.objects.filter(user=self.user).count)()

        # ✅ Update upcoming trips logic to check Trip table for actual upcoming trips
        upcoming_trips = await sync_to_async(lambda: Booking.objects.filter(
            user=self.user,
            trip__status="Upcoming",  # Check the Trip table status
            trip__departure_date__gte=datetime.today()  # Ensure the trip is still in the future
        ).count())()

        total_payments = await sync_to_async(lambda: Payment.objects.filter(user=self.user).aggregate(
            total_amount=Sum("amount")
        )["total_amount"] or 0)()

        recent_bookings = await sync_to_async(lambda: list(
            Booking.objects.filter(user=self.user)
            .select_related("trip", "trip__bus", "trip__route")  # ✅ Added trip__route for route_name
            .order_by("-booking_date")[:5]
            .values(
                "trip__bus__bus_number", 
                "trip__route__route_name",  # ✅ Fetch route name correctly
                "trip__departure_time", 
                "seat_number", 
                "status", 
                "booking_date"
            )
        ))()

        recent_payments = await sync_to_async(lambda: list(
            Payment.objects.filter(user=self.user)
            .order_by("-transaction_date")[:5]
            .values("amount", "mpesa_transaction_id", "status", "transaction_date")
        ))()

        # Convert datetime fields to readable format
        for booking in recent_bookings:
            booking["trip__departure_time"] = booking["trip__departure_time"].strftime("%H:%M:%S")
            booking["booking_date"] = booking["booking_date"].strftime("%Y-%m-%d")

        for payment in recent_payments:
            payment["transaction_date"] = payment["transaction_date"].strftime("%Y-%m-%d %H:%M:%S")

        await self.send(json.dumps({
            "totalBookings": total_bookings,
            "upcomingTrips": upcoming_trips,  # ✅ Now correctly updating based on Trip table
            "totalPayments": round(total_payments, 2),
            "recentBookings": recent_bookings,
            "recentPayments": recent_payments,
        }, default=str))
