from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("robots", "0021_path_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="robotcomponent",
            name="source_key",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=64,
                null=True,
                verbose_name="source_key",
            ),
        ),
        migrations.AddField(
            model_name="robotcomponent",
            name="source_path",
            field=models.TextField(blank=True, null=True, verbose_name="source_path"),
        ),
        migrations.AddField(
            model_name="robothighrisksnapshot",
            name="source_key",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=64,
                null=True,
                verbose_name="source_key",
            ),
        ),
        migrations.AddField(
            model_name="robothighrisksnapshot",
            name="source_path",
            field=models.TextField(blank=True, null=True, verbose_name="source_path"),
        ),
    ]
