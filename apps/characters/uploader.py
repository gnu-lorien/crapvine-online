from characters.models import VampireSheet

from pprint import pprint
from datetime import timedelta, datetime
from django.db import IntegrityError

def translate_date(date):
    if isinstance(date, basestring):
        date_translation_lambdas = [
            lambda date: datetime.strptime(date, "%m/%d/%Y %I:%M:%S %p"),
            lambda data: datetime.strptime(date, "%m/%d/%Y"),
            lambda data: datetime.strptime(date, "%I:%M:%S %p"),
            lambda date: datetime.strptime(date, "%m/%d/%Y %H:%M:%S %p"),
        ]
        dt = None
        for dtl in date_translation_lambdas:
            try:
                dt = dtl(date)
            except ValueError:
                pass

        if dt is None:
            raise ValueError("Could not convert %s to a proper date" % date)
        return dt
    else:
        if date.hour == date.minute == date.second == 0:
            return date.strftime("%m/%d/%Y")
        else:
            return date.strftime("%m/%d/%Y %I:%M:%S %p")

    raise TypeError("Expected either a string or datetime.datetime")

def map_attributes(attributes_map, attrs):
    for key, remap in attributes_map.iteritems():
        if key in attrs:
            attrs[remap] = attrs.pop(key)

def map_dates(dates, attrs):
    for key in attrs.iterkeys():
        if key in dates:
            attrs[key] = translate_date(attrs[key])


VAMPIRE_TAG_RENAMES = {
    'startdate'    : 'start_date',
    'lastmodified' : 'last_modified',
    'id'           : 'id_text',
}
VAMPIRE_TAG_OVERRIDES = {
    'aurabonus'    : 'aura',
}
VAMPIRE_TAG_REMOVES = ('socialmax', 'mentalmax')
VAMPIRE_TAG_DEFAULTS = {
    'tempconscience' : 'conscience', 
    'tempselfcontrol': 'selfcontrol',
    'tempcourage'    : 'courage',
    'tempwillpower'  : 'willpower',
    'tempblood'      : 'blood',
    'temppathtraits' : 'pathtraits'
}
VAMPIRE_TAG_DATES = ('start_date', 'last_modified')

ENTRY_TAG_RENAMES = {'type':'change_type'}
ENTRY_TAG_DATES = ['date']

TRAIT_TAG_RENAMES = { 'val' : 'value' }

TRAITLIST_TAG_RENAMES = {
    'abc':'sorted',
    'display': 'display_preference',
}

def create_base_vampire(attrs, user):
    if not attrs.has_key('name'):
        raise RuntimeError("Can't create base vampire with no name in attrs")
    my_attrs = dict(attrs)
    map_attributes(VAMPIRE_TAG_RENAMES, my_attrs)
    map_dates(VAMPIRE_TAG_DATES, my_attrs)
    for key, value in VAMPIRE_TAG_OVERRIDES.iteritems():
        if key in my_attrs:
            my_attrs[value] = my_attrs[key]
            del my_attrs[key]
    for key in VAMPIRE_TAG_REMOVES:
        if key in my_attrs:
            del my_attrs[key]
    for key, value in VAMPIRE_TAG_DEFAULTS.iteritems():
        if key not in my_attrs:
            if value in my_attrs:
                my_attrs[key] = my_attrs[value]

    my_attrs['player'] = user
    my_attrs['uploading'] = True
    my_attrs = dict([(str(k), v) for k,v in my_attrs.iteritems()])
    return VampireSheet.objects.create(**my_attrs)

def read_experience_entry(attrs, current_vampire, previous_entry):
    my_attrs = dict(attrs)
    map_attributes(ENTRY_TAG_RENAMES, my_attrs)
    map_dates(ENTRY_TAG_DATES, my_attrs)
    if previous_entry is not None:
        #print self.last_entry.date
        if previous_entry.date >= my_attrs['date']:
            #print my_attrs['date']
            my_attrs['date'] = previous_entry.date + timedelta(seconds=1)
    try:
        my_attrs = dict([(str(k), v) for k,v in my_attrs.iteritems()])
        return current_vampire.experience_entries.create(**my_attrs)
    except IntegrityError, e:
        pprint({'name':current_vampire.name, 'attrs':attrs, 'my_attrs':my_attrs})
        raise e

def read_traitlist_properties(attrs, current_vampire):
    my_attrs = dict(attrs)
    map_attributes(TRAITLIST_TAG_RENAMES, my_attrs)
    my_attrs = dict([(str(k), v) for k,v in my_attrs.iteritems()])
    current_vampire.add_traitlist_properties(**my_attrs)

def read_trait(attrs, current_traitlist, current_vampire, order=None):
    my_attrs = dict(attrs)
    map_attributes(TRAIT_TAG_RENAMES, my_attrs)
    if 'value' in my_attrs:
        try:
            # TODO Remember this when handling the menu items
            # Some things have strange values like "2 or 4" and you need
            # to pick them before setting them in a sheet
            int(my_attrs['value'])
        except ValueError:
            my_attrs['value'] = 999999
    my_attrs['display_preference'] = current_traitlist['display']
    my_attrs = dict([(str(k), v) for k,v in my_attrs.iteritems()])
    if order is not None:
        my_attrs['order'] = order
    current_vampire.add_trait(current_traitlist['name'], my_attrs)


