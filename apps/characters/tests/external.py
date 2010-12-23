from django.test import TestCase
from django.contrib.auth.models import User
from upload_helpers import upload_chronicle_for_username, upload_sheet_for_user
from characters.models import Sheet, VampireSheet, ExperienceEntry

from ..xml_uploader import handle_sheet_upload, VampireExporter

import StringIO

class ExportTestCase(TestCase):
    fixtures = ['players']

    def setUp(self):
        self.user = User.objects.get(username__exact='Andre')
        upload_sheet_for_user('mcmillan.gex', self.user)

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

    def testChronicle(self):
        pass

class ImportTestCase(TestCase):
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

    def assertSheetExists(self, sheet_name):
        self.assertRaises(Sheet.DoesNotExist, Sheet.objects.get(name__exact=sheet_name))

    def testChronicleAll(self):
        upload_chronicle_for_username('chronicle_00.gex', 'Andre')
        self.assertSheetExists('Charles McMillan')
        self.assertSheetExists('Adam St. Charles')
        self.assertSheetExists('ValueForEverything')

    def testChronicleInclude(self):
        upload_chronicle_for_username('chronicle_00.gex', 'Andre', include='Charles McMillan')
        self.assertSheetExists('Charles McMillan')
        self.assertSheetDoesNotExist('Adam St. Charles')
        self.assertSheetDoesNotExist('ValueForEverything')
        upload_chronicle_for_username('chronicle_00.gex', 'Andre', include='Adam.*')
        self.assertSheetExists('Charles McMillan')
        self.assertSheetExists('Adam St. Charles')
        self.assertSheetDoesNotExist('ValueForEverything')

    def testChronicleExclude(self):
        upload_chronicle_for_username('chronicle_00.gex', 'Andre', exclude='^C')
        self.assertSheetDoesNotExist('Charles McMillan')
        self.assertSheetExists('Adam St. Charles')
        self.assertSheetExists('ValueForEverything')
