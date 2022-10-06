from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    '''
    If detail = False, will run has_permission
    if detail = True, will run has_permission and has_object_permission
    If permission fails, IsObjectOwner.message will be shown
    '''

    message = "You do not have permission to access the object"

    def has_permission(self, request, view):
        return True

    '''
    Obj will get the object through queryset in the viewset class
    '''
    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
