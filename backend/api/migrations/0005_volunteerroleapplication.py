from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_add_volunteer_application_status"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VolunteerRoleApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("service_area", models.CharField(blank=True, max_length=120)),
                ("motivation", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("pending", "待审批"), ("approved", "已通过"), ("rejected", "已拒绝")], default="pending", max_length=20)),
                ("applied_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="volunteer_role_application", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
