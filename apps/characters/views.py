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
from characters.permissions import SheetPermission, can_edit_sheet, can_delete_sheet, can_history_sheet, can_list_sheet

from characters.forms import SheetUploadForm, VampireSheetAttributesForm, TraitForm, TraitListPropertyForm, DisplayOrderForm
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from characters.models import Sheet, VampireSheet, TraitListName, Trait, TraitListProperty

from reversion.models import Version
from django.contrib.contenttypes.models import ContentType

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
def list_sheet(request, sheet_slug, group_slug=None, bridge=None):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    sheet = get_object_or_404(Sheet, slug=sheet_slug)
    if not can_list_sheet(request, sheet):
        return permission_denied(request)

    ee = sheet.experience_entries.all().order_by('date')
    return render_to_response(
        'characters/list_sheet.html',
        {'sheet':sheet,
         'group':group,
         'experience_entries':ee},
        context_instance=RequestContext(request))

@login_required
def download_sheet(request, sheet_slug):
    sheet = VampireSheet.objects.get(slug=sheet_slug, player=request.user)
    response = HttpResponse(mimetype="application/gex")
    response['Content-Disposition'] = 'attachment; filename=Exchange.gex'
    ve = VampireExporter(sheet)
    response.write(ve)
    return response

@login_required
def edit_vampire_sheet_attributes(request, sheet_slug,
                                  form_class=VampireSheetAttributesForm, **kwargs):
    template_name = kwargs.get("template_name", "characters/vampires/edit_vampire_sheet_attributes.html")

    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/vampires/edit_vampire_sheet_attributes_facebox.html",
        )

    vampire_sheet = VampireSheet.objects.get(slug=sheet_slug)
    form = form_class(request.POST or None, instance=vampire_sheet)
    if form.is_valid() and request.method == "POST":
        form.save()
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))

    return render_to_response(template_name, {
        'sheet': vampire_sheet,
        'form': form,
    }, context_instance=RequestContext(request))

@login_required
def reorder_traitlist(request, sheet_slug, traitlistname_slug,
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
        sheet = get_object_or_404(group.content_objects(Sheet), slug=sheet_slug)
    else:
        sheet = get_object_or_404(Sheet, slug=sheet_slug)

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
    traits = []
    DisplayOrderFormSet = formset_factory(DisplayOrderForm, extra=0)
    if request.method == "POST":
        formset = DisplayOrderFormSet(request.POST)
        if formset.is_valid():
            from pprint import pprint
            pprint(formset.cleaned_data)
            for data in formset.cleaned_data:
                trait = sheet.traits.get(id=data['trait_id'])
                if data['order'] != trait.order:
                    trait.order = data['order']
                    trait.save()
            return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))
    else:
        traits = sheet.get_traits(tln.name)
        initial = []
        for trait in traits:
            initial.append({'order': trait.order, 'trait_id': trait.id, 'trait': unicode(trait)})
        formset = DisplayOrderFormSet(initial=initial)

    return render_to_response(template_name, {
        'sheet': sheet,
        'traitlistname': tln,
        'traits': traits,
        'formset': formset,
    }, context_instance=RequestContext(request))

@login_required
def edit_traitlist(request, sheet_slug, traitlistname_slug,
                   group_slug=None, bridge=None,
                   form_class=TraitListPropertyForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), slug=sheet_slug)
    else:
        sheet = get_object_or_404(Sheet, slug=sheet_slug)

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
    tlp = sheet.get_traitlist_property(tln)
    form = form_class(request.POST or None, instance=tlp)
    if form.is_valid() and request.method == "POST":
        tlp = form.save()
        for trait in sheet.get_traitlist(tln.name):
            if trait.display_preference != tlp.display_preference:
                trait.display_preference = tlp.display_preference
                trait.save()
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'traitlistname': tln,
        'form': form,
    }, context_instance=RequestContext(request))

@login_required
def edit_trait(request, sheet_slug, trait_id,
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
        sheet = get_object_or_404(group.content_objects(Sheet), slug=sheet_slug)
    else:
        sheet = get_object_or_404(Sheet, slug=sheet_slug)

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
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'form': form,
        'trait': trait,
        'group': group,
    }, context_instance=RequestContext(request))

@login_required
def delete_trait(request, sheet_slug, trait_id,
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
        sheet = get_object_or_404(group.content_objects(Sheet), slug=sheet_slug)
    else:
        sheet = get_object_or_404(Sheet, slug=sheet_slug)
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
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'trait': trait,
        'group': group,
    }, context_instance=RequestContext(request))

@login_required
def new_trait(request, sheet_slug, traitlistname_slug,
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
        sheet = get_object_or_404(group.content_objects(Sheet), slug=sheet_slug)
    else:
        sheet = get_object_or_404(Sheet, slug=sheet_slug)

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
        sheet.add_trait(traitlistname.name, form.cleaned_data)
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'form': form,
        'group': group,
        'traitlistname': traitlistname,
    }, context_instance=RequestContext(request))

@login_required
def history_sheet(request, sheet_slug,
                  group_slug=None, bridge=None,
                  form_class=TraitForm, template_name="characters/history.html"):
    if bridge is not None:
        try:
            group = bridge.get_group(group_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), slug=sheet_slug)
    else:
        sheet = get_object_or_404(Sheet, slug=sheet_slug)

    # Check all of the various sheet editing permissions
    if not can_history_sheet(request, sheet):
        return permission_denied(request)

    versions = Version.objects.get_for_object(sheet.vampiresheet)

    tl = []
    versions = Version.objects.filter(content_type=ContentType.objects.get_for_model(Trait))
    for version in versions:
        tl.append((version.revision.date_created, version.revision.user, version.object_version.object, "updated", version.object_id))
    versions = Version.objects.get_deleted(Trait)
    for version in versions:
        tl.append((version.revision.date_created, version.revision.user, version.object_version.object, "deleted", version.object_id))
    tl.sort(key=lambda x: x[0])

#   from pprint import pformat
#   versions = Version.objects.filter(content_type=ContentType.objects.get_for_model(TraitList))
#   tl = []
#   last_created_keys = {}
#   for version in versions:
#       obj = version.object_version.object
#       if sheet == obj.sheet:
#           tmp = [version.revision.date_created, version.revision.user, obj]
#
#           try:
#               trait_versions = Version.objects.get_for_object(obj.trait)
#           except Trait.DoesNotExist:
#               obj_trait_test = obj.trait
#               trait_versions = Version.objects.get_deleted_object(Trait, obj.trait)
#           if last_created_keys.has_key(version.object_id):
#               trait_versions = trait_versions.filter(revision__date_created__lte=version.revision.date_created, revision__date_created__gte=last_created_keys[version.object_id])
#           else:
#               trait_versions = trait_versions.filter(revision__date_created__lte=version.revision.date_created)
#           trait_versions = trait_versions.order_by("-revision__date_created")
#           traits = [v.object_version.object for v in trait_versions]
#           tl.append([version.revision.date_created, version.revision.user, obj, traits])
#           last_created_keys[version.object_id] = version.revision.date_created

    return render_to_response(template_name, {
        'sheet': sheet,
        'tl_versions': tl,
        'group': group,
    }, context_instance=RequestContext(request))
