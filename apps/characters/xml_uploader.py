from xml.sax.saxutils import unescape
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces, property_lexical_handler
import xml.etree.ElementTree as etree
from xml.dom.minidom import parse
from django.db import transaction
from datetime import datetime
from django.db import IntegrityError

from xml.sax import ContentHandler

from minimock import Mock

from pprint import pprint

from reversion import revision

from uploader import create_base_vampire, read_experience_entry, read_traitlist_properties, read_trait

from crapvine.types.vampire import Vampire as CrapvineVampire
from crapvine.xml.trait import TraitList as CrapvineTraitList
from crapvine.xml.trait import Trait as CrapvineTrait
from crapvine.xml.experience import Experience as CrapvineExperience
from crapvine.xml.experience import ExperienceEntry as CrapvineExperienceEntry

class VampireExporter():
    def __init__(self, vampire_sheet):
        from uploader import VAMPIRE_TAG_DATES, VAMPIRE_TAG_RENAMES
        from uploader import TRAIT_TAG_RENAMES
        from uploader import TRAITLIST_TAG_RENAMES
        from uploader import ENTRY_TAG_DATES, ENTRY_TAG_RENAMES
        from uploader import translate_date, map_attributes

        self.sheet = vampire_sheet

        vamp_attrs = dict((k, str(v)) for k,v in self.sheet.__dict__.iteritems())
        vamp_attrs.update((k, str(v)) for k,v in self.sheet.vampiresheet.__dict__.iteritems())
        vamp_attrs['player'] = self.sheet.player.username
        vamp_attrs['npc'] = 'yes' if self.sheet.npc else 'no'
        vamp_attrs['name'] = self.sheet.name
        for date_attribute in VAMPIRE_TAG_DATES:
            vamp_attrs[date_attribute] = translate_date(getattr(self.sheet, date_attribute))
        reversed_map = dict((v, k) for k, v in VAMPIRE_TAG_RENAMES.iteritems())
        map_attributes(reversed_map, vamp_attrs)
        #pprint(vamp_attrs)
        self.vampire = CrapvineVampire()
        self.vampire.read_attributes(vamp_attrs)
        #pprint(self.vampire.startdate)
        #pprint(self.vampire.npc)

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
        return "<?xml version=\"1.0\"?>\n<grapevine version=\"3\">\n%s\n</grapevine>" % (self.vampire.get_xml(indent='  '))

    def __str__(self):
        return "<?xml version=\"1.0\"?>\n<grapevine version=\"3\">\n%s\n</grapevine>" % (self.vampire.get_xml(indent='  '))

def get_date_hint(dom):
    date_strings = set()
    results = {'day':0, 'month':0}
    for v in dom.getElementsByTagName('vampire'):
        top_dates = 'startdate', 'lastmodified'
        for td in top_dates:
            if v.attributes.has_key(td):
                date_strings.add(v.getAttribute(td))

        for v_child in v.childNodes:
            if v_child.nodeName == 'experience':
                for exp_child in v_child.childNodes:
                    if exp_child.nodeName == 'entry':
                        if exp_child.attributes.has_key('date'):
                            date_strings.add(exp_child.getAttribute('date'))

        from uploader import DAY_FIRST_TRANSLATIONS, MONTH_FIRST_TRANSLATIONS

        for date in date_strings:
            ddt = None
            for format in DAY_FIRST_TRANSLATIONS:
                try:
                    ddt = datetime.strptime(date, format)
                    break
                except ValueError:
                    pass
            if ddt is not None:
                results['day'] += 1

            mdt = None
            for format in MONTH_FIRST_TRANSLATIONS:
                try:
                    mdt = datetime.strptime(date, format)
                    break
                except ValueError:
                    pass
            if mdt is not None:
                results['month'] += 1

            if ddt is None and mdt is None:
                raise ValueError("Could not convert %s to a proper date" % date)
        print results

    print results
    if results['day'] > results['month']:
        return 'day'
    else:
        return 'month'

def read_vampire(v, user, date_hint):
    vampire = {}
    previous_entry = None

    current_vampire = create_base_vampire(v._attrs, user, date_hint=date_hint)

    for v_child in v.childNodes:
        if v_child.nodeName == 'traitlist':
            tl = v_child
            read_traitlist_properties(tl._attrs, current_vampire)
            order = 0
            for tl_child in tl.childNodes:
                if tl_child.nodeName == 'trait':
                    t = tl_child
                    order += 1
                    read_trait(t._attrs, tl._attrs, current_vampire)

    exp = v.find('experience')
    for ee in exp.findall('entry'):
        previous_entry = read_experience_entry(ee.attrib, current_vampire, previous_entry, date_hint=date_hint)

    biography = v.find('biography')
    if biography is not None:
        current_vampire.biography = unescape(biography.text).strip()

    notes = v.find('notes')
    if notes is not None:
        current_vampire.notes = unescape(notes.text).strip()

    current_vampire.update_experience_total()
    current_vampire.save()
    current_vampire.add_default_traitlist_properties()
    return current_vampire

def base_read(f, user):
    dom = parse(f)
    creatures = []
    date_hint = get_date_hint(dom)
    for v in dom.getElementsByTagName('vampire'):
        creatures.append(read_vampire(v, user, date_hint))

    return creatures

class UploadResponse(object):
    pass

#from crapvine.xml.chronicle_loader import ChronicleLoader
@transaction.commit_on_success
@revision.create_on_success
def handle_sheet_upload(uploaded_file, user):
    ret = UploadResponse()
    ret.vampires = {}
    creatures = base_read(uploaded_file, user)
    for c in creatures:
        ret.vampires[c.name] = c

    return ret
