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
from characters.permissions import SheetPermission, can_edit_sheet, can_delete_sheet, can_history_sheet, can_fullview_sheet, can_list_sheet

from characters.forms import SheetUploadForm, VampireSheetAttributesForm, TraitForm, TraitListPropertyForm, DisplayOrderForm, ExperienceEntryForm, NewSheetForm
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from characters.models import Sheet, VampireSheet, TraitListName, Trait, TraitListProperty, ExperienceEntry, Menu, MenuItem
from chronicles.models import Chronicle, ChronicleMember

from reversion.models import Version, DeletedVersion
from django.contrib.contenttypes.models import ContentType

from xml_uploader import handle_sheet_upload, VampireExporter

from pprint import pprint, pformat

@login_required
def upload_sheet(request, chronicle_slug=None, bridge=None):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
def list_sheets(request, chronicle_slug=None, bridge=None):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
            sheet_chronicle_map[chronicle_member.chronicle] = {'pc': [], 'npc':[]}
            for sheet in sheets_for_user:
                if sheet.npc:
                    sheet_chronicle_map[chronicle_member.chronicle]['npc'].append(sheet)
                else:
                    sheet_chronicle_map[chronicle_member.chronicle]['pc'].append(sheet)

    return render_to_response(
        'characters/list_sheets.html',
        {'sheets':sheets,
         'group':group,
         'chronicle_sheets': sheet_chronicle_map,},
        context_instance=RequestContext(request))

@login_required
def list_sheet(request, sheet_slug, chronicle_slug=None, bridge=None):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
def download_sheet(request, sheet_slug,
                   chronicle_slug=None, bridge=None):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    sheet = get_object_or_404(Sheet, slug=sheet_slug)
    if not can_fullview_sheet(request, sheet):
        return permission_denied(request)

    response = HttpResponse(mimetype="application/gex")
    response['Content-Disposition'] = 'filename=' + sheet_slug + '.gex'
    ve = VampireExporter(sheet)
    response.write(ve)
    return response

@login_required
def delete_sheet(request, sheet_slug,
                 chronicle_slug=None, bridge=None,
                 **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), slug=sheet_slug)
    else:
        sheet = get_object_or_404(Sheet, slug=sheet_slug)

    # Check all of the various sheet editing permissions
    if not can_delete_sheet(request, sheet):
        return permission_denied(request)

    template_name = kwargs.get("template_name", "characters/generic_delete.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/generic_delete_facebox.html",
        )

    if request.method == "POST" and request.POST.has_key('__confirm__'):
        sheet.safe_delete()
        return HttpResponseRedirect(reverse('sheets_list'))

    return render_to_response(template_name, {
        'sheet': sheet,
        'group': group,
        'instance': sheet,
        'object_description': 'Sheet',
        'form_template': 'characters/generic_delete_form.html',
        'post_url': reverse('sheet_delete', args=[sheet_slug]),
    }, context_instance=RequestContext(request))

@login_required
def edit_vampire_sheet_attributes(request, sheet_slug,
                                  form_class=VampireSheetAttributesForm, **kwargs):
    sheet = get_object_or_404(Sheet, slug=sheet_slug)
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)

    template_name = kwargs.get("template_name", "characters/vampires/edit_vampire_sheet_attributes.html")

    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/vampires/edit_vampire_sheet_attributes_facebox.html",
        )

    vampire_sheet = sheet.vampiresheet
    form = form_class(request.POST or None, instance=vampire_sheet)
    if form.is_valid() and request.method == "POST":
        form.save()
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet_slug]))

    return render_to_response(template_name, {
        'sheet': vampire_sheet,
        'form': form,
    }, context_instance=RequestContext(request))

def trait_change_ajax_success(request, sheet, traitlistname, group):
    if not request.is_ajax():
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet.slug]))
    else:
        return render_to_response("characters/list_sheet_trait_ajax_success.html", {
            'sheet': sheet,
            'traitlistname': traitlistname,
            'group': group,
        }, context_instance=RequestContext(request))

@login_required
def reorder_traitlist(request, sheet_slug, traitlistname_slug,
                      chronicle_slug=None, bridge=None,
                      **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
            pprint(formset.cleaned_data)
            for data in formset.cleaned_data:
                trait = sheet.traits.get(id=data['trait_id'])
                if data['order'] != trait.order:
                    trait.order = data['order']
                    trait.save()
            return trait_change_ajax_success(request, sheet, tln, group)
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
                   chronicle_slug=None, bridge=None,
                   form_class=TraitListPropertyForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
        print "tln", tln
        return trait_change_ajax_success(request, sheet, tln, group)

    return render_to_response(template_name, {
        'sheet': sheet,
        'traitlistname': tln,
        'form': form,
    }, context_instance=RequestContext(request))

@login_required
def edit_trait(request, sheet_slug, trait_id,
               chronicle_slug=None, bridge=None,
               form_class=TraitForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
    form.is_valid()
    pprint(form.errors)
    print request.is_ajax()
    if form.is_valid() and request.method == "POST":
        form.save()
        return trait_change_ajax_success(request, sheet, trait.traitlistname, group)

    return render_to_response(template_name, {
        'sheet': sheet,
        'form': form,
        'trait': trait,
        'group': group,
    }, context_instance=RequestContext(request))

@login_required
def reload_traits(request, sheet_slug, traitlistname_slug,
                  chronicle_slug=None, bridge=None,
                  form_class=TraitForm, **kwargs):
    traitlistname = get_object_or_404(TraitListName, slug=traitlistname_slug)
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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

    template_name = "characters/_trait_category.html"
    return render_to_response(template_name, {
        'sheet': sheet,
        'group': group,
        'traitlistname': traitlistname,
        'prepend': '',
    }, context_instance=RequestContext(request))

@login_required
def delete_trait(request, sheet_slug, trait_id,
                 chronicle_slug=None, bridge=None,
                 **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
        tln = trait.traitlistname
        trait.delete()
        return trait_change_ajax_success(request, sheet, tln, group)

    return render_to_response(template_name, {
        'sheet': sheet,
        'trait': trait,
        'group': group,
    }, context_instance=RequestContext(request))

@login_required
def new_trait(request, sheet_slug, traitlistname_slug,
              menuitem_id=None, id_segment=None,
              chronicle_slug=None, bridge=None,
              form_class=TraitForm, **kwargs):
    traitlistname = get_object_or_404(TraitListName, slug=traitlistname_slug)
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
        print "New sheet trait is Ajax"
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/traits/new_trait_facebox.html",
        )

    if request.method == "POST":
        form = form_class(request.POST or None)
        if form.is_valid():
            sheet.add_trait(traitlistname.name, form.cleaned_data)
            print "returning ajax check"
            return trait_change_ajax_success(request, sheet, traitlistname, group)
    else:
        t = None
        if menuitem_id is not None:
            mi = MenuItem.objects.get(id=menuitem_id)
            t = Trait(name=mi.name, traitlistname=traitlistname, sheet=sheet, order=0, value=mi.cost)
            t.note = mi.note
            t.display_preference = sheet.get_traitlist_property(traitlistname).display_preference
            ids = id_segment.split('/')
            if len(ids) >= 2:
                menus = []
                for id in ids:
                    menus.append(Menu.objects.get(id=id))
                names = [m.name for m in menus[1:]]
                pprint(names)
                prefix = ': '.join(names) + ': '

                t.name = prefix + t.name

        form = form_class(request.POST or None, instance=t)

    print "returning regs"
    return render_to_response(template_name, {
        'sheet': sheet,
        'form': form,
        'group': group,
        'traitlistname': traitlistname,
    }, context_instance=RequestContext(request))

@login_required
def history_sheet(request, sheet_slug,
                  chronicle_slug=None, bridge=None,
                  form_class=TraitForm, template_name="characters/history.html"):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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

    sheet_trait_ids = frozenset(unicode(pk) for pk in sheet.traits.values_list("pk", flat=True))
    sheet_deleted_trait_ids = frozenset(unicode(pk) for pk in sheet.deleted_traits.values_list("pk", flat=True))
    print "sheet_trait_ids", sheet_trait_ids
    print "sheet_deleted_trait_ids", sheet_deleted_trait_ids

    def expanded_trait_call(version, trait_in):
        print "expanded_trait_call Sheet outer", sheet
        print "expanded_trait_call trait in", trait_in
        if version.object_id in sheet_trait_ids or version.object_id in sheet_deleted_trait_ids:
                try:
                    return sheet == trait_in.sheet
                except Sheet.DoesNotExist:
                    print "Sheet does not exist"
        else:
            print "Not in current or deleted trait ids"
        return False

    versions_map = {
        'Traits':(Trait, expanded_trait_call),
        'Experience Entries':(ExperienceEntry, lambda v,x: x.sheet_set.filter(id=sheet.id).count() > 0),
        'Sheet attributes':(Sheet, lambda v,x: sheet.id == x.id),
    }
    try:
        versions_map['Vampire attributes'] = (VampireSheet, lambda v,x: sheet.vampiresheet == x)
    except VampireSheet.DoesNotExist:
        pass

    for key in versions_map.keys():
        tl = []
        versions = Version.objects.filter(content_type=ContentType.objects.get_for_model(versions_map[key][0]))
        for version in versions:
            obj = version.object_version.object
            if versions_map[key][1](version, obj):
                bucket_string = "updated"
                tl.append((version.revision.date_created, version.revision.user, obj, bucket_string, version.object_id))
        dversions = DeletedVersion.objects.filter(content_type=ContentType.objects.get_for_model(versions_map[key][0]))
        print "printing dversions"
        pprint(dversions)
        print "print all deleted versions"
        print ", ".join([unicode(dv) for dv in DeletedVersion.objects.all()])
        for dversion in dversions:
            obj = Version.objects.get_deleted_object(dversion).object_version.object
            if versions_map[key][1](dversion, obj):
                tl.append((dversion.revision.date_created, dversion.revision.user, obj, "deleted", dversion.object_id))

        tl.sort(key=lambda x: x[0])
        versions_map[key] = tl

    return render_to_response(template_name, {
        'sheet': sheet,
        'versions': versions_map,
        'group': group,
    }, context_instance=RequestContext(request))

@login_required
def permissions_sheet(request, sheet_slug,
                      chronicle_slug=None, bridge=None,
                      template_name="characters/permissions.html"):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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

def experience_entry_change_ajax_success(request, sheet, entry, group):
    if not request.is_ajax():
        return HttpResponseRedirect(reverse("sheet_list", args=[sheet.slug]))
    else:
        if entry is None:
            return render_to_response("characters/list_sheet_experience_entries_ajax_success.html", {
                'sheet': sheet,
                'group': group,
            }, context_instance=RequestContext(request))
        else:
            entry_ids = sheet.experience_entries.filter(date__gte=entry.date).values_list("id", flat=True)
            return render_to_response("characters/list_sheet_experience_entry_ajax_success.html", {
                'sheet': sheet,
                'entry_ids': entry_ids,
                'group': group,
            }, context_instance=RequestContext(request))

@login_required
def reload_entry(request, sheet_slug, entry_id,
                 chronicle_slug=None, bridge=None,
                 form_class=TraitForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), slug=sheet_slug)
    else:
        sheet = get_object_or_404(Sheet, slug=sheet_slug)

    entry = get_object_or_404(sheet.experience_entries.all(), id=entry_id)

    # Check all of the various sheet editing permissions
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)

    template_name = "characters/_experience_entry.html"
    return render_to_response(template_name, {
        'sheet': sheet,
        'group': group,
        'entry': entry,
    }, context_instance=RequestContext(request))

@login_required
def reload_entries(request, sheet_slug,
                   chronicle_slug=None, bridge=None,
                   form_class=TraitForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheet = get_object_or_404(group.content_objects(Sheet), slug=sheet_slug)
    else:
        sheet = get_object_or_404(Sheet, slug=sheet_slug)

    entries = sheet.experience_entries.all()

    # Check all of the various sheet editing permissions
    if not can_edit_sheet(request, sheet):
        return permission_denied(request)

    template_name = "characters/_experience_entries.html"
    return render_to_response(template_name, {
        'sheet': sheet,
        'group': group,
        'experience_entries': entries,
    }, context_instance=RequestContext(request))

def experience_entry_action(request, sheet_slug, entry_id=None,
                            action_description="", object_description="Experience Entry",
                            post_url="", action=None,
                            chronicle_slug=None, bridge=None,
                            form_class=ExperienceEntryForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
        return experience_entry_change_ajax_success(request, sheet, entry, group)

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
                         chronicle_slug=None, bridge=None,
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
                            chronicle_slug=None, bridge=None,
                            form_class=ExperienceEntryForm, **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
        print "Posting recent"
        form = form_class(request.POST)
        pprint(request.POST)
        form.is_valid()
        pprint(form.cleaned_data)
        pprint(form.errors)
        if form.is_valid():
            print "Valid?"
            sheet.add_experience_entry(form.save(commit=False))
            return experience_entry_change_ajax_success(request, sheet, None, group)
        else:
            print "Invalid?"
    else:
        import datetime
        entry = ExperienceEntry()
        added_versions = []
        deleted_versions = []
        added_pks = set()
        deleted_pks = set()

        reasons = {'added': [], 'unspent': [], 'removed': []}
        entry.change = 0
        differences = []

        start_added = datetime.datetime.now()
        versions = Version.objects.filter(content_type=ContentType.objects.get_for_model(Trait))
        try:
            last_date = sheet.experience_entries.all().order_by('-date')[0].date
            versions = versions.filter(revision__date_created__gt=last_date)
        except IndexError:
            last_data = None
            versions = versions.all()
        versions = versions.order_by('-revision__date_created')

        sheet_trait_ids = frozenset(unicode(pk) for pk in sheet.traits.values_list("pk", flat=True))
        sheet_deleted_trait_ids = frozenset(unicode(pk) for pk in sheet.deleted_traits.values_list("pk", flat=True))

        for version in versions:
            print "date ->", version.revision.date_created
            if version.object_id in sheet_trait_ids:
                if not version.object_id in added_pks:
                    added_pks.add(version.object_id)

        end_added = datetime.datetime.now()
        print "Added: ", added_pks

        def is_meaningful_xp_trait_change(current, previous):
            #attrs_hold = ["name",
            #              "note",
            #              "value",
            #              "display_preference",
            #              "dot_character",
            #              "approved",
            #              "order",
            #              "sheet",
            #              "traitlistname"]
            attrs_hold = ["value"]
            print "in is_meaningful_xp_trait_change"
            print current
            print previous
            has_differences = [getattr(current, ah) != getattr(previous, ah) for ah in attrs_hold]
            print has_differences
            print "out is_meaningful_xp_trait_change"
            return any(has_differences)

        for added_pk in added_pks:
            # Get the most recent value for a trait and
            # the valid closest one to the "last_date" for comparison
            most_recent = sheet.traits.get(id=added_pk)
            print "Most recent", most_recent
            prev_comparison_filter = Version.objects.filter(content_type=ContentType.objects.get_for_model(Trait)).filter(object_id=added_pk)
            if last_date is not None:
                print "last_date ", last_date
                prev_comparison_filter = prev_comparison_filter.filter(revision__date_created__lte=last_date)
            else:
                print "last_date None"
                prev_comparison_filter.all()
            prev_comparison_filter = prev_comparison_filter.order_by('-revision__date_created')
            print "All revisions for pk [" + ", ".join([unicode(v) for v in prev_comparison_filter]) + "]"
            try:
                need_valid_filter = True
                i = 0
                while need_valid_filter:
                    prev_comparison = prev_comparison_filter[i].object_version.object
                    need_valid_filter = not is_meaningful_xp_trait_change(most_recent, prev_comparison)
                    i = i + 1
                difference = most_recent.value - prev_comparison.value
                print "prev_camparison ", prev_comparison
                print "difference", difference
            except IndexError:
                # If we hit here, then "most_recent" is the initial entry
                difference = most_recent.value
                print "prev_camparison None"
                print "difference", difference
            entry.change = entry.change + difference
            most_recent.value = abs(difference)
            if 0 <= difference:
                reasons['added'].append(most_recent)
            else:
                reasons['unspent'].append(most_recent)
            differences.append(difference)

        start_deleted = datetime.datetime.now()

        deleted_versions_qs = [Version.objects.get_deleted_object(Trait, object_id, None)
                   for object_id in deleted_pks]
        deleted_versions_qs.sort(lambda a, b: cmp(a.revision.date_created, b.revision.date_created))
        for version in deleted_versions_qs:
            obj = version.object_version.object
            if sheet == obj.sheet:
                deleted_versions.append([version, obj])
        end_deleted = datetime.datetime.now()
        print "Deleted: ", deleted_pks

        for av, ao in deleted_versions:
            reasons['removed'].append(ao)
            try:
                prev_av = Version.objects.get_for_object_reference(Trait, av.object_id).order_by('-revision__date_created')[1]
            except IndexError:
                prev_av = None
            if prev_av is not None:
                difference = ao.value
                if 0 == difference:
                    continue
            else:
                difference = 0
            entry.change = entry.change - difference
            differences.append(difference)

        if 0 == entry.change:
            entry.change_type = 6
        elif entry.change > 0:
            entry.change_type = 3
        else:
            entry.change_type = 4
            entry.change = abs(entry.change)

        #added = [obj for av, obj in added_versions]
        #deleted = [obj for av, obj in deleted_versions]

        #entry.reason = pformat({'added': added, 'deleted': deleted})
        #entry.reason = pformat({'reasons':reasons, 'differences':differences})

        final_reason_str = ""
        pprint(reasons)
        def gen_string(reasons, key, annotate):
            if 0 < len(reasons[key]):
                print key
                return annotate + ", ".join([unicode(r) for r in reasons[key]]) + ". "
            return ''

        final_reason_str = final_reason_str + gen_string(reasons, 'added', "Purchased ")
        final_reason_str = final_reason_str + gen_string(reasons, 'unspent', "Unspent ")
        final_reason_str = final_reason_str + gen_string(reasons, 'removed', "Removed ")

        entry.reason = final_reason_str.strip()

        form = form_class(None, instance=entry)

    return render_to_response(template_name, {
        'sheet': sheet,
        'form': form,
        'group': group,
        'action_description': action_description,
        'object_description': object_description,
        'form_template': 'characters/generic_edit_form.html',
        'post_url': reverse('sheet_add_recent_expenditures', args=[sheet_slug]),
    }, context_instance=RequestContext(request))

@login_required
def edit_experience_entry(request, sheet_slug, entry_id,
                          action_description="Edit",
                          chronicle_slug=None, bridge=None,
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

#login_required
#ef delete_experience_entry(request, sheet_slug, entry_id,
#                           action_description="Delete",
#                           group_slug=None, bridge=None,
#                           form_class=ExperienceEntryForm, **kwargs):
#   return experience_entry_action(
#       request,
#       sheet_slug,
#       entry_id=entry_id,
#       action_description=action_description,
#       post_url=reverse('sheet_delete_experience_entry', args=[sheet_slug, entry_id]),
#       form_class=form_class,
#       **kwargs)

@login_required
def delete_experience_entry(request, sheet_slug, entry_id,
                            chronicle_slug=None, bridge=None,
                            **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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
        return experience_entry_change_ajax_success(request, sheet, None, group)

    return render_to_response(template_name, {
        'sheet': sheet,
        'group': group,
        'instance': entry,
        'object_description': 'Experience Entry',
        'form_template': 'characters/generic_delete_form.html',
        'post_url': reverse('sheet_delete_experience_entry', args=[sheet_slug, entry_id]),
    }, context_instance=RequestContext(request))

@login_required
def join_chronicle(request, target_chronicle_slug,
                   chronicle_slug=None, bridge=None,
                   **kwargs):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    if group:
        sheets = group.get_sheets_for_user(request.user)
    else:
        sheets = Sheet.objects.all()
        sheets = sheets.filter(player__exact=request.user)

    chronicle = get_object_or_404(Chronicle, slug=target_chronicle_slug)
    chronicle_sheets = chronicle.get_sheets_for_user(request.user)

    set_sheets_in_chronicle = set(s.id for s in chronicle_sheets)

    checklist = []
    for sheet in sheets:
        if sheet.id in set_sheets_in_chronicle:
            checklist.append((True, sheet))
        else:
            checklist.append((False, sheet))

    template_name = kwargs.get("template_name", "characters/join_chronicle.html")
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/join_chronicle_facebox.html",
        )

    if request.method == "POST":
        for key in request.POST:
            try:
                c_id = int(key)
                if 'on' == request.POST[key]:
                    sheet = Sheet.objects.get(id=c_id)
                    chronicle.associate(sheet)
                    sheet.save()
            except ValueError:
                continue

        return HttpResponseRedirect(reverse("sheets_list"))

    return render_to_response(template_name, {
        'checklist': checklist,
        'group': group,
        'chronicle': chronicle,
    }, context_instance=RequestContext(request))

@login_required
def make_home_chronicle(request, target_chronicle_slug,
                        chronicle_slug=None, bridge=None,
                        **kwargs):
    raise Http404

def new_vampire_sheet(request, form, group=None):
    # Create the blank sheet
    vs = VampireSheet.objects.create(name=form.cleaned_data['name'], player=request.user)
    vs.save()

    vs.add_default_traitlist_properties()
    vs.save()

    return vs

@login_required
def new_sheet(request,
              chronicle_slug=None, bridge=None,
              form_class=NewSheetForm, template_name="characters/new_sheet.html"):
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
        except ObjectDoesNotExist:
            raise Http404
    else:
        group = None

    form = form_class(request.POST or None)
    mapping = {'vampire': new_vampire_sheet}
    if request.method == "POST":
        if form.is_valid():
            ret = mapping[form.cleaned_data['creature_type']](request, form, group)
            if group is not None:
                group.associate(ret)
                ret.save()
            return HttpResponseRedirect(reverse('sheets_list'))

    return render_to_response(template_name, {
        'form': form,
        'group': group,
    }, context_instance=RequestContext(request))

def get_menu_prefix_for_menus(menus):
    menu_prefix = ''
    if len(menus) >= 3:
        pprint({'raw_names': [m.name for m in menus]})
        names = [m.name for m in menus[1:-1]]
        pprint(names)
        menu_prefix = ': '.join(names) + ': '

    return menu_prefix

@login_required
def show_menu(request, id_segment,
              sheet=None, traitlistname=None,
              group=None,
              **kwargs):
    print id_segment
    template_name = kwargs.get('template_name', "characters/menus/menu.html")

    if request.is_ajax():
        print "Im in ajax mode"
        template_name = kwargs.get(
            "template_name_facebox",
            "characters/menus/_show_menu.html",
        )
    else:
        print "Not in Ajax mode"

    ids = id_segment.split('/')
    menus = []
    for id in ids:
        menus.append(Menu.objects.get(id=id))

    menu_prefix = get_menu_prefix_for_menus(menus)
    menu = menus[-1]
    parent = None
    has_parent = False
    parent_url = ''
    if len(menus) >= 2:
        has_parent = True
        parent = menus[-2]
        parent_url = reverse('menu_show', args=['/'.join([str(m.id) for m in menus[:-1]])])

    menu_items = MenuItem.objects.filter(parent__id=menu.id).order_by('order')

    previous_url = reverse('menu_show', args=[id_segment])
    under_sheet = False
    print sheet
    if sheet is not None:
        under_sheet = True
        parent_url = reverse('sheet_new_trait_from_menu', args=[
            sheet.slug,
            traitlistname.slug,
            '/' + '/'.join([str(m.id) for m in menus[:-1]])])
        previous_url = reverse('sheet_new_trait_from_menu', args=[
            sheet.slug,
            traitlistname.slug,
            '/' + id_segment])
    print "Under sheet", under_sheet

    return render_to_response(template_name, {
        'previous_url': previous_url,
        'id_segment': id_segment,
        'menu': menu,
        'menu_prefix': menu_prefix,
        'has_parent': has_parent,
        'parent': parent,
        'parent_url': parent_url,

        'under_sheet': under_sheet,
        'group': group,
        'sheet': sheet,
        'traitlistname': traitlistname,
    }, context_instance=RequestContext(request))

@login_required
def show_menus(request,
              template_name="characters/menus/menus.html"):
    return render_to_response(template_name, {
        'menus': Menu.objects.all(),
    }, context_instance=RequestContext(request))

@login_required
def new_trait_from_menu(request, sheet_slug, traitlistname_slug, id_segment,
                        chronicle_slug=None, bridge=None,
                        form_class=TraitForm, **kwargs):
    traitlistname = get_object_or_404(TraitListName, slug=traitlistname_slug)
    if bridge is not None:
        try:
            group = bridge.get_group(chronicle_slug)
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

    print traitlistname.name
    print "sheet in new_trait_from_menu", sheet
    send_segment = None
    if len(id_segment) > 0:
        print "id_segment", pformat(id_segment[1:])
        send_segment = id_segment[1:]
    else:
        try:
            if sheet.vampiresheet:
                desired_menu = Menu.get_menu_for_traitlistname(traitlistname, VampireSheet)
        except ObjectDoesNotExist:
            desired_menu = Menu.get_menu_for_traitlistname(traitlistname)
        print desired_menu.name
        send_segment = "%d" % desired_menu.id

    return show_menu(
        request,
        send_segment,
        sheet=sheet,
        traitlistname=traitlistname,
        group=group,
        template_name_facebox="characters/menus/show_menu.html")

    #form = form_class(request.POST or None)
    #print "in add trait"
    #from pprint import pprint
    #pprint(form.errors)
    #if form.is_valid() and request.method == "POST":
    #    sheet.add_trait(traitlistname.name, form.cleaned_data)
    #    print "returning ajax check"
    #    return trait_change_ajax_success(request, sheet, traitlistname, group)

    #print "returning regs"
    #return render_to_response(template_name, {
    #    'sheet': sheet,
    #    'form': form,
    #    'group': group,
    #    'traitlistname': traitlistname,
    #}, context_instance=RequestContext(request))
