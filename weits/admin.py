from django.contrib import admin
from weits.models import Weit, WeitPhoto

# Register your models here.
@admin.register(Weit)
class WeitAdmin(admin.ModelAdmin):
    date_hierachy = 'created_at'
    list_display = (
        'id',
        'user',
        'content',
        'created_at',
    )

@admin.register(WeitPhoto)
class WeitPhotoAdmin(admin.ModelAdmin):
    date_hierachy = 'created_at'
    list_display = (
        'weit',
        'user',
        'file',
        'status',
        'has_deleted',
        'created_at',
    )

    list_filer = ('status', 'has_deleted')



