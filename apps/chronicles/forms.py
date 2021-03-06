from django import forms
from django.utils.translation import ugettext_lazy as _

from chronicles.models import Chronicle, ChronicleMember

# @@@ we should have auto slugs, even if suggested and overrideable

class ChronicleForm(forms.ModelForm):
    
    slug = forms.SlugField(max_length=20,
        help_text = _("a short version of the name consisting only of letters, numbers, underscores and hyphens."),
        error_messages = {'invalid': _("This value must contain only letters, numbers, underscores and hyphens.")})
            
    def clean_slug(self):
        if Chronicle.objects.filter(slug__iexact=self.cleaned_data["slug"]).count() > 0:
            raise forms.ValidationError(_("A chronicle already exists with that slug."))
        return self.cleaned_data["slug"].lower()
    
    def clean_name(self):
        if Chronicle.objects.filter(name__iexact=self.cleaned_data["name"]).count() > 0:
            raise forms.ValidationError(_("A chronicle already exists with that name."))
        return self.cleaned_data["name"]
    
    class Meta:
        model = Chronicle
        fields = ('name', 'slug', 'description')


# @@@ is this the right approach, to have two forms where creation and update fields differ?

class ChronicleUpdateForm(forms.ModelForm):
    
    def clean_name(self):
        if Chronicle.objects.filter(name__iexact=self.cleaned_data["name"]).count() > 0:
            if self.cleaned_data["name"] == self.instance.name:
                pass # same instance
            else:
                raise forms.ValidationError(_("A chronicle already exists with that name."))
        return self.cleaned_data["name"]
    
    class Meta:
        model = Chronicle
        fields = ('name', 'description')

class ChronicleMemberForm(forms.ModelForm):
    class Meta:
        model = ChronicleMember
        fields = ('membership_role', 'membership_role_other')
