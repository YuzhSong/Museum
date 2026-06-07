from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import (
    ActivityVolunteer,
    CollectionItem,
    Exhibition,
    GuideInfo,
    MuseumActivity,
    Profile,
    VisitSlot,
)


class Command(BaseCommand):
    help = "Create demo accounts and museum data for the course MVP."

    def handle(self, *args, **options):
        admin = self.create_user("admin", "admin123", "admin@example.com", "13800000001", Profile.ROLE_ADMIN, "系统管理员")
        visitor = self.create_user("visitor", "visitor123", "visitor@example.com", "13800000002", Profile.ROLE_VISITOR, "游客示例")
        volunteer = self.create_user("volunteer", "volunteer123", "volunteer@example.com", "13800000003", Profile.ROLE_VOLUNTEER, "讲解员示例")
        volunteer.profile.service_area = "二层专题展厅"
        volunteer.profile.save()

        ex1, _ = Exhibition.objects.update_or_create(
            title="大国匠作：中国工艺美术精品展",
            defaults={
                "description": "集中展示玉雕、漆器、陶瓷、织绣等代表性工艺门类，呈现传统工艺在当代语境中的传承与创新。",
                "start_date": timezone.localdate(),
                "end_date": timezone.localdate() + timedelta(days=90),
                "location": "一层 1 号展厅",
                "status": Exhibition.STATUS_PUBLISHED,
                "cover_image_url": "https://images.unsplash.com/photo-1601841197690-6f0838bdb005?auto=format&fit=crop&w=1200&q=80",
            },
        )
        ex2, _ = Exhibition.objects.update_or_create(
            title="丝路纹样与非遗新生",
            defaults={
                "description": "围绕丝路纹样、织染技艺和当代文创设计，展示非遗技艺如何进入新的公共生活。",
                "start_date": timezone.localdate() + timedelta(days=7),
                "end_date": timezone.localdate() + timedelta(days=120),
                "location": "二层 3 号展厅",
                "status": Exhibition.STATUS_PUBLISHED,
                "cover_image_url": "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?auto=format&fit=crop&w=1200&q=80",
            },
        )

        CollectionItem.objects.update_or_create(
            exhibition=ex1,
            name="青花缠枝纹瓷瓶",
            defaults={
                "category": "陶瓷",
                "dynasty": "明代风格",
                "description": "器型挺拔，纹饰层次清晰，体现传统青花装饰的秩序感与手工温度。",
                "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=1000&q=80",
            },
        )
        CollectionItem.objects.update_or_create(
            exhibition=ex1,
            name="剔红山水人物纹漆盒",
            defaults={
                "category": "漆器",
                "dynasty": "清代风格",
                "description": "以层层髹漆后雕刻成纹，山石树木与人物活动相互映衬。",
                "image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1000&q=80",
            },
        )
        CollectionItem.objects.update_or_create(
            exhibition=ex2,
            name="云气纹织锦片",
            defaults={
                "category": "织绣",
                "dynasty": "当代复原",
                "description": "以丝路纹样为基础进行再设计，适合观察纹样结构和色彩节奏。",
                "image_url": "https://images.unsplash.com/photo-1580635089861-2f9d13865a44?auto=format&fit=crop&w=1000&q=80",
            },
        )

        for day in range(1, 6):
            for time_slot in ["09:30-11:30", "13:30-15:30", "15:30-17:00"]:
                VisitSlot.objects.update_or_create(
                    visit_date=timezone.localdate() + timedelta(days=day),
                    time_slot=time_slot,
                    defaults={"capacity": 30, "status": VisitSlot.STATUS_OPEN},
                )

        activity, _ = MuseumActivity.objects.update_or_create(
            title="周末公益讲解：走近传统工艺",
            defaults={
                "description": "由志愿者带领观众梳理展品背后的材料、技法与审美线索。",
                "activity_time": timezone.now() + timedelta(days=10, hours=3),
                "location": "一层服务台集合",
                "capacity": 20,
                "status": MuseumActivity.STATUS_PUBLISHED,
                "cover_image_url": "https://images.unsplash.com/photo-1518998053901-5348d3961a04?auto=format&fit=crop&w=1200&q=80",
            },
        )
        ActivityVolunteer.objects.get_or_create(activity=activity, volunteer=volunteer)

        MuseumActivity.objects.update_or_create(
            title="亲子手作体验：纹样拓印",
            defaults={
                "description": "面向家庭观众的轻量手作体验，了解传统纹样如何从器物走向纸面。",
                "activity_time": timezone.now() + timedelta(days=15, hours=2),
                "location": "教育活动室",
                "capacity": 16,
                "status": MuseumActivity.STATUS_PUBLISHED,
                "cover_image_url": "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?auto=format&fit=crop&w=1200&q=80",
            },
        )

        GuideInfo.objects.update_or_create(
            hall_name="一层精品展厅",
            defaults={
                "exhibition": ex1,
                "route_description": "入口服务台 -> 玉雕展柜 -> 陶瓷展区 -> 漆器展区 -> 文创出口。",
                "text_guide": "建议先从材料门类入手，再观察同一题材在不同工艺中的表现差异。",
                "map_image_url": "https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&w=1200&q=80",
            },
        )
        GuideInfo.objects.update_or_create(
            hall_name="二层专题展厅",
            defaults={
                "exhibition": ex2,
                "route_description": "扶梯上二层 -> 丝路纹样墙 -> 织染技艺区 -> 当代设计区。",
                "text_guide": "重点关注纹样如何在历史传播中发生变体，以及当代设计中的转译方式。",
                "map_image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Accounts: admin/admin123, visitor/visitor123, volunteer/volunteer123")

    def create_user(self, username, password, email, phone, role, real_name):
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if created or not user.has_usable_password():
            user.set_password(password)
            user.save()
        if user.email != email:
            user.email = email
            user.save(update_fields=["email"])
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.phone = phone
        profile.role = role
        profile.real_name = real_name
        profile.save()
        return user
