from datetime import timedelta
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_auth_token_expires_at():
    return timezone.now() + timedelta(days=7)


class Profile(models.Model):
    ROLE_VISITOR = "visitor"
    ROLE_ADMIN = "admin"
    ROLE_VOLUNTEER = "volunteer"
    ROLE_CHOICES = [
        (ROLE_VISITOR, "游客"),
        (ROLE_ADMIN, "管理员"),
        (ROLE_VOLUNTEER, "志愿者/讲解员"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_VISITOR)
    real_name = models.CharField(max_length=80, blank=True)
    department = models.CharField(max_length=120, blank=True)
    service_area = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}({self.role})"


class AuthToken(models.Model):
    key = models.CharField(max_length=64, unique=True, default=secrets.token_hex)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_tokens")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_auth_token_expires_at)


class Exhibition(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "草稿"),
        (STATUS_PUBLISHED, "已发布"),
        (STATUS_CLOSED, "已下架"),
    ]

    title = models.CharField(max_length=160)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PUBLISHED)
    cover_image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CollectionItem(models.Model):
    exhibition = models.ForeignKey(Exhibition, on_delete=models.CASCADE, related_name="collections")
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=80)
    dynasty = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


class VisitSlot(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "可预约"),
        (STATUS_CLOSED, "已关闭"),
    ]

    visit_date = models.DateField()
    time_slot = models.CharField(max_length=60)
    capacity = models.PositiveIntegerField(default=50)
    booked_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)

    class Meta:
        unique_together = ("visit_date", "time_slot")
        ordering = ["visit_date", "time_slot"]

    @property
    def available_count(self):
        return max(self.capacity - self.booked_count, 0)

    def has_quota(self):
        return self.status == self.STATUS_OPEN and self.booked_count < self.capacity

    def __str__(self):
        return f"{self.visit_date} {self.time_slot}"


class Reservation(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "已预约"),
        (STATUS_CANCELLED, "已取消"),
        (STATUS_EXPIRED, "已过期"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    slot = models.ForeignKey(VisitSlot, on_delete=models.PROTECT, related_name="reservations")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "slot")

    def can_cancel(self):
        return self.status == self.STATUS_ACTIVE and self.slot.visit_date >= timezone.localdate()


class MuseumActivity(models.Model):
    STATUS_PUBLISHED = "published"
    STATUS_CLOSED = "closed"
    STATUS_DRAFT = "draft"
    STATUS_CHOICES = [
        (STATUS_PUBLISHED, "开放报名"),
        (STATUS_CLOSED, "已下架/截止"),
        (STATUS_DRAFT, "草稿"),
    ]

    title = models.CharField(max_length=160)
    description = models.TextField()
    activity_time = models.DateTimeField()
    location = models.CharField(max_length=120)
    category = models.CharField(max_length=80, blank=True)
    target_audience = models.CharField(max_length=120, blank=True)
    materials = models.TextField(blank=True)
    preparation_note = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=90)
    capacity = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PUBLISHED)
    cover_image_url = models.URLField(blank=True)
    volunteers = models.ManyToManyField(settings.AUTH_USER_MODEL, through="ActivityVolunteer", related_name="assigned_activities", blank=True)

    @property
    def registered_count(self):
        return self.registrations.filter(status=ActivityRegistration.STATUS_ACTIVE).count()

    @property
    def available_count(self):
        return max(self.capacity - self.registered_count, 0)

    def is_registerable(self):
        return self.status == self.STATUS_PUBLISHED and self.activity_time > timezone.now() and self.registered_count < self.capacity

    def __str__(self):
        return self.title


class ActivityRegistration(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "已报名"),
        (STATUS_CANCELLED, "已取消"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_registrations")
    activity = models.ForeignKey(MuseumActivity, on_delete=models.CASCADE, related_name="registrations")
    register_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    class Meta:
        unique_together = ("user", "activity")


class GuideInfo(models.Model):
    exhibition = models.ForeignKey(Exhibition, on_delete=models.SET_NULL, related_name="guides", blank=True, null=True)
    hall_name = models.CharField(max_length=120)
    route_description = models.TextField()
    text_guide = models.TextField()
    map_image_url = models.URLField(blank=True)

    def __str__(self):
        return self.hall_name


class ActivityVolunteer(models.Model):
    activity = models.ForeignKey(MuseumActivity, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("activity", "volunteer")

# Create your models here.
