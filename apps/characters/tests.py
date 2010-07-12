from django.test import TestCase
from django.test.client import Client
from characters.models import Trait, TraitListProperty, Sheet, TraitListName, VampireSheet, ExperienceEntry
from django.contrib.auth.models import User

from pprint import pprint

import os

from django.db.models import get_apps
from xml_uploader import handle_sheet_upload, VampireExporter

from crapvine.xml.experience import ExperienceEntry as CrapvineExperienceEntry
from copy import deepcopy

import django.db.models.fields

from characters.permissions import SheetPermission

import StringIO

# TODO: Test that ExperienceEntry import order is maintained properly
# TODO: Test for escape/unescape/quoteattr side-effects
# TODO: Look more closely at how we import and export display values to grapevine xml

class ExperienceEntriesTestCase(TestCase):
    fixtures = ['players']

    def setUp(self):
        loadfn = 'mcmillan.gex'
        self.user = User.objects.get(username__exact='Andre')

        app_fixtures = [os.path.join(os.path.dirname(app.__file__), 'fixtures') for app in get_apps()]
        for app_fixture in app_fixtures:
            if os.path.exists(os.path.join(app_fixture, loadfn)):
                with open(os.path.join(app_fixture, loadfn), 'r') as fp:
                    handle_sheet_upload(fp, self.user)

        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')

    def testSimpleEndEdit(self):
        last_entry = self.sheet.experience_entries.order_by('-date')[0]
        self.assertEqual(last_entry.unspent, self.sheet.experience_unspent)
        self.assertEqual(last_entry.earned, self.sheet.experience_earned)

        prev_unspent = last_entry.unspent
        prev_earned = last_entry.earned
        adding = 10
        last_entry.change = last_entry.change + adding
        last_entry.save()
        self.sheet.edit_experience_entry(last_entry)
        last_entry = self.sheet.experience_entries.order_by('-date')[0]

        self.assertNotEqual(prev_unspent, last_entry.unspent)
        self.assertNotEqual(prev_earned, last_entry.earned)
        self.assertEqual(prev_unspent + adding, last_entry.unspent)
        self.assertEqual(prev_earned + adding, last_entry.earned)

        self.assertEqual(last_entry.unspent, self.sheet.experience_unspent)
        self.assertEqual(last_entry.earned, self.sheet.experience_earned)

    def testSimpleEndDelete(self):
        last_entry = self.sheet.experience_entries.order_by('-date')[0]
        prev_entry = last_entry.get_previous_by_date()

        self.assertEqual(last_entry.unspent, self.sheet.experience_unspent)
        self.assertEqual(last_entry.earned, self.sheet.experience_earned)

        self.sheet.delete_experience_entry(last_entry)
        self.assertEqual(prev_entry.unspent, self.sheet.experience_unspent)
        self.assertEqual(prev_entry.earned, self.sheet.experience_earned)

    def testMiddleDelete(self):
        set_unspent_entry = self.sheet.experience_entries.filter(change_type__exact=5).order_by('-date')[0]
        target_entry = set_unspent_entry.get_next_by_date()

        start_unspent = self.sheet.experience_unspent
        start_earned = self.sheet.experience_earned

        print target_entry

        self.sheet.delete_experience_entry(target_entry)

        pprint(locals())
        self.assertEqual(start_unspent - 2, self.sheet.experience_unspent)
        self.assertEqual(start_earned - 2, self.sheet.experience_earned)

    def testMiddleEdit(self):
        set_unspent_entry = self.sheet.experience_entries.filter(change_type__exact=5).order_by('-date')[0]
        target_entry = set_unspent_entry.get_next_by_date()

        start_unspent = self.sheet.experience_unspent
        start_earned = self.sheet.experience_earned

        print target_entry
        adding = 10
        target_entry.change = target_entry.change + adding
        target_entry.save()
        self.sheet.edit_experience_entry(target_entry)

        pprint(locals())
        self.assertEqual(start_unspent + adding, self.sheet.experience_unspent)
        self.assertEqual(start_earned + adding, self.sheet.experience_earned)

class PageViewPermissionsTestCase(TestCase):
    fixtures = ['double_upload']

    def testProperView(self):
        logged_in = self.client.login(username='lorien', password='lorien')
        self.assertTrue(logged_in)
        response = self.client.get("/characters/list_sheet/2/")
        self.assertEqual(response.status_code, 200)

    def testNoLoginView(self):
        response = self.client.get("/characters/list_sheet/1/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["location"], "http://testserver/account/login/?next=/characters/list_sheet/1/")

    def testUnauthorizedView(self):
        logged_in = self.client.login(username='perpet', password='lorien')
        response = self.client.get("/characters/list_sheet/2/")
        self.assertEqual(response.status_code, 403)

    def testNewSheetView(self):
        loadfn = 'adamstcharles.gex'
        c = Client()
        self.assertTrue(c.login(username='perpet', password='lorien'))
        app_fixtures = [os.path.join(os.path.dirname(app.__file__), 'fixtures') for app in get_apps()]
        for app_fixture in app_fixtures:
            if os.path.exists(os.path.join(app_fixture, loadfn)):
                with open(os.path.join(app_fixture, loadfn), 'r') as f:
                    c.post("/characters/upload_sheet/",
                           {'title': 'whocares',
                            'file': f,
                            'action': 'upload'})
        response = c.get("/characters/list_sheet/3/")
        self.assertEqual(response.status_code, 200, "perpet should be able to access his sheets")

        self.assertTrue(self.client.login(username='lorien', password='lorien'))
        response = self.client.get("/characters/list_sheet/3/")
        self.assertEqual(response.status_code, 403, "lorien should not be able to access perpet's sheets")


class ExportTestCase(TestCase):
    fixtures = ['players']

    def setUp(self):
        loadfn = 'mcmillan.gex'
        self.user = User.objects.get(username__exact='Andre')

        app_fixtures = [os.path.join(os.path.dirname(app.__file__), 'fixtures') for app in get_apps()]
        for app_fixture in app_fixtures:
            if os.path.exists(os.path.join(app_fixture, loadfn)):
                with open(os.path.join(app_fixture, loadfn), 'r') as fp:
                    handle_sheet_upload(fp, self.user)


    def testModelLooks(self):
        print dir(ExperienceEntry._meta)
        print ExperienceEntry._meta.get_fields_with_model()
        for fn in ExperienceEntry._meta.get_all_field_names():
            print fn, ExperienceEntry._meta.get_field_by_name(fn)[0]
            #if not isinstance(ExperienceEntry._meta.get_field_by_name(fn)[0], django.db.models.fields.AutoField):
            #    print fn

    def testExportEquivalence(self):
        vampire_sheet = VampireSheet.objects.get(name__exact='Charles McMillan')
        vampire_sheet.name = "Suckon Deez Nuts"
        ve = VampireExporter(vampire_sheet)
        print ve
        sf = StringIO.StringIO(unicode(ve))
        handle_sheet_upload(sf, self.user)

        new_sheet = VampireSheet.objects.get(name__exact='Suckon Deez Nuts')

        # Vampire base attributes
        self.assertEquals(new_sheet.nature, vampire_sheet.nature)
        self.assertEquals(new_sheet.demeanor, vampire_sheet.demeanor)
        self.assertEquals(new_sheet.blood, vampire_sheet.blood)
        self.assertEquals(new_sheet.clan, vampire_sheet.clan)
        self.assertEquals(new_sheet.conscience, vampire_sheet.conscience)
        self.assertEquals(new_sheet.courage, vampire_sheet.courage)
        self.assertEquals(new_sheet.generation, vampire_sheet.generation)
        self.assertEquals(new_sheet.path, vampire_sheet.path)
        self.assertEquals(new_sheet.pathtraits, vampire_sheet.pathtraits)
        self.assertEquals(new_sheet.physicalmax, vampire_sheet.physicalmax)
        self.assertEquals(new_sheet.sect, vampire_sheet.sect)
        self.assertEquals(new_sheet.selfcontrol, vampire_sheet.selfcontrol)
        self.assertEquals(new_sheet.willpower, vampire_sheet.willpower)
        self.assertEquals(new_sheet.title, vampire_sheet.title)
        self.assertEquals(new_sheet.aura, vampire_sheet.aura)
        self.assertEquals(new_sheet.coterie, vampire_sheet.coterie)
        self.assertEquals(new_sheet.id_text, vampire_sheet.id_text)
        self.assertEquals(new_sheet.sire, vampire_sheet.sire)
        self.assertEquals(new_sheet.tempcourage, vampire_sheet.tempcourage)
        self.assertEquals(new_sheet.tempselfcontrol, vampire_sheet.tempselfcontrol)
        self.assertEquals(new_sheet.tempwillpower, vampire_sheet.tempwillpower)
        self.assertEquals(new_sheet.tempblood, vampire_sheet.tempblood)
        self.assertEquals(new_sheet.tempconscience, vampire_sheet.tempconscience)
        self.assertEquals(new_sheet.temppathtraits, vampire_sheet.temppathtraits)

        # Sheet base attributes
        self.assertEquals(new_sheet.home_chronicle, vampire_sheet.home_chronicle)
        self.assertEquals(new_sheet.start_date, vampire_sheet.start_date)
        self.assertEquals(new_sheet.last_modified, vampire_sheet.last_modified)
        self.assertEquals(new_sheet.npc, vampire_sheet.npc)
        self.assertEquals(new_sheet.notes, vampire_sheet.notes)
        self.assertEquals(new_sheet.biography, vampire_sheet.biography)
        self.assertEquals(new_sheet.status, vampire_sheet.status)
        self.assertEquals(new_sheet.experience_unspent, vampire_sheet.experience_unspent)
        self.assertEquals(new_sheet.experience_earned, vampire_sheet.experience_earned)

        left_traits = new_sheet.traits.all().order_by('traitlistname__name', 'order')
        right_traits = vampire_sheet.traits.all().order_by('traitlistname__name', 'order')
        for left, right in zip(left_traits, right_traits):
            self.assertEquals(left.value, right.value)
            self.assertEquals(left.note, right.note)
            self.assertEquals(left.name, right.name)

        left_entries = new_sheet.experience_entries.all()
        right_entries = vampire_sheet.experience_entries.all()
        for left, right in zip(left_entries, right_entries):
            self.assertEquals(left.reason, right.reason)
            self.assertEquals(left.change, right.change)
            self.assertEquals(left.change_type, right.change_type)
            self.assertEquals(left.earned, right.earned)
            self.assertEquals(left.unspent, right.unspent)
            self.assertEquals(left.date, right.date)

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
        #    #grapevine_ee = CrapvineExperienceEntry(reason=ee.reason,
        #    #                              change=ee.change,
        #    #                              type=ee.change_type,
        #    #                              earned=ee.earned,
        #    #                              unspent=ee.unspent,
        #    #                              date=ee.date)
        #    grapevine_ee = CrapvineExperienceEntry()
        #    grapevine_ee.read_attributes(dict((k, str(v)) for k,v in ee.__dict__.iteritems()))
        #    print grapevine_ee
        self.assertEquals(entries[1].change, 2)
        self.assertEquals(entries[2].change, 0.5)
        self.assertEquals(entries[1].reason, "Attendance")
        self.assertEquals(entries[2].reason, "Workshop")

        self.assertEquals(self.sheet.experience_unspent, 29)
        self.assertEquals(self.sheet.experience_earned, 390)

    def testExperienceReversing(self):
        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')
        erf = [e.reason for e in self.sheet.experience_entries.all().order_by('date')]
        err = [e.reason for e in self.sheet.experience_entries.all().order_by('-date')]
        for i, reasons in enumerate(zip(erf, reversed(err))):
            self.assertEquals(reasons[0], reasons[1])
        self.assertEquals(erf, list(reversed(err)))

    def testExperienceOrdering(self):
        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')
        erf = [e.reason for e in self.sheet.experience_entries.all().order_by('date')]
        err = [e.reason for e in self.sheet.experience_entries.all()]
        for i, reasons in enumerate(zip(erf, err)):
            self.assertEquals(reasons[0], reasons[1])
        self.assertEquals(erf, err)

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
            #    grapevine_ee = CrapvineExperienceEntry()
            #    grapevine_ee.read_attributes(dict((k, str(v)) for k,v in ee.__dict__.iteritems()))
            #    print grapevine_ee
            #grapevine_ee = CrapvineExperienceEntry()
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
            player=self.andrew_player,
            blood=10,
            conscience=4,
            courage=2,
            selfcontrol=3,
            generation=12,
            pathtraits=3,
            physicalmax=10,
            willpower=3)

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
