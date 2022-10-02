from django.contrib import admin
from friendships.models import Friendship

# Register your models here.
@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    data_hierachy = 'created_at'
    list_display = (
        'created_at',
        'id',
        'from_user',
        'to_user',
    )
from django.contrib import admin

# Register your models here.
