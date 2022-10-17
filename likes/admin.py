from django.contrib import admin
from likes.models import Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    date_hierachy = 'created_at'
    list_display = (
        'user',
        'content_type',
        'object_id',
        'created_at',
    )
    list_filter = ('content_type', )