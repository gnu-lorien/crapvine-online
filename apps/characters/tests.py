import unittest
from characters.models import Trait

class TraitTestCase(unittest.TestCase):
    def __build_trait(self, name, value, note):
        return Trait.objects.create(name=name, value=value, note=note)

    def testDisplay(self):
        fully_tested = {
            self.__build_trait('Example', 3, 'Carlsbad') :
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
                    '9' : '3',
                    '10': 'Carlsbad',
                },
            self.__build_trait('Example', 3, '') :
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
                    '10': '',
                },
            self.__build_trait('Example', 0, '') :
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
                    '10': '',
                },
            self.__build_trait('Example', 0, 'Carlsbad') :
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
                    '10': 'Carlsbad',
                }
        }
        from pprint import pprint
        for trait, test_list in fully_tested.iteritems():
            for display_type, expected_result in test_list.iteritems():
                pprint(display_type)
                pprint({'name':trait.name, 'value':trait.value, 'note':trait.note})
                trait.display_preference = int(display_type)
                self.assertEqual(trait.__unicode__(), expected_result)
