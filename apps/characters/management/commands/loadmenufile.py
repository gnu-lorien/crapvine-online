from django.core.management.base import BaseCommand, CommandError
from characters.models import Menu, MenuItem
from xml.sax import ContentHandler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

class AttributeReader:
    def __init__(self, attrs):
        self.attrs = attrs

    def boolean(self, name, default=False):
        if self.attrs.has_key(name):
            bool_val = self.attrs.get(name)
            if bool_val == 'yes':
                return True
            elif bool_val == 'no':
                return False
            else:
                raise AttributeError('Boolean xml field set to invalid value |%s|' % (bool_val))
        return False
    def b(self, name, default=False):
        return self.boolean(name, default)

    def text(self, name, default=''):
        if self.attrs.has_key(name):
            return self.attrs.get(name)
        return default
    def t(self, name, default=''):
        return self.text(name, default)

    def number_as_text(self, name, default='0'):
        # Should eventually verify that it's a number
        return text(name, default)
    def nat(self, name, default='0'):
        return self.number_as_text(name, default)

    def date(self, name, default='unknown'):
        # Should eventually parse the date?
        return text(name, default)
    def d(self, name, default='unknown'):
        return self.date(name, default)

class MenuLoader(ContentHandler):
    def __init__(self):
        self.delayed = []

    def resolve_delayed(self):
        for item, link_name in self.delayed:
            print "Attempting to resolve", link_name
            try:
                item.menu_to_import = Menu.objects.get(name=link_name)
            except Menu.DoesNotExist:
                item.menu_to_import = Menu.objects.filter(name__startswith=link_name).exclude(category=item.parent.category)[0]
            item.save()

    def startElement(self, name, attrs):
        if name == 'menu':
            if not attrs.has_key('name'):
                return
            menu = Menu(name=attrs.get('name'))
            r = AttributeReader(attrs)
            from pprint import pprint

            #pprint(r.text('category', '1'))
            #pprint(r.boolean('abc'))
            #pprint(r.boolean('required'))
            #pprint(r.text('display', '0'))
            #pprint(r.boolean('autonote'))
            #pprint(r.boolean('negative'))

            menu.category = r.text('category', '1')
            menu.sorted = r.boolean('abc')
            menu.required = r.boolean('required')
            menu.display_preference = int(r.text('display', '0'))
            menu.autonote = r.boolean('autonote')
            menu.negative = r.boolean('negative')
            menu.save()
            self.current_menu = menu
            self.order_count = 0

        elif name == 'item':
            if not attrs.has_key('name'):
                return
            item = MenuItem(name=attrs.get('name'), parent=self.current_menu, item_type=0, order=self.order_count)
            r = AttributeReader(attrs)
            item.cost = r.text('cost', '1')
            item.note = r.text('note', '')
            item.save()
            self.order_count = self.order_count + 1

        elif name == 'submenu' or name == 'include':
            if not attrs.has_key('name'):
                return
            item_type = 1 if name == 'include' else 2
            link = MenuItem(name=attrs.get('name'), parent=self.current_menu, item_type=item_type, order=self.order_count)
            r = AttributeReader(attrs)
            link_menu_name = r.text('link', link.name)
            try:
                link.menu_to_import = Menu.objects.get(name=link_menu_name)
            except Menu.DoesNotExist:
                self.delayed.append((link, link_menu_name))
            link.save()
            self.order_count = self.order_count + 1

    def endElement(self, name):
        if name == 'menu':
            self.current_menu = None
            self.order_count = 0

class Command(BaseCommand):
    args = '<grapevine xml menu file>'
    help = 'Loads menus specified in an XML grapevine menu file'

    def handle(self, *args, **options):
        MenuItem.objects.all().delete()
        Menu.objects.all().delete()
        menu_loader = MenuLoader()

        print "Initial load"
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        parser.setContentHandler(menu_loader)
        parser.parse(args[0])

        print "Resolve delayed"
        menu_loader.resolve_delayed()
