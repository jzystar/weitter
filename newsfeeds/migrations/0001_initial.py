# Generated by Django 3.1.3 on 2022-10-03 03:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('weits', '0003_auto_20221001_1308'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsFeed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('weit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='weits.weit')),
            ],
            options={
                'ordering': ('-created_at',),
                'unique_together': {('user', 'weit')},
                'index_together': {('user', 'created_at')},
            },
        ),
    ]
