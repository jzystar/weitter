from django.contrib import admin
from weits.models import Weit

# Register your models here.
@admin.register(Weit)
class Weitdmin(admin.ModelAdmin):
    data_hierachy = 'created_at'
    list_display = (
        'created_at',
        'user',
        'content',
    )
