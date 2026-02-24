from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("robots", "0019_robot_info"),
    ]

    operations = [
        migrations.AddField(
            model_name="refreshlog",
            name="trigger",
            field=models.CharField(
                choices=[("manual", "手动更新"), ("scheduled", "定时更新")],
                default="manual",
                max_length=16,
                verbose_name="触发方式",
            ),
        ),
        migrations.AddIndex(
            model_name="refreshlog",
            index=models.Index(fields=["trigger"], name="refresh_logs_trigger_idx"),
        ),
    ]
