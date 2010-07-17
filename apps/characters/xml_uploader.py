from xml.sax.saxutils import quoteattr, unescape
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces, property_lexical_handler
from dateutil.parser import parse
from datetime import datetime, timedelta

from xml.sax import ContentHandler
from xml.sax.saxutils import unescape, escape

from minimock import Mock

from characters.models import Trait, TraitListProperty, Sheet, VampireSheet
from pprint import pprint

from django.db import IntegrityError

from reversion import revision

def translate_date(date):
    if isinstance(date, basestring):
        try:
            dt = datetime.strptime(date, "%m/%d/%Y %H:%M:%S %p")
        except ValueError:
            try:
                dt = datetime.strptime(date, "%m/%d/%Y")
            except ValueError:
                dt = datetime.strptime(date, "%H:%M:%S %p")

        return dt
    else:
        if date.hour == date.minute == date.second == 0:
            return date.strftime("%m/%d/%Y")
        else:
            return date.strftime("%m/%d/%Y %H:%M:%S %p")

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
VAMPIRE_TAG_DATES = ('start_date', 'last_modified')

ENTRY_TAG_RENAMES = {'type':'change_type'}
ENTRY_TAG_DATES = ['date']

TRAIT_TAG_RENAMES = { 'val' : 'value' }

TRAITLIST_TAG_RENAMES = {
    'abc':'sorted',
    'display': 'display_preference',
}

from crapvine.types.vampire import Vampire as CrapvineVampire
from crapvine.xml.trait import TraitList as CrapvineTraitList
from crapvine.xml.trait import Trait as CrapvineTrait
from crapvine.xml.experience import Experience as CrapvineExperience
from crapvine.xml.experience import ExperienceEntry as CrapvineExperienceEntry

class VampireExporter():
    def __init__(self, vampire_sheet):
        self.sheet = vampire_sheet

        vamp_attrs = dict((k, str(v)) for k,v in self.sheet.__dict__.iteritems())
        vamp_attrs['player'] = self.sheet.player.username
        vamp_attrs['npc'] = 'yes' if self.sheet.npc else 'no'
        for date_attribute in VAMPIRE_TAG_DATES:
            vamp_attrs[date_attribute] = translate_date(getattr(self.sheet, date_attribute))
        reversed_map = dict((v, k) for k, v in VAMPIRE_TAG_RENAMES.iteritems())
        map_attributes(reversed_map, vamp_attrs)
        pprint(vamp_attrs)
        self.vampire = CrapvineVampire()
        self.vampire.read_attributes(vamp_attrs)
        pprint(self.vampire.startdate)
        pprint(self.vampire.npc)

        for tlp in self.sheet.get_traitlist_properties():
            tl_attrs = dict((k, str(v)) for k,v in tlp.__dict__.iteritems())
            tl_attrs['name'] = tlp.name.name
            map_attributes(dict((v,k) for k,v in TRAITLIST_TAG_RENAMES.iteritems()), tl_attrs)
            #pprint(tl_attrs)
            ctl = CrapvineTraitList()
            ctl.read_attributes(tl_attrs)

            for t in self.sheet.get_traits(tlp.name.name):
                t_attrs = dict((k, str(v)) for k,v in t.__dict__.iteritems())
                map_attributes(dict((v, k) for k, v in TRAIT_TAG_RENAMES.iteritems()), t_attrs)
                ct = CrapvineTrait()
                ct.read_attributes(t_attrs)
                ctl.add_trait(ct)

            self.vampire.add_traitlist(ctl)

        e = CrapvineExperience()
        e.read_attributes({
            'unspent':str(self.sheet.experience_unspent),
            'earned':str(self.sheet.experience_earned)})

        for ee in self.sheet.experience_entries.all():
            ee_attrs = dict((k, str(v)) for k,v in ee.__dict__.iteritems())
            for date_attribute in ENTRY_TAG_DATES:
                ee_attrs[date_attribute] = translate_date(getattr(ee, date_attribute))
            map_attributes(dict((v, k) for k, v in ENTRY_TAG_RENAMES.iteritems()), ee_attrs)
            cee = CrapvineExperienceEntry()
            cee.read_attributes(ee_attrs)
            e.add_entry(cee)

        self.vampire.add_experience(e)

    def __unicode__(self):
        return self.vampire.get_xml()

    def __str__(self):
        return self.vampire.get_xml()

class VampireLoader(ContentHandler):
    def __init__(self, user):
        self.__user = user

        self.vampires = {}
        self.current_vampire = None

        self.in_cdata = False

        self.current_traitlist = None

        self.reading_biography = False
        self.current_biography = ''

        self.reading_notes = False
        self.current_notes = ''

        self.current_experience = None
        self.last_entry = None

    def add_vampire(self, vamp):
        vamp.update_experience_total()
        vamp.save()
        vamp.add_default_traitlist_properties()
        vamp.save()
        self.vampires[vamp.name] = vamp

    def startElement(self, name, attrs):
        if name == 'vampire':
            if not attrs.has_key('name'):
                return
            my_attrs = dict(attrs)
            map_attributes(VAMPIRE_TAG_RENAMES, my_attrs)
            map_dates(VAMPIRE_TAG_DATES, my_attrs)

            my_attrs['player'] = self.__user
            v = VampireSheet.objects.create(**my_attrs)
            #v.read_attributes(attrs)
            self.current_vampire = v

        elif name == 'experience':
            if self.current_experience:
                raise IOError('Experience encountered while still reading traitlist')
            exp = Mock('Experience')#Experience()
            exp.read_attributes(attrs)
            self.current_experience = exp
            #if self.current_vampire:
            #    self.current_vampire.add_experience(exp)

        elif name == 'entry':
            if not self.current_experience:
                raise IOError('Entry without bounding Experience')
            from pprint import pprint
            my_attrs = dict(attrs)
            map_attributes(ENTRY_TAG_RENAMES, my_attrs)
            map_dates(ENTRY_TAG_DATES, my_attrs)
            if self.last_entry is not None:
                #print self.last_entry.date
                if self.last_entry.date >= my_attrs['date']:
                    #print my_attrs['date']
                    my_attrs['date'] = self.last_entry.date + timedelta(seconds=1)
            try:
                exp = self.current_vampire.experience_entries.create(**my_attrs)
            except IntegrityError, e:
                pprint({'name':name, 'attrs':attrs, 'my_attrs':my_attrs})
                raise e

            self.last_entry = exp

        elif name == 'biography':
            self.reading_biography = True

        elif name == 'notes':
            self.reading_notes = True

        elif name == 'traitlist':
            if self.current_traitlist:
                raise IOError('TraitList encountered while still reading traitlist')
            my_attrs = dict(attrs)
            map_attributes(TRAITLIST_TAG_RENAMES, my_attrs)
            self.current_vampire.add_traitlist_properties(**my_attrs)
            self.current_traitlist = attrs
            #if self.current_vampire:
            #    self.current_vampire.add_traitlist(tl)

        elif name == 'trait':
            if not self.current_traitlist:
                raise IOError('Trait without bounding traitlist')
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
            my_attrs['display_preference'] = self.current_traitlist['display']
            self.current_vampire.add_trait(self.current_traitlist['name'], my_attrs)

    def endElement(self, name):
        if name == 'vampire':
            assert self.current_vampire
            self.add_vampire(self.current_vampire)
            self.current_vampire = None

        elif name == 'experience':
            assert self.current_experience
            self.current_experience = None

        elif name == 'traitlist':
            assert self.current_traitlist
            self.current_traitlist = None

        elif name == 'biography':
            assert self.reading_biography
            self.reading_biography = False
            if self.current_vampire:
                self.current_vampire.biography = unescape(self.current_biography)
                #print self.current_biography
            self.current_biography = ''

        elif name == 'notes':
            assert self.reading_notes
            self.reading_notes = False
            if self.current_vampire:
                self.current_vampire.notes = unescape(self.current_notes)
                #print self.current_notes
            self.current_notes = ''

    def characters(self, ch):
        if self.reading_biography and self.in_cdata:
            self.current_biography += ch
        elif self.reading_notes and self.in_cdata:
            self.current_notes += ch

    def ignorableWhitespace(self, space):
        pass

    def startCDATA(self):
        self.in_cdata = True
    def endCDATA(self):
        self.in_cdata = False

    def startDTD(self):
        pass
    def endDTD(self):
        pass
    def comment(self, text):
        pass

    def error(self, exception):
        print 'Error'
        raise exception
    def fatalError(self, exception):
        print 'Fatal Error'
        raise exception
    def warning(self, exception):
        print 'Warning'
        raise exception

class ChronicleLoader(ContentHandler):
    creatures_elements = ['vampire']
    def __init__(self, user):
        self.__user = user

        self.chronicle = None
        self.in_cdata = False

        self.reading_description = False
        self.current_description = ''

        self.reading_usualplace = False
        self.current_usualplace = ''

        self.creatures = {}
        self.reading_creature = ''
        self.creatures['vampire'] = VampireLoader(self.__user)

    @property
    def vampires(self):
        if self.creatures['vampire']:
            return self.creatures['vampire'].vampires
        return None

    def startElement(self, name, attrs):
        if self.reading_creature:
            if self.creatures[self.reading_creature]:
                self.creatures[self.reading_creature].startElement(name, attrs)
            return
        if name in self.creatures_elements:
            self.reading_creature = name
            if self.creatures[name]:
                self.creatures[name].startElement(name, attrs)
            return

        if name == 'grapevine':
            chron = Mock('Chronicle')#Chronicle()
            chron.read_attributes(attrs)
            self.chronicle = chron

        elif name == 'usualplace':
            self.reading_usualplace = True

        elif name == 'description':
            self.reading_description = True

    def endElement(self, name):
        if self.reading_creature:
            if self.creatures[self.reading_creature]:
                self.creatures[self.reading_creature].endElement(name)
            return
        if name in self.creatures_elements:
            assert self.reading_creature
            self.reading_creature = ''
            if self.creatures[name]:
                self.creatures[name].endElement(name)
            return

        if name == 'grapevine':
            assert self.chronicle

        elif name == 'usualplace':
            assert self.reading_usualplace
            self.reading_usualplace = False
            if self.chronicle:
                self.chronicle['usualplace'] = unescape(self.current_usualplace)
            self.current_usualplace = ''

        elif name == 'description':
            assert self.reading_description
            self.reading_description = False
            if self.chronicle:
                self.chronicle['description'] = unescape(self.current_description)
            self.current_description = ''

    def characters(self, ch):
        if self.reading_creature:
            if self.creatures[self.reading_creature]:
                self.creatures[self.reading_creature].characters(ch)
            return

        if self.reading_usualplace and self.in_cdata:
            self.current_usualplace += ch
        if self.reading_description and self.in_cdata:
            self.current_description += ch

    def ignorableWhitespace(self, space):
        pass

    def startCDATA(self):
        if self.reading_creature:
            if self.creatures[self.reading_creature]:
                self.creatures[self.reading_creature].startCDATA()
            return
        self.in_cdata = True
    def endCDATA(self):
        if self.reading_creature:
            if self.creatures[self.reading_creature]:
                self.creatures[self.reading_creature].endCDATA()
            return
        self.in_cdata = False

    def startDTD(self):
        pass
    def endDTD(self):
        pass
    def comment(self, text):
        pass


    def error(self, exception):
        print 'Error'
        raise exception
    def fatalError(self, exception):
        print 'Fatal Error'
        raise exception
    def warning(self, exception):
        print 'Warning'
        raise exception

#from crapvine.xml.chronicle_loader import ChronicleLoader

@revision.create_on_success
def handle_sheet_upload(uploaded_file, user):
    chronicle_loader = ChronicleLoader(user)

    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    parser.setContentHandler(chronicle_loader)
    parser.setProperty(property_lexical_handler, chronicle_loader)
    parser.parse(uploaded_file)

    return chronicle_loader
