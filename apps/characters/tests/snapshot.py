from django.test import TestCase
from characters.models import Sheet, VampireSheet, Trait, ChangedTrait
from compare import compare_vampire_sheets, compare_traits, compare_sheet_base_attributes, compare_vampire_base_attributes,\
    compare_experience_entries, compare_sheets
from upload_helpers import upload_sheet_for_username

class SnapshotTest(TestCase):
    fixtures = ['players']

    def setUp(self):
        upload_sheet_for_username('mcmillan.gex', 'Andre')
        self.sheet = VampireSheet.objects.get(name__exact='Charles McMillan')
        self.sheet.uploading = False
        self.sheet.save()

    def compareSnapshots(self, origsheet, snapsheet):
        self.assertNotEqual(origsheet.biography, "Rcenn")
        origsheet.biography = "Rcenn"
        origsheet.save()
        self.assertRaises(AssertionError, lambda:compare_sheet_base_attributes(self, origsheet, snapsheet))

        t = origsheet.traits.all()[0]
        self.assertNotEqual(t.value, 2)
        t.value = 2
        t.save()
        self.assertRaises(AssertionError, lambda:compare_traits(self, origsheet, snapsheet))

        ee = origsheet.experience_entries.all()[0]
        self.assertNotEqual(ee.reason, "Carlsbad")
        ee.reason = "Carlsbad"
        ee.save()
        self.assertRaises(AssertionError, lambda:compare_experience_entries(self, origsheet, snapsheet))

    def compareSnapshotsVampsheets(self, origsheet, snapsheet):
        self.assertNotEqual(origsheet.biography, "Rcenn")
        origsheet.biography = "Rcenn"
        origsheet.save()
        self.assertRaises(AssertionError, lambda:compare_sheet_base_attributes(self, origsheet, snapsheet))

        self.assertNotEqual(origsheet.blood, 12)
        origsheet.blood = 12
        origsheet.save()
        self.assertRaises(AssertionError, lambda:compare_vampire_base_attributes(self, origsheet, snapsheet))

        t = origsheet.traits.all()[0]
        self.assertNotEqual(t.value, 2)
        t.value = 2
        t.save()
        self.assertRaises(AssertionError, lambda:compare_traits(self, origsheet, snapsheet))

        ee = origsheet.experience_entries.all()[0]
        self.assertNotEqual(ee.reason, "Carlsbad")
        ee.reason = "Carlsbad"
        ee.save()
        self.assertRaises(AssertionError, lambda:compare_experience_entries(self, origsheet, snapsheet))

    def testSheetType(self):
        basesheet = Sheet.objects.get(name__exact='Charles McMillan')
        basesnap = basesheet.snapshot()

        compare_sheets(self, basesheet, basesnap)
        compare_vampire_sheets(self, basesheet.vampiresheet, basesnap.vampiresheet)

        with self.assertRaisesRegexp(AttributeError, "nature"):
            compare_vampire_base_attributes(self, basesheet, basesnap)
        with self.assertRaisesRegexp(AttributeError, "blood"):
            self.compareSnapshotsVampsheets(basesheet, basesnap)

    def testSnapshot(self):
        self.sheet2 = self.sheet.snapshot()
        compare_vampire_sheets(self, self.sheet, self.sheet2)
        self.compareSnapshotsVampsheets(self.sheet, self.sheet2)

    def testSnapshotMapping(self):
        snapnum = 2
        snapshots = [self.sheet.snapshot() for i in xrange(snapnum)]
        self.assertEqual(len(self.sheet.snapshots.all()), snapnum)
        self.assertEqual(len(self.sheet.am_i_a_snapshot.all()), 0)
        for s in snapshots:
            self.assertEqual(len(s.snapshots.all()), 0)
            self.assertEqual(len(s.am_i_a_snapshot.all()), 1)

    def testSnapshotListing(self):
        upload_sheet_for_username('chronicle_camarilla_five_bin.gex', 'Andre')
        self.assertEqual(len(Sheet.objects.all()), 6)
        Sheet.objects.all()[0].snapshot()
        self.assertEqual(len(Sheet.objects.all()), 7)
        # Find a quick way to filter out ones with snapshots
        f = Sheet.objects.all().filter(am_i_a_snapshot__snapshot_sheet__name__isnull=False)
        self.assertEqual(len(f), 1)