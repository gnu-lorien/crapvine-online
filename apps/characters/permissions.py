import authority
from authority import permissions
from characters.models import Sheet

from chronicles.models import Chronicle, ChronicleMember

class SheetPermission(permissions.BasePermission):
    label = 'sheet_permission'
    check = ('fullview', 'view',)

authority.register(Sheet, SheetPermission)

def can_something_sheet(request, sheet, role, checkperm):
    if request.user == sheet.player:
        return True

    for chronicle in Chronicle.objects.all():
        chronicle_sheets = chronicle.content_objects(Sheet)
        try:
            chronicle_sheets.get(id=sheet.id)
            cm = ChronicleMember.objects.get(user=request.user)
            if role == cm.membership_role:
                return True
        except Chronicle.DoesNotExist:
            pass
        except ChronicleMember.DoesNotExist:
            pass

    check = SheetPermission(request.user)
    if check.has_perm(checkperm, sheet, approved=True):
        return True

    return False

def can_edit_sheet(request, sheet):
    return can_something_sheet(request, sheet, 0, 'sheet_permission.change_sheet')

def can_delete_sheet(request, sheet):
    return can_something_sheet(request, sheet, 0, 'sheet_permission.delete_sheet')

def can_history_sheet(request, sheet):
    return can_something_sheet(request, sheet, 0, 'sheet_permission.history_sheet')

def can_list_sheet(request, sheet):
    return can_something_sheet(request, sheet, 0, 'sheet_permission.fullview_sheet')
