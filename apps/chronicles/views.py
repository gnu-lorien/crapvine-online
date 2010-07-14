from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _
from authority.views import permission_denied

from django.conf import settings

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

from chronicles.models import Chronicle, ChronicleMember
from chronicles.forms import ChronicleForm, ChronicleUpdateForm, ChronicleMemberForm

TOPIC_COUNT_SQL = """
SELECT COUNT(*)
FROM topics_topic
WHERE
    topics_topic.object_id = chronicles_chronicle.id AND
    topics_topic.content_type_id = %s
"""
MEMBER_COUNT_SQL = """
SELECT COUNT(*)
FROM chronicles_chroniclemember
WHERE chronicles_chroniclemember.chronicle_id = chronicles_chronicle.id
"""

@login_required
def create(request, form_class=ChronicleForm, template_name="chronicles/create.html"):
    chronicle_form = form_class(request.POST or None)
    
    if chronicle_form.is_valid():
        chronicle = chronicle_form.save(commit=False)
        chronicle.creator = request.user
        chronicle.save()
        chronicle_member = ChronicleMember(chronicle=chronicle, user=request.user, membership_role=0)
        chronicle.members.add(chronicle_member)
        chronicle_member.save()
        if notification:
            # @@@ might be worth having a shortcut for sending to all users
            notification.send(User.objects.all(), "chronicles_new_chronicle",
                {"chronicle": chronicle}, queue=True)
        return HttpResponseRedirect(chronicle.get_absolute_url())
    
    return render_to_response(template_name, {
        "chronicle_form": chronicle_form,
    }, context_instance=RequestContext(request))


def chronicles(request, template_name="chronicles/chronicles.html"):
    
    chronicles = Chronicle.objects.all()
    
    search_terms = request.GET.get('search', '')
    if search_terms:
        chronicles = (chronicles.filter(name__icontains=search_terms) |
            chronicles.filter(description__icontains=search_terms))
    
    content_type = ContentType.objects.get_for_model(Chronicle)
    
    chronicles = chronicles.extra(select=SortedDict([
        ('member_count', MEMBER_COUNT_SQL),
        ('topic_count', TOPIC_COUNT_SQL),
    ]), select_params=(content_type.id,))
    
    return render_to_response(template_name, {
        'chronicles': chronicles,
        'search_terms': search_terms,
    }, context_instance=RequestContext(request))

@login_required
def delete(request, group_slug=None, redirect_url=None):
    chronicle = get_object_or_404(Chronicle, slug=group_slug)
    if not redirect_url:
        redirect_url = reverse('chronicle_list')
    
    # @@@ eventually, we'll remove restriction that chronicle.creator can't leave chronicle but we'll still require chronicle.members.all().count() == 1
    if (request.user.is_authenticated() and request.method == "POST" and
            request.user == chronicle.creator and chronicle.members.all().count() == 1):
        chronicle.delete()
        request.user.message_set.create(message=_("Chronicle %(chronicle_name)s deleted.") % {"chronicle_name": chronicle.name})
        # no notification required as the deleter must be the only member
    
    return HttpResponseRedirect(redirect_url)

def can_edit_membership(request, chronicle, user=None):
    if user is None:
        user = request.user
    if not chronicle.user_is_member(request.user):
        return False
    if 0 != ChronicleMember.objects.filter(user=user, chronicle=chronicle)[0].membership_role:
        return False

    return True

@login_required
def edit_membership(request, group_slug=None, username=None,
                    form_class=ChronicleMemberForm, **kwargs):
    template_name = kwargs.get("template_name", "chronicles/edit_membership.html")

    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "chronicles/edit_membership_facebox.html"
        )

    chronicle = get_object_or_404(Chronicle, slug=group_slug)
    if not can_edit_membership(request, chronicle):
        return permission_denied(request)

    user = get_object_or_404(User, username=username)
    if not chronicle.user_is_member(user):
        return "trying to edit a user that's not a member??? what now?"

    chronicle_membership = ChronicleMember.objects.filter(user=user, chronicle=chronicle)[0]
    chronicle_membership_form = form_class(request.POST or None, instance=chronicle_membership)
    if chronicle_membership_form.is_valid() and request.method == "POST":
        chronicle_membership = chronicle_membership_form.save()
        chronicle_membership.save()
        return HttpResponseRedirect(reverse("chronicle_members", args=[group_slug]))

    return render_to_response(template_name, {
        "chronicle_membership_form": chronicle_membership_form,
        "changing_username": user.username,
        "member": user,
        "chronicle": chronicle,
    }, context_instance=RequestContext(request))

@login_required
def your_chronicles(request, template_name="chronicles/your_chronicles.html"):
    return render_to_response(template_name, {
        "chronicles": Chronicle.objects.filter(member_users=request.user).order_by("name"),
    }, context_instance=RequestContext(request))

@login_required
def list_members(request, group_slug=None, template_name="chronicles/list_members.html"):
    chronicle = get_object_or_404(Chronicle, slug=group_slug)
    return render_to_response(template_name, {
        "chronicle": chronicle,
        "can_edit_membership": can_edit_membership(request, chronicle),
    }, context_instance=RequestContext(request))

def chronicle(request, group_slug=None, form_class=ChronicleUpdateForm,
        template_name="chronicles/chronicle.html"):
    chronicle = get_object_or_404(Chronicle, slug=group_slug)
    
    chronicle_form = form_class(request.POST or None, instance=chronicle)
    
    if not request.user.is_authenticated():
        is_member = False
    else:
        is_member = chronicle.user_is_member(request.user)
    
    action = request.POST.get('action')
    if action == 'update' and chronicle_form.is_valid():
        chronicle = chronicle_form.save()
    elif action == 'join':
        if not is_member:
            chronicle_member = ChronicleMember(chronicle=chronicle, user=request.user)
            chronicle.members.add(chronicle_member)
            chronicle_member.save()
            request.user.message_set.create(
                message=_("You have joined the chronicle %(chronicle_name)s") % {"chronicle_name": chronicle.name})
            is_member = True
            if notification:
                notification.send([chronicle.creator], "chronicles_created_new_member", {"user": request.user, "chronicle": chronicle})
                notification.send(chronicle.member_users.all(), "chronicles_new_member", {"user": request.user, "chronicle": chronicle})
        else:
            request.user.message_set.create(
                message=_("You have already joined chronicle %(chronicle_name)s") % {"chronicle_name": chronicle.name})
    elif action == 'leave':
        ChronicleMember.objects.filter(chronicle=chronicle, user=request.user)[0].delete()
        request.user.message_set.create(message="You have left the chronicle %(chronicle_name)s" % {"chronicle_name": chronicle.name})
        is_member = False
        if notification:
            pass # @@@ no notification on departure yet
    
    return render_to_response(template_name, {
        "chronicle_form": chronicle_form,
        "chronicle": chronicle,
        "group": chronicle, # @@@ this should be the only context var for the chronicle
        "is_member": is_member,
    }, context_instance=RequestContext(request))
