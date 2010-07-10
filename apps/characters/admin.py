from characters.models import Sheet, Expendable, Trait, TraitList, TraitListName, VampireSheet, ExperienceEntry
from django.contrib import admin
from reversion.admin import VersionAdmin

class SheetAdmin(VersionAdmin):
    pass
class ExpendableAdmin(VersionAdmin):
    pass
class TraitAdmin(VersionAdmin):
    pass
class TraitListAdmin(VersionAdmin):
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
admin.site.register(TraitList, TraitListAdmin)
admin.site.register(TraitListName, TraitListNameAdmin)
admin.site.register(VampireSheet, VampireSheetAdmin)
admin.site.register(ExperienceEntry, ExperienceEntryAdmin)
