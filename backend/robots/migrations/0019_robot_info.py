from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("robots", "0018_edit_session_version"),
    ]

    operations = [
        migrations.CreateModel(
            name="RobotInfo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("robot", models.CharField(db_index=True, max_length=64, verbose_name="机器人")),
                ("shop", models.CharField(blank=True, max_length=64, null=True, verbose_name="车间")),
                ("reference", models.CharField(blank=True, max_length=128, null=True, verbose_name="参考编号")),
                ("number", models.FloatField(blank=True, null=True, verbose_name="编号")),
                ("type", models.CharField(blank=True, max_length=128, null=True, verbose_name="类型")),
                ("tech", models.CharField(blank=True, max_length=128, null=True, verbose_name="工艺")),
                ("mark", models.IntegerField(default=0, verbose_name="标记")),
                ("remark", models.TextField(blank=True, default="", verbose_name="备注")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "机器人基本信息",
                "verbose_name_plural": "机器人基本信息",
                "db_table": "robot_info",
                "ordering": ["robot"],
            },
        ),
        migrations.AddIndex(
            model_name="robotinfo",
            index=models.Index(fields=["robot"], name="robots_robot_idx"),
        ),
        migrations.AddIndex(
            model_name="robotinfo",
            index=models.Index(fields=["shop"], name="robots_shop_idx"),
        ),
        migrations.AddIndex(
            model_name="robotinfo",
            index=models.Index(fields=["reference"], name="robots_refere_idx"),
        ),
        migrations.AddIndex(
            model_name="robotinfo",
            index=models.Index(fields=["robot", "reference"], name="robots_robot_2f0c8b_idx"),
        ),
    ]
