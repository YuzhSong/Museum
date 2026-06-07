from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import ActivityVolunteer, MuseumActivity, Profile, VisitSlot


class ApiFlowTests(TestCase):
    def setUp(self):
        self.visitor = self.create_user("visitor", "visitor123", Profile.ROLE_VISITOR)
        self.admin = self.create_user("admin", "admin123", Profile.ROLE_ADMIN)
        self.volunteer = self.create_user("volunteer", "volunteer123", Profile.ROLE_VOLUNTEER)
        self.slot = VisitSlot.objects.create(
            visit_date=timezone.localdate() + timedelta(days=1),
            time_slot="09:30-11:30",
            capacity=1,
        )
        self.activity = MuseumActivity.objects.create(
            title="公益讲解",
            description="测试活动",
            activity_time=timezone.now() + timedelta(days=3),
            location="一层大厅",
            capacity=10,
        )
        ActivityVolunteer.objects.create(activity=self.activity, volunteer=self.volunteer)

    def create_user(self, username, password, role):
        user = User.objects.create_user(username=username, password=password, email=f"{username}@example.com")
        Profile.objects.create(user=user, role=role, phone=f"13800000{user.id:03d}")
        return user

    def login_client(self, username, password):
        client = APIClient()
        response = client.post("/api/login/", {"username": username, "password": password}, format="json")
        self.assertEqual(response.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['token']}")
        return client

    def test_visitor_can_reserve_and_cancel_ticket(self):
        client = self.login_client("visitor", "visitor123")
        response = client.post("/api/reservations/", {"slot_id": self.slot.id}, format="json")
        self.assertEqual(response.status_code, 201)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked_count, 1)

        reservation_id = response.json()["id"]
        response = client.post(f"/api/reservations/{reservation_id}/cancel/")
        self.assertEqual(response.status_code, 200)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked_count, 0)

    def test_admin_can_view_reservations(self):
        visitor_client = self.login_client("visitor", "visitor123")
        visitor_client.post("/api/reservations/", {"slot_id": self.slot.id}, format="json")

        admin_client = self.login_client("admin", "admin123")
        response = admin_client.get("/api/admin/reservations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_volunteer_only_sees_assigned_activity_registrations(self):
        visitor_client = self.login_client("visitor", "visitor123")
        visitor_client.post(f"/api/activities/{self.activity.id}/register/")

        volunteer_client = self.login_client("volunteer", "volunteer123")
        response = volunteer_client.get(f"/api/volunteer/activities/{self.activity.id}/registrations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["user"]["username"], "visitor")
