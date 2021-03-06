import unittest
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from compare import compare_vampire_sheets
from upload_helpers import upload_chronicle_for_username, upload_sheet_for_user, upload_chronicle_for_user,\
    upload_sheet_for_username, get_fixture_path_gen
from characters.models import Sheet, VampireSheet

from ..xml_uploader import handle_sheet_upload, VampireExporter

import StringIO
from copy import deepcopy
from itertools import izip
from datetime import datetime

import os

class ChronicleUpload(TestCase):
    fixtures = ['players']

    def testUploadChronicle(self):
        c = Client()
        self.assertTrue(c.login(username='Carma', password='lorien'))
        
        loadfn = 'chronicle_camarilla_five_xml.gex'
        for app_fixture in get_fixture_path_gen():
            if os.path.exists(os.path.join(app_fixture, loadfn)):
                with open(os.path.join(app_fixture, loadfn), 'r') as f:
                    c.post("/characters/upload_sheet/",
                           {'title': 'whocares',
                            'file': f,
                            'action': 'upload'})
        response = c.get("/characters/list_sheet/carma-adam-st-charles/")
        self.assertEqual(response.status_code, 200, "Can't access XML sheets")

        c = Client()
        self.assertTrue(c.login(username='Kritn', password='lorien'))
        loadfn = 'chronicle_camarilla_five_bin.gex'
        for app_fixture in get_fixture_path_gen():
            if os.path.exists(os.path.join(app_fixture, loadfn)):
                with open(os.path.join(app_fixture, loadfn), 'rb') as f:
                    c.post("/characters/upload_sheet/",
                           {'title': 'whocares',
                            'file': f,
                            'action': 'upload'})
        response = c.get("/characters/list_sheet/kritn-adam-st-charles/")
        self.assertEqual(response.status_code, 200, "Can't access binary sheets")

        xlist = User.objects.get(username__exact='Carma').personal_characters.order_by('name')
        blist = User.objects.get(username__exact='Kritn').personal_characters.order_by('name')
        self.assertNotEqual(len(xlist), 0)
        self.assertNotEqual(len(blist), 0)
        for xv, bv in izip(xlist, blist):
            compare_vampire_sheets(self, xv.vampiresheet, bv.vampiresheet)

    def uploadForUser(self, fn, username, password):
        c = Client()
        self.assertTrue(c.login(username=username, password=password))

        loadfn = fn
        for app_fixture in get_fixture_path_gen():
            if os.path.exists(os.path.join(app_fixture, loadfn)):
                with open(os.path.join(app_fixture, loadfn), 'r') as f:
                    c.post("/characters/upload_sheet/",
                           {'title': 'whocares',
                            'file': f,
                            'action': 'upload'})
        return c

    def testLotsOfSettings(self):
        to_fill = (
            ('chronicle_camarilla_five_xml_many_settings.gex', 'Carma', 'lorien'),
            ('chronicle_camarilla_five_bin_many_settings.gex', 'Andre', 'lorien'),
            ('chronicle_camarilla_five_xml_many_settings.gv2', 'Kritn', 'lorien'),
        )
        for the_args in to_fill:
            self.uploadForUser(*the_args)

    @unittest.expectedFailure
    def testBVBG(self):
        to_fill = (
            ('chronicle_camarilla_five_bin_many_settings.gv2', 'Abson', 'lorien'),
        )
        for the_args in to_fill:
            self.uploadForUser(*the_args)


class ChronicleCompare(TestCase):
    fixtures = ['players']

    def setUp(self):
        self.userx = User.objects.get(username__exact='Andre')
        self.userb = User.objects.get(username__exact='Carma')

    def loadChrons(self, xfn, bfn):
        xml_start = datetime.now()
        upload_chronicle_for_user(xfn, self.userx)
        xml_end = datetime.now()
        print "XML Timing", xml_end - xml_start

        bin_start = datetime.now()
        upload_chronicle_for_user(bfn, self.userb)
        bin_end = datetime.now()
        print "Bin Timing", bin_end - bin_start

    def testEquivalenceLarge(self):
        self.loadChrons('chronicle_camarilla_large_xml.gex', 'chronicle_camarilla_large_bin.gex')
        xlist = self.userx.personal_characters.order_by('name')
        blist = self.userb.personal_characters.order_by('name')
        self.assertNotEqual(len(xlist), 0)
        self.assertNotEqual(len(blist), 0)
        for xv, bv in izip(self.userx.personal_characters.order_by('name'), self.userb.personal_characters.order_by('name')):
            print "Comparing", xv.name
            compare_vampire_sheets(self, xv.vampiresheet, bv.vampiresheet)

    def testEquivalenceFive(self):
        self.loadChrons('chronicle_camarilla_five_xml.gex', 'chronicle_camarilla_five_bin.gex')
        xlist = self.userx.personal_characters.order_by('name')
        blist = self.userb.personal_characters.order_by('name')
        self.assertNotEqual(len(xlist), 0)
        self.assertNotEqual(len(blist), 0)
        for xv, bv in izip(self.userx.personal_characters.order_by('name'), self.userb.personal_characters.order_by('name')):
            compare_vampire_sheets(self, xv.vampiresheet, bv.vampiresheet)


class Export(TestCase):
    fixtures = ['players']

    def setUp(self):
        self.user = User.objects.get(username__exact='Andre')
        upload_sheet_for_user('mcmillan.gex', self.user)

    #def testModelLooks(self):
        #print dir(ExperienceEntry._meta)
        #print ExperienceEntry._meta.get_fields_with_model()
        #for fn in ExperienceEntry._meta.get_all_field_names():
        #    print fn, ExperienceEntry._meta.get_field_by_name(fn)[0]
        #    #if not isinstance(ExperienceEntry._meta.get_field_by_name(fn)[0], django.db.models.fields.AutoField):
        #    #    print fn

    def testExportEquivalence(self):
        vampire_sheet = VampireSheet.objects.get(name__exact='Charles McMillan')
        vampire_sheet.name = "Suckon Deez Nuts"
        ve = VampireExporter(vampire_sheet)
        #print ve
        sf = StringIO.StringIO(unicode(ve))
        handle_sheet_upload(sf, self.user)

        new_sheet = VampireSheet.objects.get(name__exact='Suckon Deez Nuts')

        compare_vampire_sheets(self, new_sheet, vampire_sheet)

    def testChronicle(self):
        pass

class Import(TestCase):
    fixtures = ['players']

    def setUp(self):
        self.user = User.objects.get(username__exact='Andre')

    def testMcMillan(self):
        upload_sheet_for_user('mcmillan.gex', self.user)
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
        self.assertEquals(entries[2].change, 2)
        self.assertEquals(entries[3].change, 0.5)
        self.assertEquals(entries[2].reason, "Attendance")
        self.assertEquals(entries[3].reason, "Workshop")

        self.assertEquals(self.sheet.experience_unspent, 29)
        self.assertEquals(self.sheet.experience_earned, 390)

    def testExperienceReversing(self):
        upload_sheet_for_user('mcmillan.gex', self.user)
        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')
        erf = [e.reason for e in self.sheet.experience_entries.all().order_by('date')]
        err = [e.reason for e in self.sheet.experience_entries.all().order_by('-date')]
        for i, reasons in enumerate(zip(erf, reversed(err))):
            self.assertEquals(reasons[0], reasons[1])
        self.assertEquals(erf, list(reversed(err)))

    def testExperienceOrdering(self):
        upload_sheet_for_user('mcmillan.gex', self.user)
        self.sheet = Sheet.objects.get(name__exact='Charles McMillan')
        erf = [e.reason for e in self.sheet.experience_entries.all().order_by('date')]
        err = [e.reason for e in self.sheet.experience_entries.all()]
        for i, reasons in enumerate(zip(erf, err)):
            self.assertEquals(reasons[0], reasons[1])
        self.assertEquals(erf, err)

    def testExperienceAdd(self):
        upload_sheet_for_user('mcmillan.gex', self.user)
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

    def assertSheetExists(self, sheet_name):
        Sheet.objects.get(name__exact=sheet_name)

    def assertSheetDoesNotExist(self, sheet_name):
        self.assertRaises(Sheet.DoesNotExist, Sheet.objects.get(name__exact=sheet_name))

    def testChronicleAll(self):
        upload_chronicle_for_username('chronicle_00.gex', 'Andre')
        self.assertSheetExists('Charles McMillan')
        self.assertSheetExists('Adam St. Charles')
        self.assertSheetExists('ValueForEverything')

    def testWeirdSandra(self):
        upload_sheet_for_username('sandra_weird_dates.gex', 'Andre')

    def testPythonDatetimeBug(self):
        from ..uploader import translate_date
        self.assertRaises(ValueError, lambda: translate_date("rrererre"))
        dt = translate_date("5/1/2004")
        print dt
        self.assertEqual(dt, datetime(2004, 5, 1, 0, 0, 0))
        print dt.strftime("%m/%d/%Y %I:%M:%S %p")
        self.assertEqual(
            datetime.strptime("05/01/2004 12:00:00 AM", "%m/%d/%Y %I:%M:%S %p"),
            datetime.strptime("05/01/2004", "%m/%d/%Y"))
        self.assertEqual(dt, translate_date(dt.strftime("%m/%d/%Y %I:%M:%S %p")))

    def testIsraelLocale(self):
        upload_sheet_for_username('israeli_datetime_xml.gex', 'Andre')
        self.sheet = Sheet.objects.get(name__exact='Rand McDom')
        expected_start_date = datetime(year=2008, month=10, day=29, hour=0, minute=26, second=48)
        expected_last_modified_date = datetime(year=2010, month=6, day=17, hour=18, minute=6, second=11)
        expected_experience_entries = (
            (2008, 8, 8),
            (2008, 10, 20),
            (2008, 10, 31, 22, 15, 37),
            (2008, 11, 19),
            (2008, 11, 28, 18, 13, 1),
            (2008, 12, 27),
            (2009, 1, 3, 23, 46, 33),
            (2009, 1, 6),
            (2009, 1, 30, 12, 40, 40),
            (2009, 2, 1, 15, 46, 58),
            (2009, 3, 8, 8, 3, 55),
            (2009, 3, 25),
            (2009, 3, 31, 16, 45, 44),
            (2009, 4, 27, 15, 31, 18),
            (2009, 5, 1),
            (2009, 5, 2, 17, 41, 26),
            (2009, 5, 4, 16, 26, 27)
        )
        expected_experience_entries = [datetime(*a) for a in expected_experience_entries]
        sheet_entries = [ee.date for ee in self.sheet.experience_entries.all()]
        self.assertEqual(expected_experience_entries, sheet_entries)


    #def testChronicleInclude(self):
    #    upload_chronicle_for_username('chronicle_00.gex', 'Andre', include='Charles McMillan')
    #    self.assertSheetExists('Charles McMillan')
    #    self.assertSheetDoesNotExist('Adam St. Charles')
    #    self.assertSheetDoesNotExist('ValueForEverything')
    #    upload_chronicle_for_username('chronicle_00.gex', 'Andre', include='Adam.*')
    #    self.assertSheetExists('Charles McMillan')
    #    self.assertSheetExists('Adam St. Charles')
    #    self.assertSheetDoesNotExist('ValueForEverything')

    #def testChronicleExclude(self):
    #    upload_chronicle_for_username('chronicle_00.gex', 'Andre', exclude='^C')
    #    self.assertSheetDoesNotExist('Charles McMillan')
    #    self.assertSheetExists('Adam St. Charles')
    #    self.assertSheetExists('ValueForEverything')
