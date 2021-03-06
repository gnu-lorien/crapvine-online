from __future__ import with_statement
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from apps.characters.tests.upload_helpers import upload_sheet_for_username
from apps.crapvine.xml.trait import TraitList
from experience import ExperienceEntriesTestCase, RecentExpenditures
from external import Export, Import, ChronicleCompare, ChronicleUpload

from django.test import TestCase
from django.test.client import Client
from characters.models import Trait, Sheet, TraitListName, VampireSheet, ExperienceEntry
from chronicles.models import Chronicle
from django.contrib.auth.models import User

from upload_helpers import upload_sheet_for_user

from pprint import pprint

import os
from upload_helpers import get_fixture_path_gen

# TODO: Test that ExperienceEntry import order is maintained properly
# TODO: Test for escape/unescape/quoteattr side-effects
# TODO: Look more closely at how we import and export display values to grapevine xml

class StorytellerViewSheetsTestCase(TestCase):
    fixtures = ['chron_test_00']

    def setUp(self):
        """
        as hst
        create testi
        as 3rdparty create
        whocares
        as play
        create suck my who cares
        associate with whocares
        create ballsplaya
        associate with testi
        """
        chronicle = Chronicle.objects.get(name="testi")
        s = Sheet.objects.get(slug='play-ballsplaya')
        chronicle.associate(s)
        s.save()

        chronicle = Chronicle.objects.get(name="whocares")
        s = Sheet.objects.get(slug='play-suck-my-who-cares')
        chronicle.associate(s)
        s.save()

    def test3rdPartyViewSheet(self):
        """login as 3rdparty and try to view play-suck-my-who-cares"""
        logged_in = self.client.login(username='3rdparty', password='3rdparty')
        response = self.client.get("/characters/list_sheet/play-suck-my-who-cares/")
        self.assertEqual(response.status_code, 200)

    def testHstViewSheet(self):
        """login as hst and try to view play-ballsplaya"""
        logged_in = self.client.login(username='hst', password='hst')
        response = self.client.get("/characters/list_sheet/play-ballsplaya/")
        self.assertEqual(response.status_code, 200)

class PageViewPermissionsTestCase(TestCase):
    fixtures = ['double_upload']

    def setUp(self):
        upload_sheet_for_username('mcmillan.gex', 'lorien')
        upload_sheet_for_username('valueforeverything.gex', 'perpet')

    def testProperView(self):
        logged_in = self.client.login(username='lorien', password='lorien')
        self.assertTrue(logged_in)
        response = self.client.get("/characters/list_sheet/lorien-charles-mcmillan/")
        self.assertEqual(response.status_code, 200)

    def testNoLoginView(self):
        response = self.client.get("/characters/list_sheet/lorien-charles-mcmillan/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["location"], "http://testserver/account/login/?next=/characters/list_sheet/lorien-charles-mcmillan/")

    def testUnauthorizedView(self):
        logged_in = self.client.login(username='perpet', password='lorien')
        response = self.client.get("/characters/list_sheet/lorien-charles-mcmillan/")
        self.assertEqual(response.status_code, 403)

    def testNewSheetView(self):
        loadfn = 'adamstcharles.gex'
        c = Client()
        self.assertTrue(c.login(username='perpet', password='lorien'))
        for app_fixture in get_fixture_path_gen():
            if os.path.exists(os.path.join(app_fixture, loadfn)):
                with open(os.path.join(app_fixture, loadfn), 'r') as f:
                    c.post("/characters/upload_sheet/",
                           {'title': 'whocares',
                            'file': f,
                            'action': 'upload'})
        response = c.get("/characters/list_sheet/perpet-adam-st-charles/")
        self.assertEqual(response.status_code, 200, "perpet should be able to access his sheets")

        self.assertTrue(self.client.login(username='lorien', password='lorien'))
        response = self.client.get("/characters/list_sheet/perpet-adam-st-charles/")
        self.assertEqual(response.status_code, 403, "lorien should not be able to access perpet's sheets")




class CharactersTestCase(TestCase):
    def _build_traitlist(self, name, sheet, traits):
        for t in traits:
            sheet.add_trait(name, {'name':t[0], 'value':t[1], 'note':t[2]})

    def _build_traitlist_randomize(self, name, sheet, traits):
        import random
        random.shuffle(traits)
        self._build_traitlist(name, sheet, traits)

class SheetTestCase(CharactersTestCase):
    fixtures = ['players']

    def _assertNamedTraitInList(self, trait_name, traitlist_name):
        self.failIf(trait_name not in [trait.name for trait in self.sheet.get_traitlist(traitlist_name)])
    def _assertNamedTraitNotInList(self, trait_name, traitlist_name):
        self.failIf(trait_name in [trait.name for trait in self.sheet.get_traitlist(traitlist_name)])

    def setUp(self):
        self.user = User.objects.get(username__exact='Andre')
        self.sheet = Sheet.objects.create(
            name='Michele',
            player=self.user)

    def testCreateTraitList(self):
        self._build_traitlist_randomize('Social', self.sheet,[
            ['dummy', 3, ''],
            ['aoeu', 2, 'frilel'],
            ['nothing', 5, 'hate']])
        self._assertNamedTraitNotInList('Vivox', 'Social')
        self._assertNamedTraitInList('dummy', 'Social')
        self._assertNamedTraitInList('aoeu', 'Social')
        self._assertNamedTraitInList('nothing', 'Social')

    def testStrangeTraitValues(self):
        self.assertRaises(ValueError, lambda: self.sheet.add_trait('Social', {'name':'Weird ness', 'value':'1 or 2'}))
        self.assertRaises(ValueError, lambda: self.sheet.add_trait('Social', {'name':'Weird har', 'value':'1-2'}))

    def testAddingTraits(self):
        self.sheet.add_trait('Mental', {'name': 'Fuckness'})
        self._assertNamedTraitInList('Fuckness', 'Mental')

    def testInsertTraits(self):
        self.sheet.add_trait('Mental', {'name':'Fuckness'})
        self.sheet.insert_trait('Mental', {'name':'Preloaded'}, 0)
        self.assertEquals('Preloaded', self.sheet.get_traitlist('Mental')[0].name)
        self.assertEquals('Fuckness', self.sheet.get_traitlist('Mental')[1].name)

    def testReorderTraitlist(self):
        names = ['a', 'b', 'c', 'd', 'e']
        for name in names:
            self.sheet.add_trait('Mental', {'name':name})

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
        self.sheet.add_trait('Mental', {'name':'CockSmap'})
        self.assertRaises(IntegrityError, lambda: self.sheet.add_trait('Mental', {'name':'CockSmap'}))

        upload_sheet_for_user('mcmillan.gex', self.user)
        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')
        self.assertRaises(IntegrityError, lambda: self.sheet.add_trait('Social', {'name': 'Commanding', 'value':2, 'note': ''}))

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
            player=self.user,
            blood=10,
            conscience=4,
            courage=2,
            selfcontrol=3,
            generation=12,
            pathtraits=3,
            physicalmax=10,
            willpower=3)

class TraitTestCase(CharactersTestCase):
    fixtures = ['players']

    def setUp(self):
        self.user = User.objects.get(username__exact='Andre')
        self.sheet = Sheet.objects.create(
            name='Michele',
            player=self.user)
    def __myAssertEqual(self, given, expected, extra):
        try:
            self.assertEqual(given, expected)
        except Exception, e:
            pprint(extra)
            raise e

    def _build_trait(self, name, value, note):
        self.sheet.add_trait('Social', {'name':name, 'value':value, 'note': note})
        return self.sheet.traits.get(name=name)

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
        for trait, test_list in fully_tested.iteritems():
            for display_type, expected_result in test_list.iteritems():
                extra = {'display_type': display_type, 'name':trait.name, 'value':trait.value, 'note':trait.note}
                trait.display_preference = int(display_type)
                self.__myAssertEqual(trait.__unicode__(), expected_result, extra)
