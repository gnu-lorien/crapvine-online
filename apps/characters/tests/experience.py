from django.test import TestCase
from characters.models import Sheet
from upload_helpers import upload_sheet_for_username

from pprint import pprint

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


