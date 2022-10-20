# Generated by Django 3.1.3 on 2022-10-20 13:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('weits', '0003_auto_20221001_1308'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeitPhoto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
                ('order', models.IntegerField(default=0)),
                ('status', models.IntegerField(choices=[(0, 'Pending'), (1, 'Approved'), (2, 'Rejected')], default=0)),
                ('has_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('weit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='weits.weit')),
            ],
            options={
                'index_together': {('status', 'created_at'), ('user', 'created_at'), ('has_deleted', 'created_at'), ('weit', 'order')},
            },
        ),
    ]
