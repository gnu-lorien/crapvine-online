import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.views.generic import date_based

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from pinax.apps.blog.models import Post

# Create your views here.
def what_next(request, template_name="about/what_next.html"):
    try:
        blogs = Post.objects.filter(status=2).select_related(depth=1).order_by("-publish").filter(author=User.objects.get(username__exact='ourianet'))
        if len(blogs) > 0:
            blog = blogs[0]
        else:
            blog = None
    except:
        blog = None
    return render_to_response(template_name, {
        "blog": blog,
    }, context_instance=RequestContext(request))

