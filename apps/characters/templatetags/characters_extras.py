from django import template
from pprint import pformat, pprint
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def get_traitlist(sheet, traitlistname):
    retlist = sheet.get_traitlist(traitlistname)
    return retlist

@register.filter
def format_traitlist(traitlist, prepend='', autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    result = '<strong>%s</strong>%s' % (esc(first), esc(other))
    return mark_safe(result)
format_traitlist.needs_autoescape = True

@register.inclusion_tag("characters/_trait_category.html", takes_context=True)
def show_traitlist(context, traitlist_name, prepend=""):
    return {'traits': context['sheet'].get_traitlist(traitlist_name), 'prepend':prepend}
