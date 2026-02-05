from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("robots", "0015_add_refresh_log"),
    ]

    operations = [
        migrations.CreateModel(
            name="RobotReferenceDict",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("robot", models.CharField(db_index=True, max_length=64, verbose_name="robot")),
                ("reference", models.CharField(db_index=True, max_length=128, verbose_name="reference")),
                ("number", models.FloatField(blank=True, null=True, verbose_name="number")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "机器人参考字典",
                "verbose_name_plural": "机器人参考字典",
                "db_table": "robot_reference_dict",
                "unique_together": {("robot", "reference")},
            },
        ),
        migrations.AddIndex(
            model_name="robotreferencedict",
            index=models.Index(fields=["robot", "reference"], name="robot_refer_robot_5f3816_idx"),
        ),
    ]
