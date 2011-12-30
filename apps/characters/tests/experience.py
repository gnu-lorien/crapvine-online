from django.test import TestCase
from django.db import IntegrityError
from characters.models import Sheet
from upload_helpers import upload_sheet_for_username

from pprint import pprint

class RecentExpenditures(TestCase):
    fixtures = ['players']

    def setUp(self):
        upload_sheet_for_username('mcmillan.gex', 'Andre')
        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')
        self.sheet.save()

    def _assertREName(self, words):
        e = self.sheet.get_recent_expenditures_entry()
        self.assertEqual(words, e.reason)

    def assertEE(self, reason, change=None, change_type=None):
        e = self.sheet.get_recent_expenditures_entry()
        self.assertEqual(reason, e.reason)
        if change is not None:
            self.assertEqual(change, e.change, "%f != %f for expected |%s|" % (change, e.change, reason))
        if change_type is not None:
            self.assertEqual(change_type, e.change_type, "%f != %f for expected |%s|" % (change_type, e.change_type, reason))

    def testBasic(self):
        t = self.sheet.traits.get(name='Law')
        t.value = 4
        t.save()
        self.assertEE(u'Purchased Law x2.', 2, 3)

        t.value = 3
        t.save()
        self.assertEE(u'Purchased Law.', 1, 3)

        t.value = 2
        t.save()
        self.assertEE(u'', 0, 6)

        t.value = 1
        t.save()
        self.assertEE(u'Removed Law.', 1, 4)

    def testRemove(self):
        t = self.sheet.traits.get(name='Law')
        self.assertEqual(2, t.value)
        t.value = 3
        t.save()
        self.assertEE(u'Purchased Law x1.', 1, 3)
        t.delete()
        self.assertEE(u'Removed Law x2.', 2, 4)

    def testAddDeleteBalance(self):
        self.sheet.add_trait('Social', {'name': 'Cockles'})
        self.assertEE(u'Purchased Cockles.', 1, 3)

        t = self.sheet.traits.get(name='Cockles')
        t.delete()
        self.assertEE(u'', 0, 6)

    def testAddChangeDelete(self):
        self.sheet.add_trait('Social', {'name': 'Cockles', 'value':3})
        self.assertEE(u'Purchased Cockles x3.', 3, 3)

        t = self.sheet.traits.get(name='Cockles')
        t.value = 2
        t.save()
        self.assertEE(u'Purchased Cockles x2.', 2, 3)

        t.value = 4
        t.save()
        self.assertEE(u'Purchased Cockles x4.', 4, 3)

        t.delete()
        self.assertEE(u'', 0, 6)

    def testAnotherBalance(self):
        self.sheet.add_trait('Social', {'name': 'Cockles', 'value':3})
        self.assertEE(u'Purchased Cockles x3.', 3, 3)

        t = self.sheet.traits.get(name='Cockles')
        t.value = 2
        t.save()
        self.assertEE(u'Purchased Cockles x2.', 2, 3)

        t = self.sheet.traits.get(name='Law')
        t.delete()
        self.assertEE(u'Purchased Cockles x2. Removed Law x2.', 0, 6)

#    def testDisplay5(self):
#        self.sheet.add_trait('Disciplines', {'name': 'Dementation: Passion', 'note': 'basic', 'display_preference': 5, 'value': 4})
#        self.assertEE(u'Purchased Dementation: Passion.', 4, 3)
#
#        t = self.sheet.traits.get(name='Auspex: Telepathy')
#        t.delete()
#        self.assertEE(u'Purchased Dementation: Passion. Removed Auspex: Telepathy.', 2, 4)

    def testDisplayNotes(self):
        self.sheet.add_trait('Social', {'name': 'Cockles', 'value':3, 'note':'recce'})
        self.assertEE(u'Purchased Cockles x3 (recce).', 3, 3)

    def testDotCharacterChange(self):
        self.sheet.add_trait('Social', {'name': 'Cockles', 'value':3, 'dot_character':'OOO'})
        #a = [ct for ct in ChangedTrait.objects.all()]

        self.assertEE(u'Purchased Cockles x3.', 3, 3)
        t = self.sheet.traits.get(name='Cockles')
        t.dot_character = 'OOOO'
        t.save()
        #a = [ct for ct in ChangedTrait.objects.all()]

        self.assertEE(u'Purchased Cockles x3.', 3, 3)
        t.value = 4
        t.save()
        #a = [ct for ct in ChangedTrait.objects.all()]

        self.assertEE(u'Purchased Cockles x4.', 4, 3)
        t.delete()
        #a = [ct for ct in ChangedTrait.objects.all()]

        self.assertEE(u'')

    def testNoteChanges(self):
        self.sheet.add_trait('Farcicle', {'name': 'Cockles', 'value':3, 'note':'OOO'})
        self.assertEE(u'Purchased Cockles x3 (OOO).', 3, 3)
        t = self.sheet.traits.get(name='Cockles')
        t.note = 'OOOO'
        t.save()
        t = self.sheet.traits.get(name='Cockles')
        self.assertEqual(t.note, 'OOOO')
        self.assertEE(u'Purchased Cockles x3 (OOOO).', 3, 3)
        t.note = '4'
        t.save()
        self.assertEE(u'Purchased Cockles x3 (4).', 3, 3)
        t.delete()
        self.assertEE(u'')

        t = self.sheet.traits.get(name='Dexterous')
        t.note = 'reallydex'
        t.save()
        self.assertEE(u'Updated note Dexterous x3 (dex) to (reallydex).', 0, 6)
        t.delete()
        self.assertEE(u'Removed Dexterous x3 (dex).', 3, 4)

    def testDoubleNoteChanges(self):
        dt = self.sheet.traits.get(name='Dexterous')
        dt.note = 'reallydex'
        dt.save()
        self.assertEE(u'Updated note Dexterous x3 (dex) to (reallydex).', 0, 6)

        et = self.sheet.traits.get(name='Energetic')
        et.note = "crap"
        et.save()
        self.assertEE(u'Updated note Dexterous x3 (dex) to (reallydex), Energetic x3 (misc) to (crap).', 0, 6)

        et.value = 4
        et.save()
        self.assertEE(u'Purchased Energetic (crap). Updated note Dexterous x3 (dex) to (reallydex), Energetic x3 (misc) to (crap).', 1, 3)

        dt.delete()
        self.assertEE(u'Purchased Energetic (crap). Removed Dexterous x3 (dex). Updated note Energetic x3 (misc) to (crap).', 2, 4)

    def testNameChanges(self):
        self.sheet.add_trait('Social', {'name': 'Cockles', 'value':3, 'note':'OOO'})
        self.assertEE(u'Purchased Cockles x3 (OOO).', 3, 3)
        t = self.sheet.traits.get(name='Cockles')
        t.name = 'OOOO'
        t.save()
        self.assertEE(u'Purchased OOOO x3 (OOO).', 3, 3)
        t.name = '4'
        t.save()
        self.assertEE(u'Purchased 4 x3 (OOO).', 3, 3)
        t.delete()
        self.assertEE(u'')

        t = self.sheet.traits.get(name='Dexterous')
        t.name = 'Douchesterous'
        t.save()
        self.assertEE(u'Renamed Dexterous x3 (dex) to Douchesterous x3 (dex).', 0, 6)
        t.delete()
        self.assertEE(u'Removed Dexterous x3 (dex).', 3, 4)

    def testDoubleNameChanges(self):
        dt = self.sheet.traits.get(name='Dexterous')
        dt.name = 'Douchesterous'
        dt.save()
        self.assertEE(u'Renamed Dexterous x3 (dex) to Douchesterous x3 (dex).', 0, 6)

        et = self.sheet.traits.get(name='Energetic')
        et.name = "Energdouchous"
        et.save()
        self.assertEE(u'Renamed Dexterous x3 (dex) to Douchesterous x3 (dex), Energetic x3 (misc) to Energdouchous x3 (misc).', 0, 6)

        et.value = 4
        et.save()
        self.assertEE(u'Purchased Energdouchous (misc). Renamed Dexterous x3 (dex) to Douchesterous x3 (dex), Energetic x3 (misc) to Energdouchous x4 (misc).', 1, 3)

        dt.delete()
        self.assertEE(u'Purchased Energdouchous (misc). Removed Dexterous x3 (dex). Renamed Energetic x3 (misc) to Energdouchous x4 (misc).', 2, 4)

    def testDoubleToTheSameNameChanges(self):
        dt = self.sheet.traits.get(name='Dexterous')
        dt.name = 'Cockles'
        dt.save()
        self.assertEE(u'Renamed Dexterous x3 (dex) to Cockles x3 (dex).', 0, 6)

        et = self.sheet.traits.get(name='Energetic')
        et.name = "Cockles"
        self.assertRaises(IntegrityError, et.save)

    def testNameAndNoteChanges(self):
        dt = self.sheet.traits.get(name='Dexterous')
        dt.note = 'reallydex'
        dt.save()
        self.assertEE(u'Updated note Dexterous x3 (dex) to (reallydex).', 0, 6)

        et = self.sheet.traits.get(name='Energetic')
        et.name = "Energon"
        et.save()
        self.assertEE(u'Updated note Dexterous x3 (dex) to (reallydex). Renamed Energetic x3 (misc) to Energon x3 (misc).', 0, 6)

        et.value = 4
        et.save()
        self.assertEE(u'Purchased Energon (misc). Updated note Dexterous x3 (dex) to (reallydex). Renamed Energetic x3 (misc) to Energon x4 (misc).', 1, 3)

        dt.delete()
        self.assertEE(u'Purchased Energon (misc). Removed Dexterous x3 (dex). Renamed Energetic x3 (misc) to Energon x4 (misc).', 2, 4)

class ExperienceEntriesTestCase(TestCase):
    fixtures = ['players']

    def setUp(self):
        upload_sheet_for_username('mcmillan.gex', 'Andre')
        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')

    def testSimpleEndEdit(self):
        last_entry = self.sheet.experience_entries.order_by('-date')[0]
        self.assertEqual(last_entry.unspent, self.sheet.experience_unspent)
        self.assertEqual(last_entry.earned, self.sheet.experience_earned)

        prev_unspent = last_entry.unspent
        prev_earned = last_entry.earned
        adding = 10
        last_entry.change += adding
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
        target_entry.change += adding
        target_entry.save()
        self.sheet.edit_experience_entry(target_entry)

        pprint(locals())
        self.assertEqual(start_unspent + adding, self.sheet.experience_unspent)
        self.assertEqual(start_earned + adding, self.sheet.experience_earned)


