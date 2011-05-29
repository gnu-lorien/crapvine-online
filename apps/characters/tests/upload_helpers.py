import os

from django.db.models import get_apps
from ..xml_uploader import handle_sheet_upload
from ..bin_uploader import handle_sheet_upload as bin_handle_sheet_upload, is_binary
from django.contrib.auth.models import User

def get_fixture_path_gen():
    for app in get_apps():
        yield os.path.join(os.path.dirname(app.__file__), 'fixtures')

def upload_sheet_for_user(sheet_file, user):
    handled = False
    for app_fixture in get_fixture_path_gen():
        sheet_file_fp = os.path.join(app_fixture, sheet_file)
        if os.path.exists(sheet_file_fp):
            handled = True
            with open(sheet_file_fp, 'rb') as fp:
                binary = is_binary(fp)
            if binary:
                with open(sheet_file_fp, 'rb') as fp:
                    bin_handle_sheet_upload(fp, user)
            else:
                with open(sheet_file_fp, 'r') as fp:
                    handle_sheet_upload(fp, user)
    if not handled:
        raise RuntimeError("Could not open file {}".format(sheet_file))

def upload_sheet_for_username(sheet_file, username):
    upload_sheet_for_user(sheet_file, User.objects.get(username__exact=username))

def upload_chronicle_for_user(chron_file, user):
    upload_sheet_for_user(chron_file, user)

def upload_chronicle_for_username(chron_file, username):
    upload_chronicle_for_user(chron_file, User.objects.get(username__exact=username))
