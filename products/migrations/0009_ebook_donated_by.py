# Generated by Django 4.2.19 on 2025-04-11 16:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        (
            "products",
            "0008_alter_cartitem_unique_together_cartitem_accessories_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="ebook",
            name="donated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
