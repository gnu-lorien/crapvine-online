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
from characters.permissions import SheetPermission, can_edit_sheet, can_delete_sheet, can_history_sheet, can_fullview_sheet

from characters.forms import SheetUploadForm, VampireSheetAttributesForm, TraitForm, TraitListPropertyForm, DisplayOrderForm, ExperienceEntryForm
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from characters.models import Sheet, VampireSheet, TraitListName, Trait, TraitListProperty, ExperienceEntry

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

    sheet_chronicle_map = {}
    if group:
        sheets = group.get_sheets_for_user(request.user)
    else:
        sheets = Sheet.objects.all()
        sheets = sheets.filter(player__exact=request.user)
        sheet_chronicle_map = {}
        for chronicle_member in request.user.chronicles.all():
            sheets_for_user = chronicle_member.chronicle.get_sheets_for_user(request.user)
            sheet_chronicle_map[chronicle_member.chronicle.name] = {'pc': [], 'npc':[]}
            for sheet in sheets_for_user:
                if sheet.npc:
                    sheet_chronicle_map[chronicle_member.chronicle.name]['npc'].append(sheet)
                else:
                    sheet_chronicle_map[chronicle_member.chronicle.name]['pc'].append(sheet)

    return render_to_response(
        'characters/list_sheets.html',
        {'sheets':sheets,
         'group':group,
         'chronicle_sheets': sheet_chronicle_map,},
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
    if not can_fullview_sheet(request, sheet):
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

    tl = []
    versions = Version.objects.filter(content_type=ContentType.objects.get_for_model(Trait))
    for version in versions:
        obj = version.object_version.object
        if sheet == obj.sheet:
            tl.append((version.revision.date_created, version.revision.user, obj, "updated", version.object_id))
    versions = Version.objects.get_deleted(Trait)
    for version in versions:
        obj = version.object_version.object
        if sheet == obj.sheet:
            tl.append((version.revision.date_created, version.revision.user, obj, "deleted", version.object_id))
    tl.sort(key=lambda x: x[0])

    return render_to_response(template_name, {
        'sheet': sheet,
        'tl_versions': tl,
        'group': group,
    }, context_instance=RequestContext(request))

@login_required
def permissions_sheet(request, sheet_slug,
                      group_slug=None, bridge=None,
                      template_name="characters/permissions.html"):
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
    if not can_list_sheet(request, sheet):
        return permission_denied(request)

    permission_keys = ("list", "history", "delete", "edit")
    permissions = {}
    for key in permission_keys:
        #permissions[key] = [user for user in User.objects.all() if globals()['can_' + key + '_sheet'](request, sheet, user=user)]
        bl = []
        for user in User.objects.all():
            keep = globals()['can_' + key + '_sheet'](request, sheet, user=user, infodump=True)
            if keep[0]:
                bl.append((user, keep[1]))
        permissions[key] = bl

    return render_to_response(template_name, {
        'sheet': sheet,
        'permissions': permissions,
        'group': group,
    }, context_instance=RequestContext(request))

def experience_entry_action(request, sheet_slug, entry_id=None,
                            action_description="", object_description="Experience Entry",
                            post_url="", action=None,
                            group_slug=None, bridge=None,
                            form_class=ExperienceEntryForm, **kwargs):
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

    if entry_id is not None:
        entry = get_object_or_404(sheet.experience_entries.all(), id=entry_id)
    else:
        entry = None

    # Check all of the various sheet editing permissions
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)

    template_name = kwargs.get("template_name", "characters/generic_edit.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/generic_edit_facebox.html",
        )

    form = form_class(request.POST or None, instance=entry)
    if form.is_valid() and request.method == "POST":
        action(form, sheet)
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'form': form,
        'group': group,
        'entry': entry,
        'action_description': action_description,
        'object_description': object_description,
        'form_template': 'characters/generic_edit_form.html',
        'post_url': post_url,
    }, context_instance=RequestContext(request))

@login_required
def new_experience_entry(request, sheet_slug, entry_id=None,
                         action_description="New",
                         group_slug=None, bridge=None,
                         form_class=ExperienceEntryForm, **kwargs):
    def local_action(form, sheet):
        sheet.add_experience_entry(form.save(commit=False))
    return experience_entry_action(
        request,
        sheet_slug,
        entry_id=entry_id,
        action_description=action_description,
        post_url=reverse('sheet_new_experience_entry', args=[sheet_slug]),
        action=local_action,
        form_class=form_class,
        **kwargs)

@login_required
def add_recent_expenditures(request, sheet_slug,
                            action_description="Recent Expenditures", object_description="Experience Entry",
                            group_slug=None, bridge=None,
                            form_class=ExperienceEntryForm, **kwargs):
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

    template_name = kwargs.get("template_name", "characters/generic_edit.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/generic_edit_facebox.html",
        )

    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            sheet.add_experience_entry(form.save(commit=False))
            return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))
    else:
        import datetime
        entry = ExperienceEntry()
        added = []
        added_pks = set()
        deleted = []
        start_added = datetime.datetime.now()
        versions = Version.objects.filter(content_type=ContentType.objects.get_for_model(Trait))
        try:
            last_date = sheet.experience_entries.all().order_by('-date')[0].date
            versions = versions.filter(revision__date_created__gt=last_date)
        except IndexError:
            versions = versions.all()
        versions = versions.order_by('revision__date_created')

        for version in versions:
            obj = version.object_version.object
            if sheet == obj.sheet:
                added.append(obj)
                added_pks.add(version.object_id)
        end_added = datetime.datetime.now()
        print "Added: ", end_added - start_added

        start_deleted = datetime.datetime.now()
        live_pks = frozenset([unicode(pk) for pk in Trait.objects.all().values_list("pk", flat=True)])
        mix_pks = live_pks.intersection(added_pks)

        deleted_pks = added_pks - live_pks
        deleted_versions = [Version.objects.get_deleted_object(Trait, object_id, None)
                   for object_id in deleted_pks]
        deleted_versions.sort(lambda a, b: cmp(a.revision.date_created, b.revision.date_created))
        for version in deleted_versions:
            obj = version.object_version.object
            if sheet == obj.sheet:
                deleted.append(obj)
        end_deleted = datetime.datetime.now()
        print "Deleted: ", end_deleted - start_deleted

        from pprint import pformat
        entry.reason = pformat({'added': added, 'deleted': deleted})

        form = form_class(None, instance=entry)

    return render_to_response(template_name, {
        'sheet': sheet,
        'form': form,
        'group': group,
        'entry': entry,
        'action_description': action_description,
        'object_description': object_description,
        'form_template': 'characters/generic_edit_form.html',
        'post_url': reverse('sheet_add_recent_expenditures', args=[sheet_slug]),
    }, context_instance=RequestContext(request))

@login_required
def edit_experience_entry(request, sheet_slug, entry_id,
                          action_description="Edit",
                          group_slug=None, bridge=None,
                          form_class=ExperienceEntryForm, **kwargs):
    def local_action(form, sheet):
        entry = form.save()
        sheet.edit_experience_entry(entry)
    return experience_entry_action(
        request,
        sheet_slug,
        entry_id=entry_id,
        action_description=action_description,
        post_url=reverse('sheet_edit_experience_entry', args=[sheet_slug, entry_id]),
        form_class=form_class,
        action=local_action,
        **kwargs)

@login_required
def delete_experience_entry(request, sheet_slug, entry_id,
                            action_description="Delete",
                            group_slug=None, bridge=None,
                            form_class=ExperienceEntryForm, **kwargs):
    return experience_entry_action(
        request,
        sheet_slug,
        entry_id=entry_id,
        action_description=action_description,
        post_url=reverse('sheet_delete_experience_entry', args=[sheet_slug, entry_id]),
        form_class=form_class,
        **kwargs)

@login_required
def delete_experience_entry(request, sheet_slug, entry_id,
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

    if entry_id is not None:
        entry = get_object_or_404(sheet.experience_entries.all(), id=entry_id)
    else:
        entry = None

    # Check all of the various sheet editing permissions
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)

    template_name = kwargs.get("template_name", "characters/generic_delete.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/generic_delete_facebox.html",
        )

    if request.method == "POST" and request.POST.has_key('__confirm__'):
        sheet.delete_experience_entry(entry)
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))

    return render_to_response(template_name, {
        'sheet': sheet,
        'group': group,
        'instance': entry,
        'object_description': 'Experience Entry',
        'form_template': 'characters/generic_delete_form.html',
        'post_url': reverse('sheet_delete_experience_entry', args=[sheet_slug, entry_id]),
    }, context_instance=RequestContext(request))
