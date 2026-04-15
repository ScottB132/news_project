"""
newsApp/permissions.py

Custom Django REST Framework permission classes for the Speedy Spectator
news application.

These permission classes are used to protect API endpoints by role,
ensuring that only users with the correct role can access specific
actions. They are applied at the view level in api_views.py.

Permission classes available:
    - IsEditor:            Only users with the editor role.
    - IsJournalist:        Only users with the journalist role.
    - IsReader:            Only users with the reader role.
    - IsEditorOrJournalist: Users with either the editor or journalist role.

Usage example in api_views.py:
    from .permissions import IsEditor

    class ArticleApproveView(APIView):
        permission_classes = [IsAuthenticated]

        def post(self, request, pk):
            if not IsEditor().has_permission(request, self):
                return Response({'error': '...'}, status=403)
"""

from rest_framework.permissions import BasePermission


# ---------------------------------------------------------------------------
# Role-Based Permission Classes
# ---------------------------------------------------------------------------

class IsEditor(BasePermission):
    """
    Grants access only to authenticated users with the editor role.

    Used to protect endpoints that should only be accessible by editors,
    such as article approval, rejection, and editor queue management.

    Returns:
        bool: True if the user is authenticated and has role 'editor'.
    """

    def has_permission(self, request, view):
        """
        Check if the requesting user is an authenticated editor.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is authenticated and has the editor role.
        """
        return (
            request.user.is_authenticated
            and request.user.role == 'editor'
        )


class IsJournalist(BasePermission):
    """
    Grants access only to authenticated users with the journalist role.

    Used to protect endpoints that should only be accessible by journalists,
    such as article creation and newsletter management.

    Returns:
        bool: True if the user is authenticated and has role 'journalist'.
    """

    def has_permission(self, request, view):
        """
        Check if the requesting user is an authenticated journalist.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is authenticated and has the journalist role.
        """
        return (
            request.user.is_authenticated
            and request.user.role == 'journalist'
        )


class IsReader(BasePermission):
    """
    Grants access only to authenticated users with the reader role.

    Used to protect endpoints that should only be accessible by readers,
    such as the subscription-based article feed.

    Returns:
        bool: True if the user is authenticated and has role 'reader'.
    """

    def has_permission(self, request, view):
        """
        Check if the requesting user is an authenticated reader.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is authenticated and has the reader role.
        """
        return (
            request.user.is_authenticated
            and request.user.role == 'reader'
        )


class IsEditorOrJournalist(BasePermission):
    """
    Grants access to authenticated users with either the editor or
    journalist role.

    Used to protect endpoints where both editors and journalists should
    have access, such as newsletter creation and article updates.

    Returns:
        bool: True if the user is authenticated and has role 'editor'
              or 'journalist'.
    """

    def has_permission(self, request, view):
        """
        Check if the requesting user is an authenticated editor or journalist.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is authenticated and has either
                  the editor or journalist role.
        """
        return (
            request.user.is_authenticated
            and request.user.role in ('editor', 'journalist')
        )
