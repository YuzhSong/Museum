from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    ActivityRegistration,
    ActivityVolunteer,
    AuthToken,
    CollectionItem,
    Exhibition,
    GuideInfo,
    MuseumActivity,
    Profile,
    Reservation,
    VisitSlot,
)


def ok(data=None, status=200):
    return Response(data if data is not None else {}, status=status)


def fail(message, status=400):
    return Response({"detail": message}, status=status)


def current_user(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = AuthToken.objects.select_related("user", "user__profile").filter(key=header.removeprefix("Bearer ").strip()).first()
    return token.user if token else None


def require_user(request):
    user = current_user(request)
    if not user:
        return None, fail("请先登录。", 401)
    return user, None


def require_role(request, *roles):
    user, error = require_user(request)
    if error:
        return None, error
    role = user.profile.role
    if role not in roles:
        return None, fail("当前账号无权访问该功能。", 403)
    return user, None


def user_payload(user):
    profile = user.profile
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": profile.phone,
        "role": profile.role,
        "real_name": profile.real_name,
        "department": profile.department,
        "service_area": profile.service_area,
    }


def exhibition_payload(exhibition, include_collections=False):
    data = {
        "id": exhibition.id,
        "title": exhibition.title,
        "description": exhibition.description,
        "start_date": exhibition.start_date,
        "end_date": exhibition.end_date,
        "location": exhibition.location,
        "status": exhibition.status,
        "cover_image_url": exhibition.cover_image_url,
    }
    if include_collections:
        data["collections"] = [collection_payload(item) for item in exhibition.collections.all()]
    return data


def collection_payload(item):
    return {
        "id": item.id,
        "exhibition_id": item.exhibition_id,
        "exhibition_title": item.exhibition.title,
        "name": item.name,
        "category": item.category,
        "dynasty": item.dynasty,
        "description": item.description or "藏品信息暂不可用。",
        "image_url": item.image_url,
    }


def slot_payload(slot):
    return {
        "id": slot.id,
        "visit_date": slot.visit_date,
        "time_slot": slot.time_slot,
        "capacity": slot.capacity,
        "booked_count": slot.booked_count,
        "available_count": slot.available_count,
        "status": slot.status,
    }


def reservation_payload(reservation):
    return {
        "id": reservation.id,
        "user": user_payload(reservation.user),
        "slot": slot_payload(reservation.slot),
        "status": reservation.status,
        "created_at": reservation.created_at,
        "can_cancel": reservation.can_cancel(),
    }


def activity_payload(activity, include_volunteers=False):
    data = {
        "id": activity.id,
        "title": activity.title,
        "description": activity.description,
        "activity_time": activity.activity_time,
        "location": activity.location,
        "capacity": activity.capacity,
        "registered_count": activity.registered_count,
        "available_count": activity.available_count,
        "status": activity.status,
        "cover_image_url": activity.cover_image_url,
    }
    if include_volunteers:
        data["volunteer_ids"] = list(activity.volunteers.values_list("id", flat=True))
    return data


def registration_payload(registration):
    return {
        "id": registration.id,
        "user": user_payload(registration.user),
        "activity": activity_payload(registration.activity),
        "register_time": registration.register_time,
        "status": registration.status,
    }


def guide_payload(guide):
    return {
        "id": guide.id,
        "exhibition_id": guide.exhibition_id,
        "exhibition_title": guide.exhibition.title if guide.exhibition else "",
        "hall_name": guide.hall_name,
        "route_description": guide.route_description,
        "text_guide": guide.text_guide,
        "map_image_url": guide.map_image_url,
    }


@api_view(["POST"])
def register(request):
    data = request.data
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()
    if not username or not password:
        return fail("用户名和密码不能为空。")
    if User.objects.filter(username=username).exists():
        return fail("用户名已存在。")
    if email and User.objects.filter(email=email).exists():
        return fail("邮箱已存在。")
    if phone and Profile.objects.filter(phone=phone).exists():
        return fail("手机号已存在。")
    user = User.objects.create_user(username=username, password=password, email=email)
    Profile.objects.create(user=user, phone=phone or None, role=Profile.ROLE_VISITOR, real_name=data.get("real_name", ""))
    token = AuthToken.objects.create(user=user)
    return ok({"token": token.key, "user": user_payload(user)}, 201)


@api_view(["POST"])
def login(request):
    user = authenticate(username=request.data.get("username", ""), password=request.data.get("password", ""))
    if not user:
        return fail("账号或密码错误。", 401)
    token = AuthToken.objects.create(user=user)
    return ok({"token": token.key, "user": user_payload(user)})


@api_view(["POST"])
def logout(request):
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        AuthToken.objects.filter(key=header.removeprefix("Bearer ").strip()).delete()
    return ok({"message": "已退出登录。"})


@api_view(["GET"])
def profile(request):
    user, error = require_user(request)
    if error:
        return error
    return ok(user_payload(user))


@api_view(["GET"])
def exhibition_list(request):
    rows = Exhibition.objects.filter(status=Exhibition.STATUS_PUBLISHED).order_by("start_date")
    return ok([exhibition_payload(item) for item in rows])


@api_view(["GET"])
def exhibition_detail(request, pk):
    item = get_object_or_404(Exhibition, pk=pk, status=Exhibition.STATUS_PUBLISHED)
    return ok(exhibition_payload(item, include_collections=True))


@api_view(["GET"])
def exhibition_collections(request, pk):
    exhibition = get_object_or_404(Exhibition, pk=pk, status=Exhibition.STATUS_PUBLISHED)
    return ok([collection_payload(item) for item in exhibition.collections.all()])


@api_view(["GET"])
def collection_detail(request, pk):
    item = get_object_or_404(CollectionItem.objects.select_related("exhibition"), pk=pk)
    if item.exhibition.status != Exhibition.STATUS_PUBLISHED:
        return fail("藏品暂未公开。", 404)
    return ok(collection_payload(item))


@api_view(["GET"])
def visit_slots(request):
    qs = VisitSlot.objects.filter(status=VisitSlot.STATUS_OPEN, visit_date__gte=timezone.localdate())
    date = request.GET.get("date")
    if date:
        qs = qs.filter(visit_date=date)
    return ok([slot_payload(slot) for slot in qs])


@api_view(["GET", "POST"])
def reservations(request):
    user, error = require_user(request)
    if error:
        return error
    if request.method == "GET":
        rows = Reservation.objects.select_related("slot", "user", "user__profile").filter(user=user).order_by("-created_at")
        return ok([reservation_payload(row) for row in rows])
    slot_id = request.data.get("slot_id")
    if not slot_id:
        return fail("请选择参观场次。")
    with transaction.atomic():
        slot = get_object_or_404(VisitSlot.objects.select_for_update(), pk=slot_id)
        if not slot.has_quota() or slot.visit_date < timezone.localdate():
            return fail("该时间段名额已满或不可预约。")
        reservation = Reservation.objects.create(user=user, slot=slot)
        VisitSlot.objects.filter(pk=slot.pk).update(booked_count=F("booked_count") + 1)
        slot.refresh_from_db()
        reservation.slot = slot
    return ok(reservation_payload(reservation), 201)


@api_view(["POST"])
def cancel_reservation(request, pk):
    user, error = require_user(request)
    if error:
        return error
    with transaction.atomic():
        reservation = get_object_or_404(
            Reservation.objects.select_for_update().select_related("slot", "user", "user__profile"),
            pk=pk,
            user=user,
        )
        if not reservation.can_cancel():
            return fail("该预约不能重复取消或已过期。")
        reservation.status = Reservation.STATUS_CANCELLED
        reservation.save(update_fields=["status"])
        VisitSlot.objects.filter(pk=reservation.slot_id, booked_count__gt=0).update(booked_count=F("booked_count") - 1)
        reservation.slot.refresh_from_db()
    return ok(reservation_payload(reservation))


@api_view(["GET"])
def admin_reservations(request):
    _, error = require_role(request, Profile.ROLE_ADMIN)
    if error:
        return error
    qs = Reservation.objects.select_related("slot", "user", "user__profile").order_by("-created_at")
    date = request.GET.get("date")
    slot_id = request.GET.get("slot_id")
    if date:
        qs = qs.filter(slot__visit_date=date)
    if slot_id:
        qs = qs.filter(slot_id=slot_id)
    return ok([reservation_payload(row) for row in qs])


@api_view(["GET"])
def activity_list(request):
    rows = MuseumActivity.objects.filter(status=MuseumActivity.STATUS_PUBLISHED).order_by("activity_time")
    return ok([activity_payload(row) for row in rows])


@api_view(["GET"])
def activity_detail(request, pk):
    activity = get_object_or_404(MuseumActivity, pk=pk, status=MuseumActivity.STATUS_PUBLISHED)
    return ok(activity_payload(activity, include_volunteers=True))


@api_view(["POST"])
def register_activity(request, pk):
    user, error = require_user(request)
    if error:
        return error
    with transaction.atomic():
        activity = get_object_or_404(MuseumActivity.objects.select_for_update(), pk=pk)
        if not activity.is_registerable():
            return fail("活动已满或报名已截止。")
        try:
            registration = ActivityRegistration.objects.create(user=user, activity=activity)
        except IntegrityError:
            return fail("你已报名该活动。")
    return ok(registration_payload(registration), 201)


@api_view(["GET"])
def my_activity_registrations(request):
    user, error = require_user(request)
    if error:
        return error
    rows = ActivityRegistration.objects.select_related("activity", "user", "user__profile").filter(user=user).order_by("-register_time")
    return ok([registration_payload(row) for row in rows])


@api_view(["GET"])
def volunteer_activities(request):
    user, error = require_role(request, Profile.ROLE_VOLUNTEER)
    if error:
        return error
    rows = MuseumActivity.objects.filter(activityvolunteer__volunteer=user).order_by("activity_time")
    return ok([activity_payload(row) for row in rows])


@api_view(["GET"])
def volunteer_activity_registrations(request, pk):
    user, error = require_role(request, Profile.ROLE_VOLUNTEER)
    if error:
        return error
    if not ActivityVolunteer.objects.filter(activity_id=pk, volunteer=user).exists():
        return fail("只能查看自己负责活动的报名情况。", 403)
    rows = ActivityRegistration.objects.select_related("activity", "user", "user__profile").filter(activity_id=pk).order_by("register_time")
    return ok([registration_payload(row) for row in rows])


@api_view(["GET"])
def guide_list(request):
    qs = GuideInfo.objects.select_related("exhibition").all().order_by("hall_name")
    return ok([guide_payload(row) for row in qs])


@api_view(["GET"])
def guide_detail(request, pk):
    return ok(guide_payload(get_object_or_404(GuideInfo.objects.select_related("exhibition"), pk=pk)))


def exhibition_from_request(data, instance=None):
    item = instance or Exhibition()
    for field in ["title", "description", "start_date", "end_date", "location", "status", "cover_image_url"]:
        if field in data:
            setattr(item, field, data[field])
    item.save()
    return item


def collection_from_request(data, instance=None):
    item = instance or CollectionItem()
    item.exhibition_id = data.get("exhibition_id", getattr(item, "exhibition_id", None))
    for field in ["name", "category", "dynasty", "description", "image_url"]:
        if field in data:
            setattr(item, field, data[field])
    item.save()
    return item


def activity_from_request(data, instance=None):
    item = instance or MuseumActivity()
    for field in ["title", "description", "activity_time", "location", "capacity", "status", "cover_image_url"]:
        if field in data:
            value = data[field]
            if field == "activity_time" and isinstance(value, str):
                parsed = parse_datetime(value)
                if parsed and timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
                value = parsed or value
            setattr(item, field, value)
    item.save()
    if "volunteer_ids" in data:
        ActivityVolunteer.objects.filter(activity=item).delete()
        for volunteer_id in data.get("volunteer_ids") or []:
            volunteer = User.objects.filter(pk=volunteer_id, profile__role=Profile.ROLE_VOLUNTEER).first()
            if volunteer:
                ActivityVolunteer.objects.get_or_create(activity=item, volunteer=volunteer)
    return item


def guide_from_request(data, instance=None):
    item = instance or GuideInfo()
    item.exhibition_id = data.get("exhibition_id") or None
    for field in ["hall_name", "route_description", "text_guide", "map_image_url"]:
        if field in data:
            setattr(item, field, data[field])
    item.save()
    return item


@api_view(["GET", "POST"])
def admin_exhibitions(request):
    _, error = require_role(request, Profile.ROLE_ADMIN)
    if error:
        return error
    if request.method == "GET":
        return ok([exhibition_payload(row) for row in Exhibition.objects.order_by("-created_at")])
    return ok(exhibition_payload(exhibition_from_request(request.data)), 201)


@api_view(["PUT", "DELETE"])
def admin_exhibition_detail(request, pk):
    _, error = require_role(request, Profile.ROLE_ADMIN)
    if error:
        return error
    item = get_object_or_404(Exhibition, pk=pk)
    if request.method == "DELETE":
        item.status = Exhibition.STATUS_CLOSED
        item.save(update_fields=["status"])
    else:
        item = exhibition_from_request(request.data, item)
    return ok(exhibition_payload(item))


@api_view(["GET", "POST"])
def admin_collections(request):
    _, error = require_role(request, Profile.ROLE_ADMIN)
    if error:
        return error
    if request.method == "GET":
        rows = CollectionItem.objects.select_related("exhibition").all()
        return ok([collection_payload(row) for row in rows])
    return ok(collection_payload(collection_from_request(request.data)), 201)


@api_view(["PUT", "DELETE"])
def admin_collection_detail(request, pk):
    _, error = require_role(request, Profile.ROLE_ADMIN)
    if error:
        return error
    item = get_object_or_404(CollectionItem, pk=pk)
    if request.method == "DELETE":
        item.delete()
        return ok({"message": "藏品已删除。"})
    return ok(collection_payload(collection_from_request(request.data, item)))


@api_view(["GET", "POST"])
def admin_activities(request):
    _, error = require_role(request, Profile.ROLE_ADMIN)
    if error:
        return error
    if request.method == "GET":
        return ok([activity_payload(row, include_volunteers=True) for row in MuseumActivity.objects.order_by("-activity_time")])
    return ok(activity_payload(activity_from_request(request.data), include_volunteers=True), 201)


@api_view(["PUT", "DELETE"])
def admin_activity_detail(request, pk):
    _, error = require_role(request, Profile.ROLE_ADMIN)
    if error:
        return error
    item = get_object_or_404(MuseumActivity, pk=pk)
    if request.method == "DELETE":
        item.status = MuseumActivity.STATUS_CLOSED
        item.save(update_fields=["status"])
    else:
        item = activity_from_request(request.data, item)
    return ok(activity_payload(item, include_volunteers=True))


@api_view(["GET", "POST"])
def admin_guides(request):
    _, error = require_role(request, Profile.ROLE_ADMIN)
    if error:
        return error
    if request.method == "GET":
        return ok([guide_payload(row) for row in GuideInfo.objects.select_related("exhibition").all()])
    return ok(guide_payload(guide_from_request(request.data)), 201)


@api_view(["PUT", "DELETE"])
def admin_guide_detail(request, pk):
    _, error = require_role(request, Profile.ROLE_ADMIN)
    if error:
        return error
    item = get_object_or_404(GuideInfo, pk=pk)
    if request.method == "DELETE":
        item.delete()
        return ok({"message": "导览信息已删除。"})
    return ok(guide_payload(guide_from_request(request.data, item)))
