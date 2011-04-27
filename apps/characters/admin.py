from characters.models import Sheet, Expendable, Trait, TraitListProperty, TraitListName, VampireSheet, ExperienceEntry, Menu, MenuItem
from django.contrib import admin
from reversion.admin import VersionAdmin
from characters.models import FailedUpload

class SheetAdmin(VersionAdmin):
    list_display = ['name', 'player', 'last_saved', 'npc', 'status']
    list_filter = ['status', 'npc', 'player']
    search_fields = ['name', 'player__username']

class ExpendableAdmin(VersionAdmin):
    pass

class TraitAdmin(VersionAdmin):
    list_display = ['name', 'value', 'note', 'traitlistname', 'sheet', 'sheet_owner']
    list_filter = ['traitlistname']
    search_fields = ['name', 'value', 'note', 'traitlistname__name', 'sheet__name', 'sheet__player__username']

    def sheet_owner(self, trait):
        return trait.sheet.player

class TraitListPropertyAdmin(VersionAdmin):
    list_display = ['name', 'sheet', 'sorted', 'atomic', 'negative', 'display_preference']
    list_filter = ['sorted', 'atomic', 'negative', 'display_preference']
    search_fields = ['name', 'sheet__name']

class TraitListNameAdmin(VersionAdmin):
    pass
class VampireSheetAdmin(VersionAdmin):
    list_display = ['name', 'player', 'last_saved', 'npc', 'status', 'clan', 'sect', 'title', 'path']
    list_filter = ['status', 'npc', 'clan', 'sect', 'title', 'path', 'player']
    search_fields = ['name', 'player__username', 'clan', 'sect', 'title', 'path']

class ExperienceEntryAdmin(VersionAdmin):
    pass

class MenuAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'sorted', 'negative', 'required', 'autonote', 'display_preference']
    list_filter = ['category', 'sorted', 'negative', 'required', 'autonote', 'display_preference']
    search_fields = ['name', 'category']

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'disp_parent', 'cost', 'note', 'order', 'item_type', 'disp_menu_to_import']

    def disp_parent(self, mi):
        return mi.parent.name

    def disp_menu_to_import(self, mi):
        return mi.menu_to_import.name

class FailedUploadAdmin(admin.ModelAdmin):
    list_display = ['file', 'time', 'player']

admin.site.register(Sheet, SheetAdmin)
admin.site.register(Expendable, ExpendableAdmin)
admin.site.register(Trait, TraitAdmin)
admin.site.register(TraitListProperty, TraitListPropertyAdmin)
admin.site.register(TraitListName, TraitListNameAdmin)
admin.site.register(VampireSheet, VampireSheetAdmin)
admin.site.register(ExperienceEntry, ExperienceEntryAdmin)

admin.site.register(Menu, MenuAdmin)
admin.site.register(MenuItem, MenuItemAdmin)

admin.site.register(FailedUpload, FailedUploadAdmin)
