from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, get_host
from django.template import RequestContext
from django.db.models import Q
from django.http import Http404
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from authority.views import permission_denied
from characters.permissions import SheetPermission

from characters.forms import SheetUploadForm, VampireSheetAttributesForm, VampireSheetTraitListForm
from django.forms.models import modelformset_factory
from characters.models import Sheet, VampireSheet, TraitListName, Trait

from xml_uploader import handle_sheet_upload, VampireExporter

@login_required
def upload_sheet(request, group_slug=None, bridge=None):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if request.method == 'POST':
        form = SheetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            cl = handle_sheet_upload(request.FILES['file'], request.user)
            sheet_permission = SheetPermission(request.user)
            for name, vs in cl.vampires.iteritems():
                s = Sheet.objects.get(id=vs.id)
                sheet_permission.assign(check=('fullview_sheet'), content_object=s)
            if group:
                for name, vs in cl.vampires.iteritems():
                    group.associate(vs)
                    vs.save()
                redirect_to = bridge.reverse('sheets_list', group)
            else:
                redirect_to = reverse('sheets_list')
            return HttpResponseRedirect(redirect_to)
    else:
        form = SheetUploadForm()
    return render_to_response(
        'characters/upload_sheet.html',
        {'form':form, 'group':group},
        context_instance=RequestContext(request))

@login_required
def list_sheets(request, group_slug=None, bridge=None):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheets = group.get_sheets_for_user(request.user)
    else:
        sheets = Sheet.objects.all()
    sheets = sheets.filter(player__exact=request.user)

    return render_to_response(
        'characters/list_sheets.html',
        {'sheets':sheets, 'group':group},
        context_instance=RequestContext(request))

@login_required
def list_sheet(request, sheet_id, group_slug=None, bridge=None):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    sheet = get_object_or_404(Sheet, id=sheet_id)
    check = SheetPermission(request.user)
    if not check.has_perm('sheet_permission.fullview_sheet', sheet, approved=True):
        return permission_denied(request)

    ee = sheet.experience_entries.all().order_by('date')
    return render_to_response(
        'characters/list_sheet.html',
        {'sheet':sheet,
         'group':group,
         'experience_entries':ee},
        context_instance=RequestContext(request))

@login_required
def download_sheet(request, sheet_id):
    sheet = VampireSheet.objects.get(id=sheet_id, player=request.user)
    response = HttpResponse(mimetype="application/gex")
    response['Content-Disposition'] = 'attachment; filename=Exchange.gex'
    ve = VampireExporter(sheet)
    response.write(ve)
    return response

@login_required
def edit_vampire_sheet_attributes(request, sheet_id,
                                  form_closs=VampireSheetAttributesForm, **kwargs):
    template_name = kwargs.get("template_name", "characters/vampires/edit_vampire_sheet_attributes.html")

    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/vampires/edit_vampire_sheet_attributes_facebox.html",
        )

    vampire_sheet = VampireSheet.objects.get(id=sheet_id)
    form = VampireSheetAttributesForm(request.POST or None, instance=vampire_sheet)
    if form.is_valid() and request.method == "POST":
        form.save()
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_id]))

    return render_to_response(template_name, {
        'sheet': vampire_sheet,
        'form': form,
    }, context_instance=RequestContext(request))

@login_required
def edit_vampire_sheet_traitlist(request, sheet_id, traitlistname_slug,
                                  form_closs=VampireSheetTraitListForm, **kwargs):
    template_name = kwargs.get("template_name", "characters/vampires/edit_vampire_sheet_traitlist.html")

    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/vampires/edit_vampire_sheet_traitlist_facebox.html",
        )

    vampire_sheet = get_object_or_404(VampireSheet, id=sheet_id)
    tln = get_object_or_404(TraitListName, slug=traitlistname_slug)
    tl = vampire_sheet.get_traitlist(tln.name)
    TraitFormSet = modelformset_factory(Trait, extra=0, exclude=('approved'))
    if request.method == "POST":
        formset = TraitFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(reverse("sheet_list", args=[sheet_id]))
    else:
        formset = TraitFormSet(queryset=tl)

    return render_to_response(template_name, {
        'sheet': vampire_sheet,
        'traitlistname': tln,
        'traitlist': tl,
        'formset': formset,
    }, context_instance=RequestContext(request))
