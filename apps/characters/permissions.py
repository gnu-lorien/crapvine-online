import authority
from authority import permissions
from characters.models import Sheet

class SheetPermission(permissions.BasePermission):
    label = 'sheet_permission'
    check = ('fullview', 'view',)

authority.register(Sheet, SheetPermission)
