from datetime import datetime
from django import forms
from django.utils.translation import ugettext_lazy as _

from characters.models import Sheet, VampireSheet, TraitListProperty, Trait, DISPLAY_PREFERENCES, ExperienceEntry

class SheetUploadForm(forms.Form):
    file = forms.FileField()

class VampireSheetAttributesForm(forms.ModelForm):
    class Meta:
        model = VampireSheet
        exclude = ("last_modified", "experience_unspent", "experience_earned", "object_id", "content_type", "traits", "experience_entries", "uploading", "slug", "player", "name")

class TraitListPropertyForm(forms.ModelForm):
    class Meta:
        model = TraitListProperty

class TraitListPropertyForm(forms.ModelForm):
    class Meta:
        model = TraitListProperty
        exclude = ("sheet", "name")

class TraitForm(forms.ModelForm):
    class Meta:
        model = Trait
        exclude = ("order", "sheet", "traitlistname")

class DisplayOrderForm(forms.Form):
    order = forms.IntegerField(min_value=0)
    trait_id = forms.IntegerField(widget=forms.widgets.HiddenInput)
    trait = forms.CharField(max_length=128)

class ExperienceEntryForm(forms.ModelForm):
    class Meta:
        model = ExperienceEntry
        exclude = ("earned", "unspent")

class NewSheetForm(forms.Form):
    name = forms.CharField()
    creature_type = forms.ChoiceField(choices=[("vampire","Vampire")])
