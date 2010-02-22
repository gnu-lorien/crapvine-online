from django.test import TestCase
from characters.models import Trait, TraitList, Sheet, TraitListName
from django.contrib.auth.models import User

from pprint import pprint

class CharactersTestCase(TestCase):
    def _build_trait(self, name, value, note):
        return Trait.objects.create(name=name, value=value, note=note)

    def _build_traitlist(self, name, sheet, traits):
        trait_objs = [self._build_trait(*args) for args in traits]
        traitlist_name = TraitListName.objects.get(name__exact=name)
        for i, trait in enumerate(trait_objs):
            TraitList.objects.create(sheet=sheet, trait=trait, display_order=i, name=traitlist_name)
        return trait_objs

    def _build_traitlist_randomize(self, name, sheet, traits):
        import random
        random.shuffle(traits)
        return self._build_traitlist(name, sheet, traits)

class SheetTestCase(CharactersTestCase):
    fixtures = ['players']

    def _assertNamedTraitInList(self, trait_name, traitlist_name):
        self.failIf(trait_name not in [trait.name for trait in self.sheet.get_traitlist(traitlist_name)])
    def _assertNamedTraitNotInList(self, trait_name, traitlist_name):
        self.failIf(trait_name in [trait.name for trait in self.sheet.get_traitlist(traitlist_name)])


    def setUp(self):
        self.andrew_player = User.objects.get(username__exact='Andre')
        self.sheet = Sheet.objects.create(
            name='Michele',
            player=self.andrew_player)
        self.trait = Trait.objects.create(name='Vivox')
        self.tl = TraitList.objects.create(sheet=self.sheet, trait=self.trait, display_order=1, name=TraitListName.objects.get(name__exact='Physical'))

    def testCreateTraitList(self):
        tl = self._build_traitlist_randomize('Social', self.sheet,[
            ('dummy', 3, ''),
            ('aoeu', 2, 'frilel'),
            ('nothing', 5, 'hate')])
        self._assertNamedTraitNotInList('Vivox', 'Social')
        self._assertNamedTraitInList('dummy', 'Social')
        self._assertNamedTraitInList('aoeu', 'Social')
        self._assertNamedTraitInList('nothing', 'Social')

    def testAddingTraits(self):
        #self.sheet.add_trait('Mental', 'Determined')
        #self.sheet.add_trait('Mental', 'Insidious', value=2)
        #self.sheet.add_trait('Mental', 'Perceptive', value=5, note='Cars')
        t = Trait.objects.create(name='Fuckness')
        self.sheet.add_trait('Mental', t)
        #pprint(dir(self.sheet.get_traitlist('Mental')))
        #self.sheet.get_traitlist('Mental')[0].display_order

        #self._assertNamedTraitInList('Determined', 'Mental')
        #self._assertNamedTraitInList('Insidious', 'Mental')
        #self._assertNamedTraitInList('Perceptive', 'Mental')
        self._assertNamedTraitInList('Fuckness', 'Mental')

    def testInsertTraits(self):
        t = Trait.objects.create(name='Fuckness')
        self.sheet.add_trait('Mental', t)
        t = Trait.objects.create(name='Preloaded')
        self.sheet.insert_trait('Mental', t, 0)
        self.assertEquals('Preloaded', self.sheet.get_traitlist('Mental')[0].name)
        self.assertEquals('Fuckness', self.sheet.get_traitlist('Mental')[1].name)

    def testReorderTraitlist(self):
        names = ['a', 'b', 'c', 'd', 'e']
        for name in names:
            t = Trait.objects.create(name=name)
            self.sheet.add_trait('Mental', t)

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
        try:
            t1 = Trait.objects.create(name='CockSmap')
            self.sheet.add_trait('Mental', t1)
            self.sheet.add_trait('Social', t1)
        except ValidationError:
            return
        raise AssertionError

class TraitTestCase(CharactersTestCase):
    def __myAssertEqual(self, given, expected, extra):
        try:
            self.assertEqual(given, expected)
        except Exception, e:
            from pprint import pprint
            pprint(extra)
            raise e

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
        from pprint import pprint
        for trait, test_list in fully_tested.iteritems():
            for display_type, expected_result in test_list.iteritems():
                extra = {'display_type': display_type, 'name':trait.name, 'value':trait.value, 'note':trait.note}
                trait.display_preference = int(display_type)
                self.__myAssertEqual(trait.__unicode__(), expected_result, extra)
