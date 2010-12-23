import os

from django.db.models import get_apps
from ..xml_uploader import handle_sheet_upload
from django.contrib.auth.models import User

def get_fixture_path_gen():
    for app in get_apps():
        yield os.path.join(os.path.dirname(app.__file__), 'fixtures')

def upload_sheet_for_user(sheet_file, user):
    for app_fixture in get_fixture_path_gen():
        sheet_file_fp = os.path.join(app_fixture, sheet_file)
        if os.path.exists(sheet_file_fp):
            with open(sheet_file_fp, 'r') as fp:
                handle_sheet_upload(fp, user)

def upload_sheet_for_username(sheet_file, username):
    upload_sheet_for_user(sheet_file, User.objects.get(username__exact=username))

def upload_chronicle_for_username(chron_file, username):
    upload_sheet_for_user(chron_file, User.objects.get(username__exact=username))
