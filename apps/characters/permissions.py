import authority
from authority import permissions
from characters.models import Sheet

from chronicles.models import Chronicle, ChronicleMember

class SheetPermission(permissions.BasePermission):
    label = 'sheet_permission'
    check = ('fullview', 'change', 'delete', 'list', 'history',)

authority.register(Sheet, SheetPermission)

def can_something_sheet(request, sheet, role, checkperm, user=None, infodump=False):
    if user is None:
        user = request.user
    if user == sheet.player:
        if infodump:
            return (True, "Sheet owner")
        else:
            return True

    for chronicle in Chronicle.objects.all():
        chronicle_sheets = chronicle.content_objects(Sheet)
        try:
            chronicle_sheets.get(id=sheet.id)
            cm = ChronicleMember.objects.get(user=user)
            if role == cm.membership_role:
                if infodump:
                    return (True, "%s in %s" % (cm.get_membership_role_display(), cm.chronicle.name))
                else:
                    return True
        except Chronicle.DoesNotExist:
            pass
        except ChronicleMember.DoesNotExist:
            pass

    check = SheetPermission(user)
    if check.has_perm(checkperm, sheet, approved=True):
        if infodump:
            if user.is_superuser:
                return (True, "Superuser")
            else:
                return (True, "Has perm %s" % checkperm)
        else:
            return True

    if infodump:
        return (False, "")
    else:
        return False

def can_edit_sheet(request, sheet, user=None, infodump=False):
    return can_something_sheet(request, sheet, 0, 'sheet_permission.change_sheet', user=user, infodump=infodump)

def can_delete_sheet(request, sheet, user=None, infodump=False):
    return can_something_sheet(request, sheet, 0, 'sheet_permission.delete_sheet', user=user, infodump=infodump)

def can_history_sheet(request, sheet, user=None, infodump=False):
    return can_something_sheet(request, sheet, 0, 'sheet_permission.history_sheet', user=user, infodump=infodump)
def can_fullview_sheet(request, sheet, user=None, infodump=False):
    return can_something_sheet(request, sheet, 0, 'sheet_permission.fullview_sheet', user=user, infodump=infodump)

def can_list_sheet(request, sheet, user=None, infodump=False):
    return can_something_sheet(request, sheet, 0, 'sheet_permission.list_sheet', user=user, infodump=infodump)
