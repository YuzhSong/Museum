from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import ActivityVolunteer, AuthToken, CollectionItem, Exhibition, MuseumActivity, Profile, Reservation, VisitSlot


class ApiFlowTests(TestCase):
    def setUp(self):
        self.visitor = self.create_user("visitor", "visitor123", Profile.ROLE_VISITOR)
        self.admin = self.create_user("admin", "admin123", Profile.ROLE_ADMIN)
        self.volunteer = self.create_user("volunteer", "volunteer123", Profile.ROLE_VOLUNTEER)
        self.exhibition = Exhibition.objects.create(
            title="青铜器特展",
            description="测试展览",
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=30),
            location="一号馆",
        )
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

    def test_expired_token_cannot_access_protected_endpoint(self):
        client = self.login_client("visitor", "visitor123")
        AuthToken.objects.filter(user=self.visitor).update(expires_at=timezone.now() - timedelta(minutes=1))

        response = client.get("/api/reservations/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "请先登录。")

    def test_same_user_cannot_reserve_same_slot_twice(self):
        client = self.login_client("visitor", "visitor123")

        first_response = client.post("/api/reservations/", {"slot_id": self.slot.id}, format="json")
        second_response = client.post("/api/reservations/", {"slot_id": self.slot.id}, format="json")

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(second_response.json()["detail"], "你已预约过该场次。")
        self.assertEqual(Reservation.objects.filter(user=self.visitor, slot=self.slot).count(), 1)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked_count, 1)

    def test_non_admin_cannot_access_admin_reservations(self):
        client = self.login_client("visitor", "visitor123")

        response = client.get("/api/admin/reservations/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "当前账号无权访问该功能。")

    def test_admin_can_list_volunteers(self):
        admin_client = self.login_client("admin", "admin123")

        response = admin_client.get("/api/admin/volunteers/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["username"], "volunteer")

    def test_non_admin_cannot_access_admin_volunteers(self):
        client = self.login_client("visitor", "visitor123")

        response = client.get("/api/admin/volunteers/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "当前账号无权访问该功能。")

    def test_volunteer_only_sees_assigned_activity_registrations(self):
        visitor_client = self.login_client("visitor", "visitor123")
        visitor_client.post(f"/api/activities/{self.activity.id}/register/")

        volunteer_client = self.login_client("volunteer", "volunteer123")
        response = volunteer_client.get(f"/api/volunteer/activities/{self.activity.id}/registrations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["user"]["username"], "visitor")

    def test_admin_collection_create_requires_exhibition_id_when_missing(self):
        admin_client = self.login_client("admin", "admin123")

        response = admin_client.post(
            "/api/admin/collections/",
            {
                "name": "四羊方尊",
                "category": "青铜器",
                "dynasty": "商朝",
                "description": "测试藏品",
                "image_url": "https://example.com/bronze.jpg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "必须选择所属展览。")
        self.assertEqual(CollectionItem.objects.count(), 0)

    def test_admin_collection_create_requires_exhibition_id_when_null(self):
        admin_client = self.login_client("admin", "admin123")

        response = admin_client.post(
            "/api/admin/collections/",
            {
                "exhibition_id": None,
                "name": "四羊方尊",
                "category": "青铜器",
                "dynasty": "商朝",
                "description": "测试藏品",
                "image_url": "https://example.com/bronze.jpg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "必须选择所属展览。")
        self.assertEqual(CollectionItem.objects.count(), 0)

    def test_admin_collection_create_succeeds_with_exhibition_id(self):
        admin_client = self.login_client("admin", "admin123")

        response = admin_client.post(
            "/api/admin/collections/",
            {
                "exhibition_id": self.exhibition.id,
                "name": "四羊方尊",
                "category": "青铜器",
                "dynasty": "商朝",
                "description": "测试藏品",
                "image_url": "https://example.com/bronze.jpg",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["exhibition_id"], self.exhibition.id)
        self.assertEqual(response.json()["exhibition_title"], self.exhibition.title)
        self.assertEqual(CollectionItem.objects.count(), 1)

    def test_register_rejects_invalid_phone(self):
        client = APIClient()

        response = client.post(
            "/api/register/",
            {"username": "visitor2", "password": "visitor123", "phone": "12345"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "手机号格式不正确。")

    def test_register_rejects_short_password(self):
        client = APIClient()

        response = client.post(
            "/api/register/",
            {"username": "visitor2", "password": "123"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "密码长度不能少于 6 位。")

    def test_login_replaces_old_token(self):
        client = APIClient()
        first = client.post("/api/login/", {"username": "visitor", "password": "visitor123"}, format="json")
        second = client.post("/api/login/", {"username": "visitor", "password": "visitor123"}, format="json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(AuthToken.objects.filter(user=self.visitor).count(), 1)
        self.assertNotEqual(first.json()["token"], second.json()["token"])

    def test_admin_can_create_activity_with_material_fields(self):
        admin_client = self.login_client("admin", "admin123")

        response = admin_client.post(
            "/api/admin/activities/",
            {
                "title": "扎染体验课",
                "description": "测试活动",
                "activity_time": (timezone.now() + timedelta(days=5)).isoformat(),
                "location": "非遗手工艺体验中心",
                "category": "亲子手作",
                "target_audience": "亲子家庭",
                "materials": "棉布、染料、手套",
                "preparation_note": "提前备料",
                "duration_minutes": 90,
                "capacity": 18,
                "status": "published",
                "volunteer_ids": [self.volunteer.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["category"], "亲子手作")
        self.assertEqual(response.json()["materials"], "棉布、染料、手套")
        self.assertEqual(response.json()["duration_minutes"], 90)
