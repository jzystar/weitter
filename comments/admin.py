from django.contrib import admin
from comments.models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    data_hierachy = 'created_at'
    list_display = (
        'id',
        'user',
        'weit',
        'content',
        'created_at',
        'updated_at',
    )
