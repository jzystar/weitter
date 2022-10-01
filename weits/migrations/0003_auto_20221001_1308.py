# Generated by Django 3.1.3 on 2022-10-01 13:08

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('weits', '0002_auto_20221001_1129'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='weit',
            options={'ordering': ('user', '-created_at')},
        ),
        migrations.AlterField(
            model_name='weit',
            name='content',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterIndexTogether(
            name='weit',
            index_together={('user', 'created_at')},
        ),
    ]
