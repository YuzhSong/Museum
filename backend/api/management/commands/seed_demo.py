import json
from datetime import datetime, timedelta
from pathlib import Path

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


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "official_content.json"


class Command(BaseCommand):
    help = "Create demo accounts and official museum-based content for the course MVP."

    def handle(self, *args, **options):
        if not DATA_PATH.exists():
            raise FileNotFoundError(f"Missing scraped content file: {DATA_PATH}")

        payload = json.loads(DATA_PATH.read_text())

        admin = self.create_user("admin", "admin123", "admin@example.com", "13800000001", Profile.ROLE_ADMIN, "系统管理员")
        self.create_user("visitor", "visitor123", "visitor@example.com", "13800000002", Profile.ROLE_VISITOR, "游客示例")
        volunteer = self.create_user("volunteer", "volunteer123", "volunteer@example.com", "13800000003", Profile.ROLE_VOLUNTEER, "讲解员示例")
        volunteer.profile.service_area = "专题展厅与社教活动"
        volunteer.profile.save()

        exhibitions = self.seed_exhibitions(payload["exhibitions"])
        self.seed_collections(payload["collections"], exhibitions)
        self.seed_slots()
        activities = self.seed_activities(payload["activities"])
        self.seed_guides(exhibitions)

        for activity in activities:
            ActivityVolunteer.objects.get_or_create(activity=activity, volunteer=volunteer)

        self.stdout.write(self.style.SUCCESS("Demo data ready from official museum content."))
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

    def parse_date_range(self, text):
        parts = [part.strip() for part in text.split("-") if part.strip()]
        if len(parts) >= 2:
            start_text = parts[0]
            end_text = parts[-1]
        else:
            start_text = text.strip()
            end_text = text.strip()

        try:
            start_date = datetime.strptime(start_text, "%Y.%m.%d").date()
        except ValueError:
            start_date = timezone.localdate()
        try:
            end_date = datetime.strptime(end_text, "%Y.%m.%d").date()
        except ValueError:
            end_date = start_date + timedelta(days=120)
        return start_date, end_date

    def clean_summary(self, text, limit=900):
        text = " ".join((text or "").split())
        return text[:limit].rstrip()

    def seed_exhibitions(self, rows):
        created = []
        for row in rows:
            title = row["title"].strip()
            if not title or title == "404 Not Found":
                continue
            start_date, end_date = self.parse_date_range(row.get("date_range", ""))
            item, _ = Exhibition.objects.update_or_create(
                title=title,
                defaults={
                    "description": self.clean_summary(row.get("summary", "")),
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": row.get("location", "中国工艺美术馆"),
                    "status": Exhibition.STATUS_PUBLISHED,
                    "cover_image_url": row.get("image_local", ""),
                },
            )
            created.append(item)
        return created

    def seed_collections(self, rows, exhibitions):
        if not exhibitions:
            return
        targets = exhibitions[:3] if len(exhibitions) >= 3 else exhibitions
        for index, row in enumerate(rows):
            exhibition = targets[index % len(targets)]
            CollectionItem.objects.update_or_create(
                exhibition=exhibition,
                name=row["title"].strip(),
                defaults={
                    "category": row.get("category_name", "馆藏"),
                    "dynasty": "馆藏陈列",
                    "description": self.clean_summary(row.get("summary", ""), 220) or "馆藏信息暂不可用。",
                    "image_url": row.get("image_local", ""),
                },
            )

    def seed_slots(self):
        for day in range(1, 8):
            for time_slot in ["09:00-11:00", "11:00-13:00", "14:00-16:00", "16:00-17:00"]:
                VisitSlot.objects.update_or_create(
                    visit_date=timezone.localdate() + timedelta(days=day),
                    time_slot=time_slot,
                    defaults={"capacity": 60, "status": VisitSlot.STATUS_OPEN},
                )

    def seed_activities(self, rows):
        created = []
        base_time = timezone.now() + timedelta(days=3)
        workshop_rows = [
            {
                "title": "扎染手作体验课",
                "description": "围绕传统扎染工艺开展亲子手作体验，了解扎结、染色与纹样变化，完成可带走的小幅扎染作品。",
                "location": "非遗手工艺体验中心",
                "category": "亲子手作",
                "target_audience": "6 岁以上儿童与家长",
                "materials": "棉布方巾、植物染料、皮筋、手套、围裙、清洗盆",
                "preparation_note": "志愿者需提前 30 分钟分装染料与防护用品，管理员需确认耗材与清洁安排。",
                "duration_minutes": 90,
                "capacity": 18,
            },
            {
                "title": "福灯制作工坊",
                "description": "结合传统节令文化完成纸艺灯笼制作，适合儿童与家庭共同参与。",
                "location": "非遗手工艺体验中心",
                "category": "节庆手作",
                "target_audience": "亲子家庭",
                "materials": "灯笼骨架、彩纸、流苏、胶水、剪刀、毛笔",
                "preparation_note": "志愿者负责桌面分组和儿童安全提示，管理员需准备备用灯笼骨架。",
                "duration_minutes": 75,
                "capacity": 20,
            },
            {
                "title": "景泰蓝掐丝体验",
                "description": "以景泰蓝基础工艺为引导，体验掐丝、填彩与纹样设计。",
                "location": "非遗手工艺体验中心",
                "category": "工艺体验",
                "target_audience": "10 岁以上青少年与成人",
                "materials": "铜胎底板、掐丝铜线、彩砂、点胶工具、镊子",
                "preparation_note": "志愿者需示范掐丝步骤，管理员需按报名人数配齐安全工具。",
                "duration_minutes": 120,
                "capacity": 16,
            },
            {
                "title": "竹编扇小课堂",
                "description": "体验竹编基础穿插与扇面装饰，感受传统编织工艺的秩序感与手感。",
                "location": "非遗手工艺体验中心",
                "category": "编织体验",
                "target_audience": "8 岁以上观众",
                "materials": "竹篾、扇柄、棉线、压条、剪刀",
                "preparation_note": "志愿者需提前修整竹篾边缘，管理员需准备防割手套。",
                "duration_minutes": 90,
                "capacity": 18,
            },
            {
                "title": "制香体验课",
                "description": "了解传统香文化与制香流程，亲手完成香牌或香丸制作。",
                "location": "非遗手工艺体验中心",
                "category": "传统生活美学",
                "target_audience": "青少年与成人",
                "materials": "香粉、模具、压片器、香盒、手套",
                "preparation_note": "志愿者需维护制作台秩序，管理员需提前核对香材存量。",
                "duration_minutes": 80,
                "capacity": 16,
            },
            {
                "title": "玉雕纹样体验",
                "description": "围绕玉雕常见纹样进行描摹、刻画与审美讲解，适合展览延伸教学。",
                "location": "非遗手工艺体验中心",
                "category": "展览延伸",
                "target_audience": "9 岁以上观众",
                "materials": "纹样稿、描图纸、刻画笔、亚克力练习板",
                "preparation_note": "志愿者需协助低龄观众完成描摹，管理员需打印足量纹样稿。",
                "duration_minutes": 70,
                "capacity": 20,
            },
            {
                "title": "点翠首饰体验",
                "description": "从传统点翠工艺纹样出发，完成安全替代材料的胸针或挂饰制作。",
                "location": "非遗手工艺体验中心",
                "category": "首饰手作",
                "target_audience": "青少年与成人",
                "materials": "金属底托、替代羽片材料、珠饰、镊子、胶水",
                "preparation_note": "志愿者需提醒精细操作节奏，管理员需准备备用镊子与收纳盒。",
                "duration_minutes": 100,
                "capacity": 14,
            },
            {
                "title": "泥塑瑞兽工坊",
                "description": "以传统瑞兽造型为主题开展泥塑创作，适合儿童和家庭参与。",
                "location": "非遗手工艺体验中心",
                "category": "亲子手作",
                "target_audience": "5 岁以上儿童与家长",
                "materials": "超轻黏土、塑形刀、压板、展示底座",
                "preparation_note": "志愿者需看护儿童工具使用，管理员需预留作品晾置区域。",
                "duration_minutes": 75,
                "capacity": 24,
            },
            {
                "title": "敦煌石粉彩绘体验",
                "description": "结合敦煌壁画色彩与图案，体验石粉彩绘的上色与层次控制。",
                "location": "非遗手工艺体验中心",
                "category": "绘画体验",
                "target_audience": "12 岁以上观众",
                "materials": "石粉颜料、调色盘、线稿板、毛笔、围裙",
                "preparation_note": "志愿者负责讲解配色与清洗流程，管理员需准备防污台布。",
                "duration_minutes": 100,
                "capacity": 16,
            },
            {
                "title": "龙泉青瓷纹样彩绘",
                "description": "围绕龙泉青瓷器型与纹样进行釉下彩模拟体验，理解青瓷造型美学。",
                "location": "非遗手工艺体验中心",
                "category": "陶瓷体验",
                "target_audience": "青少年与成人",
                "materials": "素坯盘、颜料、勾线笔、展示托盘",
                "preparation_note": "志愿者需指导器型拿取与摆放，管理员需核对素坯破损率。",
                "duration_minutes": 90,
                "capacity": 18,
            },
            {
                "title": "漆艺小盒制作",
                "description": "从漆艺髹饰与装饰语言切入，完成小盒表面纹样创作。",
                "location": "非遗手工艺体验中心",
                "category": "漆艺体验",
                "target_audience": "10 岁以上观众",
                "materials": "木盒坯、漆艺装饰片、描金笔、保护手套",
                "preparation_note": "志愿者需提醒材料使用顺序，管理员需准备成品包装袋。",
                "duration_minutes": 90,
                "capacity": 16,
            },
            {
                "title": "木版年画印制体验",
                "description": "通过套色与拓印体验认识传统木版年画的印制流程与年俗寓意。",
                "location": "非遗手工艺体验中心",
                "category": "版画体验",
                "target_audience": "亲子家庭与学生团体",
                "materials": "版画底板、水性颜料、滚筒、宣纸、晾纸架",
                "preparation_note": "志愿者需维持印制顺序，管理员需准备充足晾晒空间。",
                "duration_minutes": 85,
                "capacity": 22,
            },
            {
                "title": "剪纸窗花课堂",
                "description": "以节令纹样与吉祥图案为主，体验基础剪纸折叠与纹样构成。",
                "location": "非遗手工艺体验中心",
                "category": "节庆手作",
                "target_audience": "7 岁以上观众",
                "materials": "彩纸、安全剪刀、图样模板、收纳袋",
                "preparation_note": "志愿者需重点照看低龄儿童剪刀使用，管理员需准备安全剪刀备用。",
                "duration_minutes": 60,
                "capacity": 24,
            },
            {
                "title": "盘扣香囊制作",
                "description": "围绕传统服饰细节与节庆配饰，体验基础盘扣与香囊拼装。",
                "location": "非遗手工艺体验中心",
                "category": "服饰手作",
                "target_audience": "青少年与成人",
                "materials": "盘扣绳、香囊包、香料包、针线包",
                "preparation_note": "志愿者需协助缝线步骤，管理员需准备成品展示样本。",
                "duration_minutes": 85,
                "capacity": 18,
            },
            {
                "title": "绒花发饰体验",
                "description": "了解绒花基础造型方法，完成一件可佩戴的小型发饰作品。",
                "location": "非遗手工艺体验中心",
                "category": "首饰手作",
                "target_audience": "青少年与成人",
                "materials": "绒条、金属丝、发夹底托、热熔胶、剪刀",
                "preparation_note": "志愿者需协助细节塑形，管理员需控制热熔工具的安全摆放。",
                "duration_minutes": 100,
                "capacity": 14,
            },
        ]
        for index, row in enumerate(rows):
            item, _ = MuseumActivity.objects.update_or_create(
                title=row["title"].strip(),
                defaults={
                    "description": self.clean_summary(row.get("summary", ""), 900),
                    "activity_time": base_time + timedelta(days=index * 5),
                    "location": "中国工艺美术馆公共活动区",
                    "category": "展演活动",
                    "target_audience": "公众观众",
                    "materials": "现场观演，无需自备材料。",
                    "preparation_note": "志愿者负责现场引导与秩序维护，管理员提前确认座椅与音响。",
                    "duration_minutes": 90,
                    "capacity": 40 if index == 0 else 24,
                    "status": MuseumActivity.STATUS_PUBLISHED,
                    "cover_image_url": row.get("image_local", ""),
                },
            )
            created.append(item)
        workshop_image = rows[0].get("image_local", "") if rows else ""
        for index, row in enumerate(workshop_rows, start=len(created)):
            item, _ = MuseumActivity.objects.update_or_create(
                title=row["title"],
                defaults={
                    "description": row["description"],
                    "activity_time": base_time + timedelta(days=index * 2),
                    "location": row["location"],
                    "category": row["category"],
                    "target_audience": row["target_audience"],
                    "materials": row["materials"],
                    "preparation_note": row["preparation_note"],
                    "duration_minutes": row["duration_minutes"],
                    "capacity": row["capacity"],
                    "status": MuseumActivity.STATUS_PUBLISHED,
                    "cover_image_url": workshop_image,
                },
            )
            created.append(item)
        return created

    def seed_guides(self, exhibitions):
        guide_templates = [
            (
                "一层主展区",
                "从序厅进入后，先沿主展墙浏览展览背景，再进入重点展柜与图像单元，最后回到公共休息区。",
                "建议先快速把握展览主题，再挑选 3 至 5 件重点作品停留观看。展签、图像和空间动线是理解展览叙事的最佳入口。",
            ),
            (
                "四层专题展区",
                "电梯抵达后从左侧专题展入口进入，顺时针完成主题内容、代表作品和多媒体展示区的参观。",
                "如果是第一次参观，可优先关注展览标题、时间线、代表作品和出口前的总结性内容，理解会更完整。",
            ),
            (
                "常设陈列区",
                "建议按材料门类依次观看：玉雕、陶瓷、金属工艺、织绣与漆艺，再进入延展陈列区。",
                "常设陈列更适合慢看。可从材料、工艺、纹样和用途四个角度观察，能更容易比较不同门类之间的审美差异。",
            ),
        ]

        for exhibition, template in zip(exhibitions[:3], guide_templates):
            GuideInfo.objects.update_or_create(
                hall_name=template[0],
                defaults={
                    "exhibition": exhibition,
                    "route_description": template[1],
                    "text_guide": template[2],
                    "map_image_url": exhibition.cover_image_url,
                },
            )
