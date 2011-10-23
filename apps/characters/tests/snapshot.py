from django.test import TestCase
from characters.models import VampireSheet, Trait, ChangedTrait
from compare import compare_vampire_sheets
from upload_helpers import upload_sheet_for_username

class Snapshot(TestCase):
    fixtures = ['players']

    def setUp(self):
        upload_sheet_for_username('mcmillan.gex', 'Andre')
        self.sheet = VampireSheet.objects.get(name__exact='Charles McMillan')
        self.sheet.uploading = False
        self.sheet.save()

    def testCopy(self):
        self.sheet2 = self.sheet.copy(save=True)
        compare_vampire_sheets(self, self.sheet, self.sheet2)