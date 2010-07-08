from django.contrib import admin
from chronicles.models import Chronicle

class ChronicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'creator', 'created')

admin.site.register(Chronicle, ChronicleAdmin)
