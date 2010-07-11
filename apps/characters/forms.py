from datetime import datetime
from django import forms
from django.utils.translation import ugettext_lazy as _

from characters.models import Sheet, VampireSheet, TraitList, Trait, DISPLAY_PREFERENCES

class SheetUploadForm(forms.Form):
    title = forms.CharField(max_length=128)
    file = forms.FileField()

class VampireSheetAttributesForm(forms.ModelForm):
    class Meta:
        model = VampireSheet
        exclude = ("last_modified", "experience_unspent", "experience_earned", "object_id", "content_type", "traits", "experience_entries")

class TraitListForm(forms.ModelForm):
    class Meta:
        model = TraitList

class TraitListDisplayForm(forms.Form):
    display = forms.ChoiceField(choices=DISPLAY_PREFERENCES)

class TraitForm(forms.ModelForm):
    class Meta:
        model = Trait

class DisplayOrderForm(forms.Form):
    order = forms.IntegerField(min_value=0)
    traitlist_id = forms.IntegerField(widget=forms.widgets.HiddenInput)
    trait = forms.CharField(max_length=128)
