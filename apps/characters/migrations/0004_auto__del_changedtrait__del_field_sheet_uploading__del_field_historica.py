# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'ChangedTrait'
        db.delete_table('characters_changedtrait')

        # Deleting field 'Sheet.uploading'
        db.delete_column('characters_sheet', 'uploading')

        # Deleting field 'HistoricalVampireSheet.uploading'
        db.delete_column('characters_historicalvampiresheet', 'uploading')

        # Deleting field 'HistoricalSheet.uploading'
        db.delete_column('characters_historicalsheet', 'uploading')


    def backwards(self, orm):
        
        # Adding model 'ChangedTrait'
        db.create_table('characters_changedtrait', (
            ('note', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('traitlistname', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['characters.TraitListName'])),
            ('sheet', self.gf('django.db.models.fields.related.ForeignKey')(related_name='changed_traits', to=orm['characters.Sheet'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('value', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('newer_trait_form', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('characters', ['ChangedTrait'])

        # Adding field 'Sheet.uploading'
        db.add_column('characters_sheet', 'uploading', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'HistoricalVampireSheet.uploading'
        db.add_column('characters_historicalvampiresheet', 'uploading', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding field 'HistoricalSheet.uploading'
        db.add_column('characters_historicalsheet', 'uploading', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


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
        'characters.historicalsheet': {
            'Meta': {'ordering': "('-history_date',)", 'object_name': 'HistoricalSheet'},
            'biography': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'content_type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'experience_earned': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'experience_unspent': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'history_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'history_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'history_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'home_chronicle': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_saved': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'narrator': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'npc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'player_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '128', 'db_index': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'characters.historicaltrait': {
            'Meta': {'ordering': "('-history_date',)", 'object_name': 'HistoricalTrait'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_preference': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'dot_character': ('django.db.models.fields.CharField', [], {'default': "'O'", 'max_length': '8'}),
            'history_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'history_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'history_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'note': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'sheet_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'traitlistname_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'characters.historicalvampiresheet': {
            'Meta': {'ordering': "('-history_date',)", 'object_name': 'HistoricalVampireSheet'},
            'aura': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'biography': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'blood': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '10', 'blank': 'True'}),
            'clan': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'conscience': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3', 'blank': 'True'}),
            'content_type_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'coterie': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'courage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3', 'blank': 'True'}),
            'demeanor': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'experience_earned': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'experience_unspent': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'generation': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '13', 'blank': 'True'}),
            'history_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'history_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'history_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'home_chronicle': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'id_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_saved': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'narrator': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'nature': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'npc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'pathtraits': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3', 'blank': 'True'}),
            'physicalmax': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '10', 'blank': 'True'}),
            'player_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'sect': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'selfcontrol': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2', 'blank': 'True'}),
            'sheet_ptr_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'sire': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '128', 'db_index': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'tempblood': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'tempconscience': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'tempcourage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'temppathtraits': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'tempselfcontrol': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'tempwillpower': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'willpower': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2', 'blank': 'True'})
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
            'status': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'characters.snapshot': {
            'Meta': {'object_name': 'Snapshot'},
            'datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original_sheet': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'snapshots'", 'to': "orm['characters.Sheet']"}),
            'snapshot_sheet': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'am_i_a_snapshot'", 'to': "orm['characters.Sheet']"})
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
