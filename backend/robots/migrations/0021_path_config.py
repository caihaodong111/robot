from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("robots", "0020_refresh_log_trigger"),
    ]

    operations = [
        migrations.CreateModel(
            name="PathConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=64, unique=True, verbose_name="配置键")),
                ("path", models.TextField(verbose_name="路径")),
                ("description", models.CharField(blank=True, default="", max_length=255, verbose_name="描述")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "路径配置",
                "verbose_name_plural": "路径配置",
                "db_table": "path_configs",
                "ordering": ["key"],
            },
        ),
    ]
