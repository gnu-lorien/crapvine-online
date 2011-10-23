from django.test import TestCase
from characters.models import VampireSheet, Trait, ChangedTrait
from compare import compare_vampire_sheets, compare_traits, compare_sheet_base_attributes, compare_vampire_base_attributes,\
    compare_experience_entries
from upload_helpers import upload_sheet_for_username

class SnapshotTest(TestCase):
    fixtures = ['players']

    def setUp(self):
        upload_sheet_for_username('mcmillan.gex', 'Andre')
        self.sheet = VampireSheet.objects.get(name__exact='Charles McMillan')
        self.sheet.uploading = False
        self.sheet.save()

    def testSnapshot(self):
        self.sheet2 = self.sheet.snapshot()
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

    def testSnapshotMapping(self):
        snapnum = 2
        snapshots = [self.sheet.snapshot() for i in xrange(snapnum)]
        print "Orig sheet"
        print self.sheet.snapshots.all()
        self.assertEqual(len(self.sheet.snapshots.all()), snapnum)
        print self.sheet.am_i_a_snapshot.all()
        self.assertEqual(len(self.sheet.am_i_a_snapshot.all()), 0)
        for s in snapshots:
            self.assertEqual(len(s.snapshots.all()), 0)
            self.assertEqual(len(s.am_i_a_snapshot.all()), 1)