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

        Exhibition.objects.filter(title__in=["大国匠作：中国工艺美术精品展", "丝路纹样与非遗新生"]).delete()
        MuseumActivity.objects.filter(title__in=["周末公益讲解：走近传统工艺", "亲子手作体验：纹样拓印"]).delete()
        GuideInfo.objects.filter(hall_name__in=["一层精品展厅", "二层专题展厅"]).delete()

        ex1, _ = Exhibition.objects.update_or_create(
            title="岩骨正气 和合致远 ——“三茶”统筹的南平实践",
            defaults={
                "description": "参考馆方专题展信息设置，围绕南平地区茶文化、生态实践与工艺表达，呈现传统技艺和地方文化之间的互文关系。",
                "start_date": timezone.datetime(2026, 5, 21).date(),
                "end_date": timezone.datetime(2026, 7, 21).date(),
                "location": "四层 3、4 展厅",
                "status": Exhibition.STATUS_PUBLISHED,
                "cover_image_url": "https://www.gmfyg.org.cn/Attachments/Image/20260525/5d0ba517-f235-4f0c-9a6c-f1bc885648d6.PNG",
            },
        )
        ex2, _ = Exhibition.objects.update_or_create(
            title="高原丝路 瞿昙之光——青海丝路文物与瞿昙寺壁画艺术展",
            defaults={
                "description": "参考馆方专题展信息设置，以青海丝路文物和瞿昙寺壁画艺术为线索，展示高原丝路上的文化交流与图像传统。",
                "start_date": timezone.datetime(2026, 4, 21).date(),
                "end_date": timezone.datetime(2026, 8, 31).date(),
                "location": "一层 1、2 展厅",
                "status": Exhibition.STATUS_PUBLISHED,
                "cover_image_url": "https://www.gmfyg.org.cn/Attachments/Image/20260424/54f85452-bd5b-43d8-aded-80404478487f.jpeg",
            },
        )
        ex3, _ = Exhibition.objects.update_or_create(
            title="文脉华滋——中国工艺美术基本陈列",
            defaults={
                "description": "参考馆方基本陈列和专题页面设置，聚焦玉雕、陶瓷、金属、竹木雕、民族民间工艺等门类，呈现工艺美术的材料、技法与审美脉络。",
                "start_date": timezone.datetime(2026, 1, 1).date(),
                "end_date": timezone.datetime(2026, 12, 31).date(),
                "location": "二层、三层常设展厅",
                "status": Exhibition.STATUS_PUBLISHED,
                "cover_image_url": "https://www.gmfyg.org.cn/display/wenmaihuazi/pic/head.jpg",
            },
        )

        CollectionItem.objects.update_or_create(
            exhibition=ex1,
            name="密玉雕刻 敦煌之声·伎乐天",
            defaults={
                "category": "玉雕",
                "dynasty": "当代",
                "description": "以敦煌伎乐天形象为灵感，适合展示玉石材料、圆雕技法和音乐舞姿的视觉转译。",
                "image_url": "https://file.gmfyg.org.cn/collection/WaterMarks/%E5%9B%BE%E7%89%87/2001-2376/2334.jpg",
            },
        )
        CollectionItem.objects.update_or_create(
            exhibition=ex1,
            name="玉雕 三希堂传世宝玺",
            defaults={
                "category": "玉雕",
                "dynasty": "当代",
                "description": "以宝玺形制和传统纹样为核心，体现玉雕在礼制意象、文字篆刻和器物造型上的综合表现。",
                "image_url": "https://file.gmfyg.org.cn/collection/WaterMarks/%E5%9B%BE%E7%89%87/2001-2376/2198.jpg",
            },
        )
        CollectionItem.objects.update_or_create(
            exhibition=ex2,
            name="玛瑙 石窟印象",
            defaults={
                "category": "玉石雕刻",
                "dynasty": "当代",
                "description": "借石窟造像和天然玛瑙色理营造层次，呼应丝路题材中的宗教艺术与石窟图像。",
                "image_url": "https://file.gmfyg.org.cn/collection/WaterMarks/%E5%9B%BE%E7%89%87/2001-2376/2196.jpg",
            },
        )
        CollectionItem.objects.update_or_create(
            exhibition=ex2,
            name="水晶 金刚橛",
            defaults={
                "category": "水晶雕刻",
                "dynasty": "当代",
                "description": "以清透水晶表现宗教法器形制，可用于导览中说明工艺、信仰图像与材料质感的关系。",
                "image_url": "https://file.gmfyg.org.cn/collection/WaterMarks/%E5%9B%BE%E7%89%87/2001-2376/2195.jpg",
            },
        )
        for name, category, image, description in [
            ("昌江玉雕 山海黎乡", "玉雕", "https://file.gmfyg.org.cn/collection/WaterMarks/%E5%9B%BE%E7%89%87/2001-2376/2194.jpg", "以地域文化为题材，适合展示民间生活、地方记忆与玉雕语言的结合。"),
            ("墨玉微雕 春江花月夜", "玉雕", "https://file.gmfyg.org.cn/collection/WaterMarks/%E5%9B%BE%E7%89%87/2001-2376/2192.jpg", "微雕题材细密，适合强调工艺美术中尺度、耐心和文字图像互构的特点。"),
            ("黄龙玉 花仙子", "玉雕", "https://file.gmfyg.org.cn/collection/WaterMarks/%E5%9B%BE%E7%89%87/2001-2376/2190.jpg", "以花卉与人物意象结合，展现当代玉雕对自然题材的温润表达。"),
            ("水晶 太子佛", "水晶雕刻", "https://file.gmfyg.org.cn/collection/WaterMarks/%E5%9B%BE%E7%89%87/2001-2376/2188.jpg", "通过透明材料处理佛像体量和光感，可作为展品文字导览的重点案例。"),
            ("阿拉善玉 文明的碎片", "玉石雕刻", "https://file.gmfyg.org.cn/collection/WaterMarks/%E5%9B%BE%E7%89%87/2001-2376/2187.jpg", "作品题名带有历史想象，适合展示现代工艺美术中的叙事性。"),
        ]:
            CollectionItem.objects.update_or_create(
                exhibition=ex3,
                name=name,
                defaults={
                    "category": category,
                    "dynasty": "当代",
                    "description": description,
                    "image_url": image,
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
            title="公益讲解 | 展厅公益讲解场次安排",
            defaults={
                "description": "参考馆方志愿者活动栏目设置，由志愿讲解员带领观众了解展厅主题、重点藏品和参观动线。",
                "activity_time": timezone.now() + timedelta(days=6, hours=2),
                "location": "一层服务台集合",
                "capacity": 24,
                "status": MuseumActivity.STATUS_PUBLISHED,
                "cover_image_url": "https://www.gmfyg.org.cn/Attachments/Image/20260521/872f6d81-fb78-48a2-bc68-8a25f1372d82.jpeg",
            },
        )
        ActivityVolunteer.objects.get_or_create(activity=activity, volunteer=volunteer)

        MuseumActivity.objects.update_or_create(
            title="社教 | 非遗手工艺体验中心体验课",
            defaults={
                "description": "参考馆方活动栏目中的非遗体验项目，设置竹编、传统制香、泥塑、剪纸、灯彩等体验方向。",
                "activity_time": timezone.now() + timedelta(days=12, hours=2),
                "location": "活动中心",
                "capacity": 18,
                "status": MuseumActivity.STATUS_PUBLISHED,
                "cover_image_url": "https://www.gmfyg.org.cn/Attachments/Image/20241010/4197978c-e44a-42fa-8509-7de47df824d4.jpeg",
            },
        )
        MuseumActivity.objects.update_or_create(
            title="社教活动 | 大型原创情景舞剧《大明瞿昙》片段展演",
            defaults={
                "description": "参考馆方社教活动栏目设置，围绕瞿昙寺壁画艺术与舞台表达，设计展演与导赏结合的活动。",
                "activity_time": timezone.now() + timedelta(days=18, hours=3),
                "location": "多功能厅",
                "capacity": 60,
                "status": MuseumActivity.STATUS_PUBLISHED,
                "cover_image_url": "https://www.gmfyg.org.cn/Attachments/Image/20260421/b6666b7e-3c8d-4186-acdd-9568ee32c757.jpeg",
            },
        )
        MuseumActivity.objects.update_or_create(
            title="研学 | 应时循节学非遗：二十四节气研学",
            defaults={
                "description": "参考馆方研学栏目设置，将节气知识、非遗技艺和展厅观察结合，面向亲子观众开展课堂式体验。",
                "activity_time": timezone.now() + timedelta(days=24, hours=2),
                "location": "教育活动室",
                "capacity": 20,
                "status": MuseumActivity.STATUS_PUBLISHED,
                "cover_image_url": "https://www.gmfyg.org.cn/Attachments/Image/20260508/ba76b591-8b7b-49e4-9431-5d6e47c378ef.jpeg",
            },
        )

        GuideInfo.objects.update_or_create(
            hall_name="四层 3、4 展厅",
            defaults={
                "exhibition": ex1,
                "route_description": "一层服务台 -> 乘梯至四层 -> 茶文化主题区 -> 地方工艺展示区 -> 观众互动区。",
                "text_guide": "建议结合展览标题中的“三茶”线索观察展项：从茶产业、茶文化到茶科技，理解地方实践如何进入展览叙事。",
                "map_image_url": "https://www.gmfyg.org.cn/Attachments/TmpFile/20240628/46e501e6-d7cd-40bb-9f5a-a8752e8bab27.jpg",
            },
        )
        GuideInfo.objects.update_or_create(
            hall_name="一层 1、2 展厅",
            defaults={
                "exhibition": ex2,
                "route_description": "入口序厅 -> 青海丝路文物单元 -> 瞿昙寺壁画艺术单元 -> 文创与教育活动区。",
                "text_guide": "建议先看展览时间轴，再观察壁画图像中的人物、建筑、纹样和色彩如何呈现丝路交流。",
                "map_image_url": "https://www.gmfyg.org.cn/Attachments/TmpFile/20240621/2596c806-c857-409c-bdc6-0de06b7939e5.jpg",
            },
        )
        GuideInfo.objects.update_or_create(
            hall_name="二层、三层常设展厅",
            defaults={
                "exhibition": ex3,
                "route_description": "二层玉雕与金属工艺 -> 三层陶瓷、竹木雕和民族民间工艺 -> 文创出口。",
                "text_guide": "按照材料门类参观，比较玉石、陶瓷、金属、竹木等材料在造型、纹样和工艺流程上的差异。",
                "map_image_url": "https://www.gmfyg.org.cn/Attachments/TmpFile/20240628/8df75eb9-e1ea-4511-8184-95b0f16fc5d3.png",
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
