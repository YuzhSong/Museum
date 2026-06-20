from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import ActivityVolunteer, AuthToken, CollectionItem, Exhibition, MuseumActivity, Profile, Reservation, VisitSlot, VolunteerRoleApplication


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
            time_slot="09:00-11:00",
            capacity=1,
        )
        self.second_slot = VisitSlot.objects.create(
            visit_date=self.slot.visit_date,
            time_slot="11:00-13:00",
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
        self.extra_activity = MuseumActivity.objects.create(
            title="非遗体验课",
            description="测试活动二",
            activity_time=timezone.now() + timedelta(days=5),
            location="非遗手工艺体验中心",
            capacity=10,
            status=MuseumActivity.STATUS_PUBLISHED,
        )

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

    def test_visitor_can_reserve_again_after_cancelling(self):
        client = self.login_client("visitor", "visitor123")
        first = client.post("/api/reservations/", {"slot_id": self.slot.id}, format="json")
        self.assertEqual(first.status_code, 201)

        reservation_id = first.json()["id"]
        cancel = client.post(f"/api/reservations/{reservation_id}/cancel/")
        self.assertEqual(cancel.status_code, 200)

        second = client.post("/api/reservations/", {"slot_id": self.slot.id}, format="json")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["status"], Reservation.STATUS_ACTIVE)
        self.assertEqual(second.json()["id"], reservation_id)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.booked_count, 1)

    def test_same_user_cannot_reserve_two_slots_on_same_day(self):
        client = self.login_client("visitor", "visitor123")

        first = client.post("/api/reservations/", {"slot_id": self.slot.id}, format="json")
        second = client.post("/api/reservations/", {"slot_id": self.second_slot.id}, format="json")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(second.json()["detail"], "同一天只能预约一个时间段，请先取消已预约场次。")
        self.assertEqual(
            Reservation.objects.filter(user=self.visitor, slot__visit_date=self.slot.visit_date, status=Reservation.STATUS_ACTIVE).count(),
            1,
        )

    def test_admin_can_view_reservations(self):
        visitor_client = self.login_client("visitor", "visitor123")
        visitor_client.post("/api/reservations/", {"slot_id": self.slot.id}, format="json")

        admin_client = self.login_client("admin", "admin123")
        response = admin_client.get("/api/admin/reservations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_admin_can_filter_reservations_by_time_slot(self):
        visitor_client = self.login_client("visitor", "visitor123")
        visitor_client.post("/api/reservations/", {"slot_id": self.slot.id}, format="json")

        other_visitor = self.create_user("visitor_b", "visitor123", Profile.ROLE_VISITOR)
        other_client = self.login_client("visitor_b", "visitor123")
        other_client.post("/api/reservations/", {"slot_id": self.second_slot.id}, format="json")

        admin_client = self.login_client("admin", "admin123")
        response = admin_client.get(f"/api/admin/reservations/?date={self.slot.visit_date}&time_slot=11:00-13:00")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["user"]["username"], other_visitor.username)
        self.assertEqual(response.json()[0]["slot"]["time_slot"], "11:00-13:00")

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

    def test_rejected_volunteer_application_can_be_applied_again(self):
        volunteer_client = self.login_client("volunteer", "volunteer123")
        admin_client = self.login_client("admin", "admin123")

        apply_response = volunteer_client.post(f"/api/volunteer/activities/{self.extra_activity.id}/apply/")
        self.assertEqual(apply_response.status_code, 200)
        rv = ActivityVolunteer.objects.get(activity=self.extra_activity, volunteer=self.volunteer)

        reject_response = admin_client.post(f"/api/admin/applications/{rv.id}/reject/")
        self.assertEqual(reject_response.status_code, 200)
        rv.refresh_from_db()
        self.assertEqual(rv.status, ActivityVolunteer.STATUS_REJECTED)

        available_response = volunteer_client.get("/api/volunteer/available-activities/")
        self.assertEqual(available_response.status_code, 200)
        self.assertIn(self.extra_activity.id, [item["id"] for item in available_response.json()])

        reapply_response = volunteer_client.post(f"/api/volunteer/activities/{self.extra_activity.id}/apply/")
        self.assertEqual(reapply_response.status_code, 200)
        rv.refresh_from_db()
        self.assertEqual(rv.status, ActivityVolunteer.STATUS_PENDING)

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

    def test_visitor_can_apply_for_volunteer_role_and_admin_can_approve(self):
        visitor_client = self.login_client("visitor", "visitor123")
        response = visitor_client.post(
            "/api/my/volunteer-role-application/",
            {"service_area": "社教活动", "motivation": "有讲解经验，希望参与馆内活动服务。"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], VolunteerRoleApplication.STATUS_PENDING)

        admin_client = self.login_client("admin", "admin123")
        pending = admin_client.get("/api/admin/volunteer-role-applications/")
        self.assertEqual(pending.status_code, 200)
        self.assertEqual(len(pending.json()), 1)

        app_id = pending.json()[0]["id"]
        approve = admin_client.post(f"/api/admin/volunteer-role-applications/{app_id}/approve/")
        self.assertEqual(approve.status_code, 200)
        self.visitor.profile.refresh_from_db()
        self.assertEqual(self.visitor.profile.role, Profile.ROLE_VOLUNTEER)

    def test_rejected_volunteer_role_application_can_be_resubmitted(self):
        visitor_client = self.login_client("visitor", "visitor123")
        first = visitor_client.post(
            "/api/my/volunteer-role-application/",
            {"service_area": "展厅讲解", "motivation": "首次申请"},
            format="json",
        )
        self.assertEqual(first.status_code, 201)

        admin_client = self.login_client("admin", "admin123")
        item = VolunteerRoleApplication.objects.get(user=self.visitor)
        reject = admin_client.post(f"/api/admin/volunteer-role-applications/{item.id}/reject/")
        self.assertEqual(reject.status_code, 200)

        second = visitor_client.post(
            "/api/my/volunteer-role-application/",
            {"service_area": "展厅讲解", "motivation": "补充了可服务时间，重新申请"},
            format="json",
        )
        self.assertEqual(second.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.status, VolunteerRoleApplication.STATUS_PENDING)
        self.assertEqual(item.motivation, "补充了可服务时间，重新申请")

    def test_pending_volunteer_role_application_can_be_updated(self):
        visitor_client = self.login_client("visitor", "visitor123")
        first = visitor_client.post(
            "/api/my/volunteer-role-application/",
            {"service_area": "社教活动", "motivation": "第一次填写"},
            format="json",
        )
        self.assertEqual(first.status_code, 201)

        second = visitor_client.post(
            "/api/my/volunteer-role-application/",
            {"service_area": "展厅讲解", "motivation": "补充讲解经验后更新"},
            format="json",
        )
        self.assertEqual(second.status_code, 200)

        item = VolunteerRoleApplication.objects.get(user=self.visitor)
        self.assertEqual(item.status, VolunteerRoleApplication.STATUS_PENDING)
        self.assertEqual(item.service_area, "展厅讲解")
        self.assertEqual(item.motivation, "补充讲解经验后更新")
