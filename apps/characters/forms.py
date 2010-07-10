from datetime import datetime
from django import forms
from django.utils.translation import ugettext_lazy as _

from characters.models import Sheet, VampireSheet, TraitList, Trait

class SheetUploadForm(forms.Form):
    title = forms.CharField(max_length=128)
    file = forms.FileField()

class VampireSheetAttributesForm(forms.ModelForm):
    class Meta:
        model = VampireSheet
        fields=("nature", "demeanor", "blood", "clan", "conscience", "courage", "generation", "path", "pathtraits", "physicalmax", "sect", "selfcontrol", "willpower", "title", "aura", "coterie", "sire")

class VampireSheetTraitListForm(forms.ModelForm):
    class Meta:
        model = TraitList

class TraitForm(forms.ModelForm):
    class Meta:
        model = Trait
