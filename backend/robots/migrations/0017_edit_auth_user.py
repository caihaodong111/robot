from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("robots", "0016_robot_reference_dict"),
    ]

    operations = [
        migrations.CreateModel(
            name="EditAuthUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=64, unique=True, verbose_name="用户名")),
                ("password_hash", models.CharField(max_length=128, verbose_name="密码哈希")),
                ("is_active", models.BooleanField(default=True, verbose_name="是否启用")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("last_login_at", models.DateTimeField(blank=True, null=True, verbose_name="最后登录时间")),
            ],
            options={
                "verbose_name": "编辑认证用户",
                "verbose_name_plural": "编辑认证用户",
                "db_table": "edit_auth_users",
                "ordering": ["-created_at"],
            },
        ),
    ]
