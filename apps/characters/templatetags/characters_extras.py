from django import template
from pprint import pformat, pprint
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from characters.models import TraitListName, Menu, MenuItem

register = template.Library()

@register.filter
def get_traitlist(sheet, traitlistname):
    retlist = sheet.get_traitlist(traitlistname)
    return retlist

@register.filter
def get_trait_count(sheet, traitlistname):
    retlist = sheet.get_traitlist(traitlistname)
    tlp = sheet.get_traitlist_property(TraitListName.objects.get(name=traitlistname))
    if tlp.atomic:
        return retlist.count()
    else:
        count = sum([t.value for t in retlist])
        return count

@register.filter
def format_traitlist(traitlist, prepend='', autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    result = '<strong>%s</strong>%s' % (esc(first), esc(other))
    return mark_safe(result)
format_traitlist.needs_autoescape = True

@register.filter
def print_trait(trait, tlp):
    if tlp.display_preference == 1:
        trait.display_preference = 2
    return trait

@register.filter
def format_trait(trait, disp):
    trait.display_preference = disp
    return trait

@register.filter
def tally(value):
    return "O" * value

@register.inclusion_tag("characters/show_traitlist.html", takes_context=True)
def show_traitlist(context, traitlist_name, prepend=""):
    printing = False if 'printing' not in context else context['printing']
    tlp = context['sheet'].get_traitlist_property(TraitListName.objects.get(name=traitlist_name))
    return {
        'traits': context['sheet'].get_traitlist(traitlist_name),
        'prepend':prepend,
        'STATIC_URL': context['STATIC_URL'],
        'sheet': context['sheet'],
        'traitlistname': TraitListName.objects.get(name=traitlist_name),
        'printing': printing,
        'tlp': tlp,
    }

@register.inclusion_tag("characters/trait_category_header.html", takes_context=True)
def trait_category_header(context, traitlist_name):
    tln = TraitListName.objects.get(name=traitlist_name)
    printing = False if 'printing' not in context else context['printing']
    return {'traitlistname': tln,
            'sheet': context['sheet'],
            'STATIC_URL': context['STATIC_URL'],
            'printing': printing}

@register.inclusion_tag("characters/_sheet_list_item.html", takes_context=False)
def sheet_list_item(sheet):
    return {'sheet':sheet}

@register.inclusion_tag("characters/trait_category.html", takes_context=True)
def trait_category(context, traitlist_name, prepend=''):
    tln = TraitListName.objects.get(name=traitlist_name)
    printing = False if 'printing' not in context else context['printing']
    return {'traitlistname': tln,
            'sheet': context['sheet'],
            'STATIC_URL': context['STATIC_URL'],
            'prepend':prepend,
            'printing': printing}

@register.inclusion_tag("characters/experience_entries.html", takes_context=True)
def experience_entries(context, experience_entries):
    return {'experience_entries': experience_entries, 'sheet': context['sheet'], 'STATIC_URL': context['STATIC_URL']}

@register.inclusion_tag("characters/experience_entry.html", takes_context=True)
def show_experience_entry(context, entry,):
    return {'entry': entry, 'sheet': context['sheet'], 'STATIC_URL': context['STATIC_URL']}

@register.inclusion_tag("characters/menus/show_menu.html", takes_context=True)
def show_menu(context, in_menu):
    if isinstance(in_menu, basestring):
        menu = Menu.objects.get(name=in_menu)
    else:
        menu = in_menu
    return {
        'menu':menu,
        'previous_url':context['previous_url'],
        'id_segment':context['id_segment'],
        'menu_prefix':context['menu_prefix'],
        'has_parent':context['has_parent'],
        'parent':context['parent'],
        'parent_url':context['parent_url'],
        'under_sheet': context['under_sheet'],
        'group':context['group'],
        'sheet':context['sheet'],
        'traitlistname':context['traitlistname'],
    }

@register.inclusion_tag("characters/menus/__show_menu.html", takes_context=True)
def show_include_menu(context, in_menu):
    if isinstance(in_menu, basestring):
        menu = Menu.objects.get(name=in_menu)
    else:
        menu = in_menu
    return {
        'menu':menu,
        'previous_url':context['previous_url'],
        'id_segment':context['id_segment'],
        'under_sheet': context['under_sheet'],
        'group':context['group'],
        'sheet':context['sheet'],
        'traitlistname':context['traitlistname'],
    }

@register.inclusion_tag("characters/menus/show_menu_item.html", takes_context=True)
def show_menu_item(context, menu_item):
    return {
        'item':menu_item,
        'previous_url':context['previous_url'],
        'id_segment':context['id_segment'],
        'under_sheet': context['under_sheet'],
        'group':context['group'],
        'sheet':context['sheet'],
        'traitlistname':context['traitlistname'],
    }
