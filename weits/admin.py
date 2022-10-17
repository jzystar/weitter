from django.contrib import admin
from weits.models import Weit

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
