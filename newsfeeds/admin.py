from django.contrib import admin
from newsfeeds.models import NewsFeed

# Register your models here.
@admin.register(NewsFeed)
class NewsFeedAdmin(admin.ModelAdmin):
    date_hierachy = 'created_at'
    list_display = (
        'user',
        'weit',
        'created_at',
    )
