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

from characters.forms import SheetUploadForm
from characters.models import Sheet

from xml_uploader import handle_sheet_upload

@login_required
def upload_sheet(request):
    if request.method == 'POST':
        form = SheetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_sheet_upload(request.FILES['file'], request.user)
            return HttpResponseRedirect('/success/url')
    else:
        form = SheetUploadForm()
    return render_to_response(
        'characters/upload_sheet.html',
        {'form':form},
        context_instance=RequestContext(request))

@login_required
def list_sheets(request):
    sheets = Sheet.objects.filter(player__exact=request.user)
    return render_to_response(
        'characters/list_sheets.html',
        {'sheets':sheets},
        context_instance=RequestContext(request))

@login_required
def list_sheet(request, sheet_id):
    sheet = Sheet.objects.get(id=sheet_id, player=request.user)
    return render_to_response(
        'characters/list_sheet.html',
        {'sheet':sheet},
        context_instance=RequestContext(request))

