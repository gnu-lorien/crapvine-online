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

from characters.forms import SheetUploadForm, VampireSheetAttributesForm, TraitForm, TraitListDisplayForm, DisplayOrderForm
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from characters.models import Sheet, VampireSheet, TraitListName, Trait, TraitList

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
                                  form_class=VampireSheetAttributesForm, **kwargs):
    template_name = kwargs.get("template_name", "characters/vampires/edit_vampire_sheet_attributes.html")

    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/vampires/edit_vampire_sheet_attributes_facebox.html",
        )

    vampire_sheet = VampireSheet.objects.get(id=sheet_id)
    form = form_class(request.POST or None, instance=vampire_sheet)
    if form.is_valid() and request.method == "POST":
        form.save()
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_id]))

    return render_to_response(template_name, {
        'sheet': vampire_sheet,
        'form': form,
    }, context_instance=RequestContext(request))

def can_edit_sheet(request, sheet):
    if request.user == sheet.player:
        return True

    chronicle_sheets = Chronicle.content_objects(Sheet)
    try:
        chronicle_sheets.get(id=sheet.id)
        cm = ChronicleMember.objects.get(user=request.user)
        if 0 == cm.membership_role:
            return True
    except Chronicle.DoesNotExist:
        pass

    check = SheetPermission(request.user)
    if check.has_perm('sheet_permission.change_sheet', sheet, approved=True):
        return True

    return False

def can_delete_sheet(request, sheet):
    return can_edit_sheet(request, sheet)

@login_required
def reorder_traitlist(request, sheet_id, traitlistname_slug,
                      group_slug=None, bridge=None,
                      form_class=TraitListDisplayForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), id=sheet_id)
    else:
        sheet = get_object_or_404(Sheet, id=sheet_id)

    # Check all of the various sheet editing permissions
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)
    template_name = kwargs.get("template_name", "characters/traits/reorder_traitlist.html")

    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/traits/reorder_traitlist_facebox.html",
        )

    tln = get_object_or_404(TraitListName, slug=traitlistname_slug)
    DisplayOrderFormSet = formset_factory(DisplayOrderForm, extra=0)
    if request.method == "POST":
        formset = DisplayOrderFormSet(request.POST)
        if formset.is_valid():
            from pprint import pprint
            pprint(formset.cleaned_data)
            for data in formset.cleaned_data:
                traitlist = TraitList.objects.get(id=data['traitlist_id'])
                traitlist.display_order = data['order']
                traitlist.save()
            return HttpResponseRedirect(reverse("sheet_list", args=[sheet_id]))
    else:
        qs = TraitList.objects.filter(sheet=sheet, name=tln).order_by('display_order')
        initial = []
        traits = []
        for trait_list in qs:
            initial.append({'order': trait_list.display_order, 'traitlist_id': trait_list.id, 'trait': unicode(trait_list.trait)})
            traits.append(trait_list.trait)
        formset = DisplayOrderFormSet(initial=initial)

    return render_to_response(template_name, {
        'sheet': sheet,
        'traitlistname': tln,
        'traits': traits,
        'formset': formset,
    }, context_instance=RequestContext(request))

@login_required
def edit_traitlist(request, sheet_id, traitlistname_slug,
                   group_slug=None, bridge=None,
                   form_class=TraitListDisplayForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), id=sheet_id)
    else:
        sheet = get_object_or_404(Sheet, id=sheet_id)

    # Check all of the various sheet editing permissions
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)
    template_name = kwargs.get("template_name", "characters/traits/edit_traitlist.html")

    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/traits/edit_traitlist_facebox.html",
        )

    tln = get_object_or_404(TraitListName, slug=traitlistname_slug)
    tl = sheet.get_traitlist(tln.name)
    form = form_class(request.POST or None)
    if form.is_valid() and request.method == "POST":
        for t in tl:
            t.display_preference = form.cleaned_data['display']
            t.save()
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_id]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'traitlistname': tln,
        'traitlist': tl,
        'form': form,
    }, context_instance=RequestContext(request))

@login_required
def edit_trait(request, sheet_id, trait_id,
               group_slug=None, bridge=None,
               form_class=TraitForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), id=sheet_id)
    else:
        sheet = get_object_or_404(Sheet, id=sheet_id)

    trait = get_object_or_404(sheet.traits.all(), id=trait_id)

    # Check all of the various sheet editing permissions
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)

    template_name = kwargs.get("template_name", "characters/traits/edit_trait.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/traits/edit_trait_facebox.html",
        )

    form = form_class(request.POST or None, instance=trait)
    if form.is_valid() and request.method == "POST":
        form.save()
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_id]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'form': form,
        'trait': trait,
        'group': group,
    }, context_instance=RequestContext(request))

@login_required
def delete_trait(request, sheet_id, trait_id,
                 group_slug=None, bridge=None,
                 **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), id=sheet_id)
    else:
        sheet = get_object_or_404(Sheet, id=sheet_id)
    trait = get_object_or_404(sheet.traits.all(), id=trait_id)

    # Check all of the various sheet editing permissions
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)

    template_name = kwargs.get("template_name", "characters/traits/delete_trait.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/traits/delete_trait_facebox.html",
        )

    if request.method == "POST" and request.POST.has_key('__confirm__'):
        trait.delete()
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_id]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'trait': trait,
        'group': group,
    }, context_instance=RequestContext(request))

@login_required
def new_trait(request, sheet_id, traitlistname_slug,
               group_slug=None, bridge=None,
               form_class=TraitForm, **kwargs):
    traitlistname = get_object_or_404(TraitListName, slug=traitlistname_slug)
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), id=sheet_id)
    else:
        sheet = get_object_or_404(Sheet, id=sheet_id)

    # Check all of the various sheet editing permissions
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)

    template_name = kwargs.get("template_name", "characters/traits/new_trait.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/traits/new_trait_facebox.html",
        )

    form = form_class(request.POST or None)
    if form.is_valid() and request.method == "POST":
        trait = form.save(commit=False)
        sheet.add_trait(traitlistname.name, trait)
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_id]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'form': form,
        'group': group,
        'traitlistname': traitlistname,
    }, context_instance=RequestContext(request))
