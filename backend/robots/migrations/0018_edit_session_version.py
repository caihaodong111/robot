from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("robots", "0017_edit_auth_user"),
    ]

    operations = [
        migrations.CreateModel(
            name="EditSessionVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.BigIntegerField(default=1, verbose_name="版本号")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("updated_by", models.CharField(blank=True, default="", max_length=64, verbose_name="更新来源")),
            ],
            options={
                "verbose_name": "编辑会话版本",
                "verbose_name_plural": "编辑会话版本",
                "db_table": "edit_session_version",
            },
        ),
    ]
