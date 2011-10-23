# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ExperienceEntry'
        db.create_table('characters_experienceentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reason', self.gf('django.db.models.fields.TextField')()),
            ('change', self.gf('django.db.models.fields.FloatField')()),
            ('change_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('earned', self.gf('django.db.models.fields.FloatField')()),
            ('unspent', self.gf('django.db.models.fields.FloatField')()),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('characters', ['ExperienceEntry'])

        # Adding model 'Expendable'
        db.create_table('characters_expendable', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('value', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('modifier', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('dot_character', self.gf('django.db.models.fields.CharField')(default='O', max_length=8)),
            ('modifier_character', self.gf('django.db.models.fields.CharField')(default='\xc3\x95', max_length=8)),
        ))
        db.send_create_signal('characters', ['Expendable'])

        # Adding model 'TraitListName'
        db.create_table('characters_traitlistname', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
        ))
        db.send_create_signal('characters', ['TraitListName'])

        # Adding model 'Sheet'
        db.create_table('characters_sheet', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('player', self.gf('django.db.models.fields.related.ForeignKey')(related_name='personal_characters', to=orm['auth.User'])),
            ('narrator', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=128, db_index=True)),
            ('home_chronicle', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('npc', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('notes', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('biography', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_saved', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('experience_unspent', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('experience_earned', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('object_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('uploading', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('characters', ['Sheet'])

        # Adding unique constraint on 'Sheet', fields ['player', 'name']
        db.create_unique('characters_sheet', ['player_id', 'name'])

        # Adding M2M table for field experience_entries on 'Sheet'
        db.create_table('characters_sheet_experience_entries', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sheet', models.ForeignKey(orm['characters.sheet'], null=False)),
            ('experienceentry', models.ForeignKey(orm['characters.experienceentry'], null=False))
        ))
        db.create_unique('characters_sheet_experience_entries', ['sheet_id', 'experienceentry_id'])

        # Adding model 'VampireSheet'
        db.create_table('characters_vampiresheet', (
            ('sheet_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['characters.Sheet'], unique=True, primary_key=True)),
            ('nature', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('demeanor', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('blood', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=10, blank=True)),
            ('clan', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('conscience', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=3, blank=True)),
            ('courage', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=3, blank=True)),
            ('generation', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=13, blank=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('pathtraits', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=3, blank=True)),
            ('physicalmax', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=10, blank=True)),
            ('sect', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('selfcontrol', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=2, blank=True)),
            ('willpower', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=2, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('aura', self.gf('django.db.models.fields.SmallIntegerField')(default=0, blank=True)),
            ('coterie', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('id_text', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('sire', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('tempcourage', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('tempselfcontrol', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('tempwillpower', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('tempblood', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('tempconscience', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('temppathtraits', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal('characters', ['VampireSheet'])

        # Adding model 'TraitListProperty'
        db.create_table('characters_traitlistproperty', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sheet', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['characters.Sheet'])),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['characters.TraitListName'])),
            ('sorted', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('atomic', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('negative', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('display_preference', self.gf('django.db.models.fields.SmallIntegerField')(default=1)),
        ))
        db.send_create_signal('characters', ['TraitListProperty'])

        # Adding unique constraint on 'TraitListProperty', fields ['sheet', 'name']
        db.create_unique('characters_traitlistproperty', ['sheet_id', 'name_id'])

        # Adding model 'Trait'
        db.create_table('characters_trait', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('note', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('value', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('display_preference', self.gf('django.db.models.fields.SmallIntegerField')(default=1)),
            ('dot_character', self.gf('django.db.models.fields.CharField')(default='O', max_length=8)),
            ('approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('sheet', self.gf('django.db.models.fields.related.ForeignKey')(related_name='traits', to=orm['characters.Sheet'])),
            ('traitlistname', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['characters.TraitListName'])),
        ))
        db.send_create_signal('characters', ['Trait'])

        # Adding unique constraint on 'Trait', fields ['sheet', 'traitlistname', 'name']
        db.create_unique('characters_trait', ['sheet_id', 'traitlistname_id', 'name'])

        # Adding model 'ChangedTrait'
        db.create_table('characters_changedtrait', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sheet', self.gf('django.db.models.fields.related.ForeignKey')(related_name='changed_traits', to=orm['characters.Sheet'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('note', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('value', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('traitlistname', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['characters.TraitListName'])),
            ('newer_trait_form', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('added', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('characters', ['ChangedTrait'])

        # Adding model 'Menu'
        db.create_table('characters_menu', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('category', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('sorted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('negative', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('autonote', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('display_preference', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
        ))
        db.send_create_signal('characters', ['Menu'])

        # Adding model 'MenuItem'
        db.create_table('characters_menuitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('cost', self.gf('django.db.models.fields.CharField')(default='1', max_length=128, blank=True)),
            ('note', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['characters.Menu'])),
            ('item_type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('menu_to_import', self.gf('django.db.models.fields.related.ForeignKey')(related_name='imported_menus', null=True, to=orm['characters.Menu'])),
        ))
        db.send_create_signal('characters', ['MenuItem'])

        # Adding model 'FailedUpload'
        db.create_table('characters_failedupload', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('player', self.gf('django.db.models.fields.related.ForeignKey')(related_name='failed_uploads', to=orm['auth.User'])),
            ('exception', self.gf('django.db.models.fields.TextField')()),
            ('traceback', self.gf('django.db.models.fields.TextField')()),
            ('verified', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('characters', ['FailedUpload'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Trait', fields ['sheet', 'traitlistname', 'name']
        db.delete_unique('characters_trait', ['sheet_id', 'traitlistname_id', 'name'])

        # Removing unique constraint on 'TraitListProperty', fields ['sheet', 'name']
        db.delete_unique('characters_traitlistproperty', ['sheet_id', 'name_id'])

        # Removing unique constraint on 'Sheet', fields ['player', 'name']
        db.delete_unique('characters_sheet', ['player_id', 'name'])

        # Deleting model 'ExperienceEntry'
        db.delete_table('characters_experienceentry')

        # Deleting model 'Expendable'
        db.delete_table('characters_expendable')

        # Deleting model 'TraitListName'
        db.delete_table('characters_traitlistname')

        # Deleting model 'Sheet'
        db.delete_table('characters_sheet')

        # Removing M2M table for field experience_entries on 'Sheet'
        db.delete_table('characters_sheet_experience_entries')

        # Deleting model 'VampireSheet'
        db.delete_table('characters_vampiresheet')

        # Deleting model 'TraitListProperty'
        db.delete_table('characters_traitlistproperty')

        # Deleting model 'Trait'
        db.delete_table('characters_trait')

        # Deleting model 'ChangedTrait'
        db.delete_table('characters_changedtrait')

        # Deleting model 'Menu'
        db.delete_table('characters_menu')

        # Deleting model 'MenuItem'
        db.delete_table('characters_menuitem')

        # Deleting model 'FailedUpload'
        db.delete_table('characters_failedupload')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'characters.changedtrait': {
            'Meta': {'ordering': "['date']", 'object_name': 'ChangedTrait'},
            'added': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'newer_trait_form': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'sheet': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'changed_traits'", 'to': "orm['characters.Sheet']"}),
            'traitlistname': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['characters.TraitListName']"}),
            'value': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'characters.expendable': {
            'Meta': {'object_name': 'Expendable'},
            'dot_character': ('django.db.models.fields.CharField', [], {'default': "'O'", 'max_length': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modifier': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'modifier_character': ('django.db.models.fields.CharField', [], {'default': "'\\xc3\\x95'", 'max_length': '8'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'value': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'characters.experienceentry': {
            'Meta': {'ordering': "['date']", 'object_name': 'ExperienceEntry'},
            'change': ('django.db.models.fields.FloatField', [], {}),
            'change_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'earned': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reason': ('django.db.models.fields.TextField', [], {}),
            'unspent': ('django.db.models.fields.FloatField', [], {})
        },
        'characters.failedupload': {
            'Meta': {'object_name': 'FailedUpload'},
            'exception': ('django.db.models.fields.TextField', [], {}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'failed_uploads'", 'to': "orm['auth.User']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'traceback': ('django.db.models.fields.TextField', [], {}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'characters.menu': {
            'Meta': {'object_name': 'Menu'},
            'autonote': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'category': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'display_preference': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'negative': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sorted': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'characters.menuitem': {
            'Meta': {'ordering': "['order']", 'object_name': 'MenuItem'},
            'cost': ('django.db.models.fields.CharField', [], {'default': "'1'", 'max_length': '128', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'menu_to_import': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'imported_menus'", 'null': 'True', 'to': "orm['characters.Menu']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'note': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['characters.Menu']"})
        },
        'characters.sheet': {
            'Meta': {'unique_together': "(('player', 'name'),)", 'object_name': 'Sheet'},
            'biography': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
            'experience_earned': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'experience_entries': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['characters.ExperienceEntry']", 'symmetrical': 'False'}),
            'experience_unspent': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'home_chronicle': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_saved': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'narrator': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'npc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'personal_characters'", 'to': "orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '128', 'db_index': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'uploading': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'characters.trait': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('sheet', 'traitlistname', 'name'),)", 'object_name': 'Trait'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_preference': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'dot_character': ('django.db.models.fields.CharField', [], {'default': "'O'", 'max_length': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'note': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'sheet': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'traits'", 'to': "orm['characters.Sheet']"}),
            'traitlistname': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['characters.TraitListName']"}),
            'value': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'characters.traitlistname': {
            'Meta': {'object_name': 'TraitListName'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'characters.traitlistproperty': {
            'Meta': {'ordering': "['name__name']", 'unique_together': "(('sheet', 'name'),)", 'object_name': 'TraitListProperty'},
            'atomic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_preference': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['characters.TraitListName']"}),
            'negative': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sheet': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['characters.Sheet']"}),
            'sorted': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'characters.vampiresheet': {
            'Meta': {'object_name': 'VampireSheet', '_ormbases': ['characters.Sheet']},
            'aura': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'blood': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '10', 'blank': 'True'}),
            'clan': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'conscience': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3', 'blank': 'True'}),
            'coterie': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'courage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3', 'blank': 'True'}),
            'demeanor': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'generation': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '13', 'blank': 'True'}),
            'id_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'nature': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'pathtraits': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3', 'blank': 'True'}),
            'physicalmax': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '10', 'blank': 'True'}),
            'sect': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'selfcontrol': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2', 'blank': 'True'}),
            'sheet_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['characters.Sheet']", 'unique': 'True', 'primary_key': 'True'}),
            'sire': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'tempblood': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'tempconscience': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'tempcourage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'temppathtraits': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'tempselfcontrol': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'tempwillpower': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'willpower': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['characters']
