from datetime import datetime
from django import forms
from django.utils.translation import ugettext_lazy as _

from characters.models import Sheet

class SheetUploadForm(forms.Form):
    title = forms.CharField(max_length=128)
    file = forms.FileField()
