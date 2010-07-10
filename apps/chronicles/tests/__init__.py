from django.test import TestCase
from django.db.models import get_apps
import os
from characters.xml_uploader import handle_sheet_upload

from django.contrib.auth.models import User

from chronicles.models import Chronicle

from pprint import pprint

class ChronicleCharacterListTest(TestCase):
    fixtures = ['woa_hst_nar_pla_no_characters']
    def _load_sheet(self, loadfn, user):
        app_fixtures = [os.path.join(os.path.dirname(app.__file__), 'fixtures') for app in get_apps()]
        for app_fixture in app_fixtures:
            if os.path.exists(os.path.join(app_fixture, loadfn)):
                with open(os.path.join(app_fixture, loadfn), 'r') as fp:
                    return handle_sheet_upload(fp, user)

    def setUp(self):
        self.chronicle = Chronicle.objects.get(slug='woa')
        self.hst = User.objects.get(username='hst')
        self.nar = User.objects.get(username='nar')
        self.play = User.objects.get(username='play')

        self.hstnpccl = self._load_sheet('npc.gex', self.hst)
        self.hstpc2cl = self._load_sheet('pc2.gex', self.hst)
        self.playpc1cl = self._load_sheet('pc1.gex', self.play)

        for name, vs in self.hstnpccl.vampires.iteritems():
            self.chronicle.associate(vs)
        for name, vs in self.playpc1cl.vampires.iteritems():
            self.chronicle.associate(vs)

    def testHST(self):
        sheets = self.chronicle.get_sheets_for_user(self.hst)
        self.assertEqual(2, len(sheets))
        names = [s.name for s in sheets]
        self.assertTrue('Charles McMillan' in names)
        self.assertTrue('Adam St. Charles' in names)

    def testNar(self):
        sheets = self.chronicle.get_sheets_for_user(self.nar)
        self.assertEqual(0, len(sheets))

    def testPlay(self):
        sheets = self.chronicle.get_sheets_for_user(self.play)
        self.assertEqual(1, len(sheets))
        names = [s.name for s in sheets]
        self.assertTrue('Charles McMillan' in names)
