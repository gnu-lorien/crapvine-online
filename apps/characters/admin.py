from characters.models import Sheet, Expendable, Trait, TraitListProperty, TraitListName, VampireSheet, ExperienceEntry, Menu, MenuItem
from django.contrib import admin
from reversion.admin import VersionAdmin

class SheetAdmin(VersionAdmin):
    pass
class ExpendableAdmin(VersionAdmin):
    pass
class TraitAdmin(VersionAdmin):
    pass
class TraitListPropertyAdmin(VersionAdmin):
    pass
class TraitListNameAdmin(VersionAdmin):
    pass
class VampireSheetAdmin(VersionAdmin):
    pass
class ExperienceEntryAdmin(VersionAdmin):
    pass

admin.site.register(Sheet, SheetAdmin)
admin.site.register(Expendable, ExpendableAdmin)
admin.site.register(Trait, TraitAdmin)
admin.site.register(TraitListProperty, TraitListPropertyAdmin)
admin.site.register(TraitListName, TraitListNameAdmin)
admin.site.register(VampireSheet, VampireSheetAdmin)
admin.site.register(ExperienceEntry, ExperienceEntryAdmin)

admin.site.register(Menu)
admin.site.register(MenuItem)
