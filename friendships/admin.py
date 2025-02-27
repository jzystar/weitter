from django.contrib import admin
from friendships.models import Friendship


# Register your models here.
@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    date_hierachy = 'created_at'
    list_display = (
        'id',
        'from_user',
        'to_user',
        'created_at',
    )

