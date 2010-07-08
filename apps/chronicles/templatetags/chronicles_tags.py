from django import template
from tribes.forms import TribeForm

register = template.Library()


@register.inclusion_tag("chronicles/chronicle_item.html", takes_context=True)
def show_chronicle(context, tribe):
    return {'chronicle': tribe, 'request': context['request']}

# @@@ should move these next two as they aren't particularly tribe-specific

@register.simple_tag
def clear_search_url(request):
    getvars = request.GET.copy()
    if 'search' in getvars:
        del getvars['search']
    if len(getvars.keys()) > 0:
        return "%s?%s" % (request.path, getvars.urlencode())
    else:
        return request.path


@register.simple_tag
def persist_getvars(request):
    getvars = request.GET.copy()
    if len(getvars.keys()) > 0:
        return "?%s" % getvars.urlencode()
    return ''
