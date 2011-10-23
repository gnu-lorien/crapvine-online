from django.test import TestCase
from characters.models import VampireSheet, Trait, ChangedTrait
from compare import compare_vampire_sheets, compare_traits, compare_sheet_base_attributes, compare_vampire_base_attributes,\
    compare_experience_entries
from upload_helpers import upload_sheet_for_username

class Snapshot(TestCase):
    fixtures = ['players']

    def setUp(self):
        upload_sheet_for_username('mcmillan.gex', 'Andre')
        self.sheet = VampireSheet.objects.get(name__exact='Charles McMillan')
        self.sheet.uploading = False
        self.sheet.save()

    def testCopy(self):
        self.sheet2 = self.sheet.copy()
        compare_vampire_sheets(self, self.sheet, self.sheet2)

        self.assertNotEqual(self.sheet.biography, "Rcenn")
        self.sheet.biography = "Rcenn"
        self.sheet.save()
        self.assertRaises(AssertionError, lambda:compare_sheet_base_attributes(self, self.sheet, self.sheet2))

        self.assertNotEqual(self.sheet.blood, 12)
        self.sheet.blood = 12
        self.sheet.save()
        self.assertRaises(AssertionError, lambda:compare_vampire_base_attributes(self, self.sheet, self.sheet2))

        t = self.sheet.traits.all()[0]
        self.assertNotEqual(t.value, 2)
        t.value = 2
        t.save()
        self.assertRaises(AssertionError, lambda:compare_traits(self, self.sheet, self.sheet2))

        ee = self.sheet.experience_entries.all()[0]
        self.assertNotEqual(ee.reason, "Carlsbad")
        ee.reason = "Carlsbad"
        ee.save()
        self.assertRaises(AssertionError, lambda:compare_experience_entries(self, self.sheet, self.sheet2))