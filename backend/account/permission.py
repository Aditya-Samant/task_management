from rest_framework import permissions

class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the manager.
        return request.user.is_staff
        
class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is a manager
        return request.user.is_staff