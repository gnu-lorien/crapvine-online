from django.test import TestCase
from characters.models import Trait, TraitList, Sheet, TraitListName, VampireSheet, ExperienceEntry
from django.contrib.auth.models import User

from pprint import pprint

import os

from django.db.models import get_apps
from xml_uploader import handle_sheet_upload

from crapvine.xml.experience import ExperienceEntry
from copy import deepcopy

# TODO: Test that ExperienceEntry import order is maintained properly

class ImportTestCase(TestCase):
    fixtures = ['players']

    def setUp(self):
        loadfn = 'mcmillan.gex'
        self.user = User.objects.get(username__exact='Andre')

        app_fixtures = [os.path.join(os.path.dirname(app.__file__), 'fixtures') for app in get_apps()]
        for app_fixture in app_fixtures:
            if os.path.exists(os.path.join(app_fixture, loadfn)):
                with open(os.path.join(app_fixture, loadfn), 'r') as fp:
                    handle_sheet_upload(fp, self.user)

    def testMcMillan(self):
        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')
        entries = self.sheet.experience_entries.all().order_by('date')
        #for ee in entries:
        #    #grapevine_ee = ExperienceEntry(reason=ee.reason,
        #    #                              change=ee.change,
        #    #                              type=ee.change_type,
        #    #                              earned=ee.earned,
        #    #                              unspent=ee.unspent,
        #    #                              date=ee.date)
        #    grapevine_ee = ExperienceEntry()
        #    grapevine_ee.read_attributes(dict((k, str(v)) for k,v in ee.__dict__.iteritems()))
        #    print grapevine_ee
        self.assertEquals(entries[1].change, 2)
        self.assertEquals(entries[2].change, 0.5)
        self.assertEquals(entries[1].reason, "Attendance")
        self.assertEquals(entries[2].reason, "Workshop")

        self.assertEquals(self.sheet.experience_unspent, 29)
        self.assertEquals(self.sheet.experience_earned, 390)

    def testExperienceOrdering(self):
        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')
        erf = [e.reason for e in self.sheet.experience_entries.all().order_by('date')]
        err = [e.reason for e in self.sheet.experience_entries.all().order_by('-date')]
        for i, reasons in enumerate(zip(erf, reversed(err))):
            self.assertEquals(reasons[0], reasons[1])
        self.assertEquals(erf, list(reversed(err)))

    def testExperienceAdd(self):
        self.imported_sheet = Sheet.objects.get(name__exact='Charles McMillan')
        self.sheet = Sheet.objects.create(
            name='Michele',
            player=self.user)
        for entry in self.imported_sheet.experience_entries.all().order_by('date'):
            copied_entry = deepcopy(entry)
            copied_entry.id = None
            copied_entry.earned = 0
            copied_entry.unspent = 0
            #print "(", entry.unspent, ",", entry.earned, ") ->", entry.change_type
            #print "(", copied_entry.unspent, ",", copied_entry.earned, ") ->", entry.change_type
            self.sheet.add_experience_entry(copied_entry)
            #for ee in self.sheet.experience_entries.all().order_by('date'):
            #    grapevine_ee = ExperienceEntry()
            #    grapevine_ee.read_attributes(dict((k, str(v)) for k,v in ee.__dict__.iteritems()))
            #    print grapevine_ee
            #grapevine_ee = ExperienceEntry()
            #grapevine_ee.read_attributes(dict((k, str(v)) for k,v in entry.__dict__.iteritems()))
            #print grapevine_ee

            #print "(", that_entry.unspent, ",", that_entry.earned, ") ->", entry.change_type
            that_entry = self.sheet.experience_entries.all().order_by('-date')[0]
            self.assertEquals(entry.unspent, that_entry.unspent)
            self.assertEquals(entry.earned, that_entry.earned)

        erf = [e.reason for e in self.sheet.experience_entries.all().order_by('date')]
        err = [e.reason for e in self.sheet.experience_entries.all().order_by('-date')]
        self.assertEquals(erf, list(reversed(err)), "Reversal of the experience entries is not identical")

        self.assertEquals(self.sheet.experience_unspent, 29)
        self.assertEquals(self.sheet.experience_earned, 390)

class CharactersTestCase(TestCase):
    def _build_trait(self, name, value, note):
        return Trait.objects.create(name=name, value=value, note=note)

    def _build_traitlist(self, name, sheet, traits):
        trait_objs = [self._build_trait(*args) for args in traits]
        traitlist_name = TraitListName.objects.get(name__exact=name)
        for i, trait in enumerate(trait_objs):
            TraitList.objects.create(sheet=sheet, trait=trait, display_order=i, name=traitlist_name)
        return trait_objs

    def _build_traitlist_randomize(self, name, sheet, traits):
        import random
        random.shuffle(traits)
        return self._build_traitlist(name, sheet, traits)

class SheetTestCase(CharactersTestCase):
    fixtures = ['players']

    def _assertNamedTraitInList(self, trait_name, traitlist_name):
        self.failIf(trait_name not in [trait.name for trait in self.sheet.get_traitlist(traitlist_name)])
    def _assertNamedTraitNotInList(self, trait_name, traitlist_name):
        self.failIf(trait_name in [trait.name for trait in self.sheet.get_traitlist(traitlist_name)])


    def setUp(self):
        self.andrew_player = User.objects.get(username__exact='Andre')
        self.sheet = Sheet.objects.create(
            name='Michele',
            player=self.andrew_player)
        self.trait = Trait.objects.create(name='Vivox')
        self.tl = TraitList.objects.create(sheet=self.sheet, trait=self.trait, display_order=1, name=TraitListName.objects.get(name__exact='Physical'))

    def testCreateTraitList(self):
        tl = self._build_traitlist_randomize('Social', self.sheet,[
            ('dummy', 3, ''),
            ('aoeu', 2, 'frilel'),
            ('nothing', 5, 'hate')])
        self._assertNamedTraitNotInList('Vivox', 'Social')
        self._assertNamedTraitInList('dummy', 'Social')
        self._assertNamedTraitInList('aoeu', 'Social')
        self._assertNamedTraitInList('nothing', 'Social')

    def testStrangeTraitValues(self):
        t = Trait.objects.create(name='Weird ness', value='1 or 2')
        t = Trait.objects.create(name='Weird ness', value='1-2')

    def testAddingTraits(self):
        #self.sheet.add_trait('Mental', 'Determined')
        #self.sheet.add_trait('Mental', 'Insidious', value=2)
        #self.sheet.add_trait('Mental', 'Perceptive', value=5, note='Cars')
        t = Trait.objects.create(name='Fuckness')
        self.sheet.add_trait('Mental', t)
        #pprint(dir(self.sheet.get_traitlist('Mental')))
        #self.sheet.get_traitlist('Mental')[0].display_order

        #self._assertNamedTraitInList('Determined', 'Mental')
        #self._assertNamedTraitInList('Insidious', 'Mental')
        #self._assertNamedTraitInList('Perceptive', 'Mental')
        self._assertNamedTraitInList('Fuckness', 'Mental')

    def testInsertTraits(self):
        t = Trait.objects.create(name='Fuckness')
        self.sheet.add_trait('Mental', t)
        t = Trait.objects.create(name='Preloaded')
        self.sheet.insert_trait('Mental', t, 0)
        self.assertEquals('Preloaded', self.sheet.get_traitlist('Mental')[0].name)
        self.assertEquals('Fuckness', self.sheet.get_traitlist('Mental')[1].name)

    def testReorderTraitlist(self):
        names = ['a', 'b', 'c', 'd', 'e']
        for name in names:
            t = Trait.objects.create(name=name)
            self.sheet.add_trait('Mental', t)

        self.sheet.reorder_traits('Mental', names)
        traitlist = self.sheet.get_traitlist('Mental')
        for i in xrange(len(traitlist)):
            self.assertEquals(names[i], traitlist[i].name)

        import random
        random.shuffle(names)
        self.sheet.reorder_traits('Mental', names)
        traitlist = self.sheet.get_traitlist('Mental')
        for i in xrange(len(traitlist)):
            self.assertEquals(names[i], traitlist[i].name)

    def testTraitRules(self):
        try:
            t1 = Trait.objects.create(name='CockSmap')
            self.sheet.add_trait('Mental', t1)
            self.sheet.add_trait('Social', t1)
        except ValidationError:
            return
        raise AssertionError

    def testAddExperienceEntry(self):
        entry = ExperienceEntry.objects.create(reason="Test reason",
                                               change=3.4,
                                               change_type=0,
                                               earned=3.4,
                                               unspent=0)
        self.sheet.add_experience_entry(entry)
        retEntry = self.sheet.experience_entries.all()
        self.assertEquals(entry, retEntry[0])
        self.assertEquals(entry.change, retEntry[0].change)

class VampireSheetTestCase(SheetTestCase):
    def setUp(self):
        SheetTestCase.setUp(self)
        self.vampire = VampireSheet.objects.create(
            name='BloodNess',
            player=self.andrew_player)

class TraitTestCase(CharactersTestCase):
    def __myAssertEqual(self, given, expected, extra):
        try:
            self.assertEqual(given, expected)
        except Exception, e:
            from pprint import pprint
            pprint(extra)
            raise e

    def testDisplay(self):
        fully_tested = {
            self._build_trait('Example', 3, 'Carlsbad') :
                {
                    '0' : 'Example',
                    '1' : 'Example x3 (Carlsbad)',
                    '2' : 'Example x3 OOO (Carlsbad)',
                    '3' : 'Example OOO (Carlsbad)',
                    '4' : 'Example (3, Carlsbad)',
                    '5' : 'Example (Carlsbad)',
                    '6' : 'Example (3)',
                    '7' : 'Example (Carlsbad)OExample (Carlsbad)OExample (Carlsbad)',
                    '8' : 'OOO',
                    '9' : '3'
                },
            self._build_trait('Example', 3, '') :
                {
                    '0' : 'Example',
                    '1' : 'Example x3',
                    '2' : 'Example x3 OOO',
                    '3' : 'Example OOO',
                    '4' : 'Example (3)',
                    '5' : 'Example',
                    '6' : 'Example (3)',
                    '7' : 'ExampleOExampleOExample',
                    '8' : 'OOO',
                    '9' : '3',
                },
            self._build_trait('Example', 0, '') :
                {
                    '0' : 'Example',
                    '1' : 'Example',
                    '2' : 'Example',
                    '3' : 'Example',
                    '4' : 'Example',
                    '5' : 'Example',
                    '6' : 'Example',
                    '7' : 'Example',
                    '8' : '',
                    '9' : '',
                },
            self._build_trait('Example', 0, 'Carlsbad') :
                {
                    '0' : 'Example',
                    '1' : 'Example (Carlsbad)',
                    '2' : 'Example (Carlsbad)',
                    '3' : 'Example (Carlsbad)',
                    '4' : 'Example (Carlsbad)',
                    '5' : 'Example (Carlsbad)',
                    '6' : 'Example',
                    '7' : 'Example (Carlsbad)',
                    '8' : '',
                    '9' : '',
                }
        }
        from pprint import pprint
        for trait, test_list in fully_tested.iteritems():
            for display_type, expected_result in test_list.iteritems():
                extra = {'display_type': display_type, 'name':trait.name, 'value':trait.value, 'note':trait.note}
                trait.display_preference = int(display_type)
                self.__myAssertEqual(trait.__unicode__(), expected_result, extra)
