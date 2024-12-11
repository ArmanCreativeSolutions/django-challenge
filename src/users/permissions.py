from rest_framework.permissions import BasePermission

class IsStadiumAdmin(BasePermission):
    def has_permission(self, request, view):
        print(request.user)
        return request.user.is_authenticated and request.user.is_stadium_admin
