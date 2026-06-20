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
ACTIVITY_ROWS = [
    {
        "title": "嵊州竹编蹴鞠体验",
        "description": "围绕嵊州竹编的历史与编织技法展开，课程将带领观众了解这项国家级非遗的工艺特点，并动手完成竹编蹴鞠球，感受传统竹编的文化韵味与结构之美。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "青少年与公众观众",
        "materials": "竹篾、球体骨架、编织辅件由现场统一提供。",
        "preparation_note": "建议提前到场熟悉编织步骤，细节制作阶段请听从现场老师指导。",
        "duration_minutes": 90,
        "capacity": 18,
        "cover_image_url": "/static/official/activities/shengzhou-bamboo-weaving.jpg",
    },
    {
        "title": "传统制香体验",
        "description": "课程以清苑传统制香技艺为主线，介绍中国香文化的历史源流和配香工序，参与者可体验选料、配料与成型，完成香包、香锤、香牌或香珠等作品。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "青少年与成人",
        "materials": "香粉、模具、香材配件由现场统一提供。",
        "preparation_note": "课程包含粉料操作，建议穿着便于活动的服装并遵循现场操作提示。",
        "duration_minutes": 80,
        "capacity": 16,
        "cover_image_url": "/static/official/activities/qingyuan-incense-making.jpg",
    },
    {
        "title": "玉牌挂件制作",
        "description": "从中国玉文化与古代制玉技艺讲起，课程将带领观众体验“如切如磋，如琢如磨”的工艺意趣，在天然玉石挂件上完成属于自己的创作。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "10 岁以上观众",
        "materials": "玉牌坯件、打磨与装饰工具由现场统一提供。",
        "preparation_note": "需按指导分步完成打磨与装饰，低龄参与者建议由家长陪同。",
        "duration_minutes": 90,
        "capacity": 18,
        "cover_image_url": "/static/official/activities/jade-carving-pendant.jpg",
    },
    {
        "title": "仿点翠制作",
        "description": "课程将介绍点翠工艺的历史渊源、制作流程与当代环保替代材料的应用，参与者可体验拓稿、剪羽、胶合等步骤，完成一件仿点翠作品。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "青少年与成人",
        "materials": "仿点翠材料、底托、裁剪与粘贴工具由现场统一提供。",
        "preparation_note": "制作环节较细致，建议预留完整课程时间完成作品。",
        "duration_minutes": 100,
        "capacity": 14,
        "cover_image_url": "/static/official/activities/kingfisher-feather-inlay.jpg",
    },
    {
        "title": "凤翔泥塑彩绘",
        "description": "课程聚焦凤翔泥塑的造型传统、色彩语言与吉祥寓意，参与者将学习泥塑工艺流程，并体验彩绘、上光等步骤，完成生动有趣的泥塑作品。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "亲子家庭与公众观众",
        "materials": "泥塑坯体、彩绘颜料、上光辅具由现场统一提供。",
        "preparation_note": "彩绘阶段请注意衣物防护，作品完成后需按要求放置晾干。",
        "duration_minutes": 75,
        "capacity": 24,
        "cover_image_url": "/static/official/activities/fengxiang-clay-sculpture.jpg",
    },
    {
        "title": "敦煌石粉彩绘",
        "description": "以敦煌壁画的历史、题材与色彩体系为切入点，课程将教授线描、调色与敷色的基础步骤，参与者可在泥板上临摹一幅丝路壁画作品。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "12 岁以上观众",
        "materials": "石粉颜料、泥板、毛笔与调色工具由现场统一提供。",
        "preparation_note": "课程涉及颜料调配，建议按老师节奏分层上色，避免画面混色。",
        "duration_minutes": 100,
        "capacity": 16,
        "cover_image_url": "/static/official/activities/dunhuang-pigment-painting.jpg",
    },
    {
        "title": "龙泉青瓷拉坯体验",
        "description": "课程将介绍龙泉青瓷的发展历史与烧制技艺，并带领参与者体验揉泥、找中心、开孔等拉坯基础手法，在触摸泥土的过程中感受青瓷工艺之美。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "青少年与成人",
        "materials": "陶泥、拉坯工具与基础围裙由现场统一提供。",
        "preparation_note": "拉坯过程对手部稳定性有一定要求，建议听完示范后再开始操作。",
        "duration_minutes": 90,
        "capacity": 16,
        "cover_image_url": "/static/official/activities/longquan-celadon.jpg",
    },
    {
        "title": "扬州漆器螺钿镶嵌",
        "description": "以扬州漆器髹饰技艺中的螺钿工艺为核心，课程将带领观众了解其历史脉络和装饰语言，并通过镶嵌、打磨、抛光等步骤完成一件螺钿作品。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "青少年与成人",
        "materials": "螺钿薄片、底板、打磨与抛光材料由现场统一提供。",
        "preparation_note": "请按顺序完成镶嵌与打磨，避免在未固定前移动作品。",
        "duration_minutes": 100,
        "capacity": 14,
        "cover_image_url": "/static/official/activities/yangzhou-lacquer-inlay.jpg",
    },
    {
        "title": "扬州漆艺打磨抛光",
        "description": "课程将从扬州漆艺的历史与工艺品类出发，带领参与者体验漆器由粗到细的打磨与抛光过程，感受漆艺器物表面质感的变化与传统审美。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "青少年与成人",
        "materials": "漆器坯体、砂纸、抛光辅具由现场统一提供。",
        "preparation_note": "打磨过程需耐心完成多个层次，建议全程佩戴现场提供的防护用品。",
        "duration_minutes": 90,
        "capacity": 16,
        "cover_image_url": "/static/official/activities/lacquer-polishing.jpg",
    },
    {
        "title": "朱仙镇木版年画",
        "description": "围绕朱仙镇木版年画的艺术风格、传统用色与年俗寓意展开，课程将带领观众体验刷墨、覆纸、印制等流程，制作年历或冰箱贴等作品。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "亲子家庭与学生团体",
        "materials": "版画底板、颜料、滚筒、纸张由现场统一提供。",
        "preparation_note": "印制环节需要按步骤排队完成，请注意保持画面与工具整洁。",
        "duration_minutes": 85,
        "capacity": 22,
        "cover_image_url": "/static/official/activities/zhuxianzhen-woodblock-print.jpg",
    },
    {
        "title": "蔚县剪纸窗花",
        "description": "课程将介绍蔚县剪纸的历史文化、刀刻特色与色彩风格，参与者可在老师指导下练习刻画线条与点染技巧，完成一件具有民间艺术气息的窗花作品。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "10 岁以上观众",
        "materials": "彩纸、刻刀、底板与点染辅材由现场统一提供。",
        "preparation_note": "课程涉及刻刀使用，请严格按照安全提示操作。",
        "duration_minutes": 75,
        "capacity": 18,
        "cover_image_url": "/static/official/activities/yuxian-paper-cut.jpg",
    },
    {
        "title": "北京灯彩制作",
        "description": "从北京灯彩的历史流变、分类与制作手段讲起，课程将带领观众完成裁剪、拼接、粘贴与装饰等步骤，感受传统灯彩的节庆氛围与造型趣味。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "亲子家庭与公众观众",
        "materials": "灯彩骨架、彩纸、装饰材料由现场统一提供。",
        "preparation_note": "建议亲子观众共同完成组装步骤，便于更好地控制结构稳定性。",
        "duration_minutes": 75,
        "capacity": 20,
        "cover_image_url": "/static/official/activities/beijing-lantern.jpg",
    },
    {
        "title": "纸笺团扇制作",
        "description": "课程将介绍纸笺加工技艺的发展脉络与代表性纸笺品类，参与者可体验水上点划与团扇轻覆的制作方式，完成一把独一无二的团扇作品。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "青少年与成人",
        "materials": "团扇、纸笺染料与水拓工具由现场统一提供。",
        "preparation_note": "制作时请按指导控制水面纹理，避免过度搅动影响图案效果。",
        "duration_minutes": 70,
        "capacity": 18,
        "cover_image_url": "/static/official/activities/decorated-paper-fan.jpg",
    },
    {
        "title": "中式盘扣制作",
        "description": "围绕中式服装盘扣的历史、经典样式与制作逻辑展开，课程将带领参与者体验盘绕、固定与整形等步骤，感受传统服饰工艺的精巧结构。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "青少年与成人",
        "materials": "盘扣绳、布面辅材与定型工具由现场统一提供。",
        "preparation_note": "盘绕工序较细致，建议跟随老师节奏逐步完成基础结型。",
        "duration_minutes": 85,
        "capacity": 18,
        "cover_image_url": "/static/official/activities/chinese-knot-button.jpg",
    },
    {
        "title": "绒花制作体验",
        "description": "课程将介绍绒花的历史流变与基础造型技法，参与者可在老师讲解下完成一枚精美绒花作品，体验传统绒花从材料到成形的制作魅力。",
        "location": "非遗手工艺体验中心",
        "category": "非遗体验",
        "target_audience": "青少年与成人",
        "materials": "绒条、金属丝、花托与装配工具由现场统一提供。",
        "preparation_note": "细节塑形较多，建议预留完整课程时间并耐心完成收尾。",
        "duration_minutes": 100,
        "capacity": 14,
        "cover_image_url": "/static/official/activities/ronghua-flower.jpg",
    },
    {
        "title": "常设展公益讲解",
        "description": "面向初次到馆观众的常设展公益讲解活动，围绕馆藏门类、代表工艺与重点展柜展开，帮助观众快速建立参观主线与内容理解框架。",
        "location": "一层序厅集合",
        "category": "讲解活动",
        "target_audience": "公众观众",
        "materials": "无需自备材料，建议提前 10 分钟到达集合点。",
        "preparation_note": "讲解期间请跟随志愿者统一动线参观，避免掉队影响节奏。",
        "duration_minutes": 60,
        "capacity": 30,
        "cover_image_url": "/static/official/exhibitions/prosperity-nourished-by-chinese-culture-basic-exhibition-of-chinese-arts-and-crafts.jpg",
    },
    {
        "title": "青瓷与玉雕专题导赏",
        "description": "聚焦青瓷与玉雕两大工艺门类的专题讲解活动，结合代表器物讲解材料特征、造型语言与审美脉络，适合希望深看重点展品的观众。",
        "location": "常设陈列区服务台",
        "category": "讲解活动",
        "target_audience": "青少年与成人",
        "materials": "无需自备材料，可自带笔记本记录重点内容。",
        "preparation_note": "专题导赏节奏较紧凑，建议提前入场并全程跟随讲解。",
        "duration_minutes": 50,
        "capacity": 24,
        "cover_image_url": "/static/official/collections/guan-er-ping.jpg",
    },
    {
        "title": "非遗技艺亲子导览",
        "description": "面向亲子家庭的轻量化讲解活动，通过器物观察、互动提问与路线串联，带孩子理解非遗技艺背后的生活场景与文化趣味。",
        "location": "四层专题展厅入口",
        "category": "讲解活动",
        "target_audience": "亲子家庭",
        "materials": "无需自备材料，建议家长陪同完成全程导览。",
        "preparation_note": "活动中包含互动问答，请家长协助儿童保持队列与观展秩序。",
        "duration_minutes": 45,
        "capacity": 20,
        "cover_image_url": "/static/official/exhibitions/splendid-diversity-practices-in-chinese-ich-protection.jpg",
    },
    {
        "title": "馆藏精品志愿者讲解",
        "description": "由志愿者围绕馆内精品器物开展定时讲解，重点介绍作品工艺、纹样寓意与时代背景，适合希望在较短时间内抓住亮点的观众。",
        "location": "精品展柜区集合点",
        "category": "讲解活动",
        "target_audience": "公众观众",
        "materials": "无需自备材料，讲解结束后可自行延伸参观。",
        "preparation_note": "请提前到达集合点签到，迟到可能无法加入当场讲解队伍。",
        "duration_minutes": 40,
        "capacity": 18,
        "cover_image_url": "/static/official/collections/ru-yi-jian.jpg",
    },
]


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

        ActivityVolunteer.objects.filter(volunteer=volunteer).delete()
        volunteer_plan = [
            ("常设展公益讲解", ActivityVolunteer.STATUS_APPROVED),
            ("青瓷与玉雕专题导赏", ActivityVolunteer.STATUS_APPROVED),
            ("非遗技艺亲子导览", ActivityVolunteer.STATUS_PENDING),
            ("馆藏精品志愿者讲解", ActivityVolunteer.STATUS_PENDING),
        ]
        activity_map = {activity.title: activity for activity in activities}
        for title, status in volunteer_plan:
            activity = activity_map.get(title)
            if not activity:
                continue
            ActivityVolunteer.objects.create(activity=activity, volunteer=volunteer, status=status)

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
        today = timezone.localdate()
        open_time_slots = ["09:00-11:00", "11:00-13:00", "13:00-15:00", "15:00-17:00"]
        desired_keys = set()

        for day in range(14):
            visit_date = today + timedelta(days=day)
            if visit_date.weekday() == 0:
                continue
            for time_slot in open_time_slots:
                desired_keys.add((visit_date, time_slot))
                VisitSlot.objects.update_or_create(
                    visit_date=visit_date,
                    time_slot=time_slot,
                    defaults={"capacity": 60, "status": VisitSlot.STATUS_OPEN},
                )

        removable = VisitSlot.objects.filter(visit_date__gte=today)
        for slot in removable:
            if (slot.visit_date, slot.time_slot) not in desired_keys:
                if slot.booked_count > 0:
                    slot.status = VisitSlot.STATUS_CLOSED
                    slot.save(update_fields=["status"])
                else:
                    slot.delete()

    def seed_activities(self, rows):
        created = []
        base_time = timezone.now() + timedelta(days=3)
        desired_titles = {row["title"] for row in ACTIVITY_ROWS}
        MuseumActivity.objects.exclude(title__in=desired_titles).delete()

        for offset, row in enumerate(ACTIVITY_ROWS):
            item, _ = MuseumActivity.objects.update_or_create(
                title=row["title"],
                defaults={
                    "description": row["description"],
                    "activity_time": base_time + timedelta(days=offset * 2),
                    "location": row["location"],
                    "category": row["category"],
                    "target_audience": row["target_audience"],
                    "materials": row["materials"],
                    "preparation_note": row["preparation_note"],
                    "duration_minutes": row["duration_minutes"],
                    "capacity": row["capacity"],
                    "status": MuseumActivity.STATUS_PUBLISHED,
                    "cover_image_url": row["cover_image_url"],
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
