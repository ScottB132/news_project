"""
newsApp/api_views.py

Django REST Framework API views for the Speedy Spectator news application.

Provides a RESTful API for third-party clients to interact with articles,
newsletters, and user data. All endpoints require JWT authentication.

Views defined here:
    - ArticleListView:           GET all approved articles / POST create article
    - SubscribedArticleListView: GET articles from reader's subscriptions
    - ArticleDetailView:         GET / PUT / DELETE a single article
    - ArticleApproveView:        POST approve a pending article (editor only)
    - NewsletterListView:        GET all newsletters / POST create newsletter
    - NewsletterDetailView:      GET / PUT / DELETE a single newsletter
    - CurrentUserView:           GET the current authenticated user's profile

Access control summary:
    - Readers:     GET articles, GET subscribed articles, GET newsletters
    - Journalists: All reader access + POST articles, PUT/DELETE own content
    - Editors:     All journalist access + POST approve, PUT/DELETE any content
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Newsletter
from .permissions import IsEditor, IsEditorOrJournalist, IsJournalist
from .serializers import ArticleSerializer, NewsletterSerializer, UserSerializer


# ---------------------------------------------------------------------------
# Article List — GET all approved articles / POST create article
# ---------------------------------------------------------------------------

class ArticleListView(APIView):
    """
    API view for listing approved articles and creating new articles.

    GET:  Returns a list of all approved articles ordered by most recent.
          Accessible by all authenticated users.

    POST: Creates a new article attributed to the authenticated journalist.
          The article is saved as unapproved and requires editor approval.
          Only accessible by journalists — readers and editors are blocked.

    Endpoint: /api/articles/
    """

    # All authenticated users can access this endpoint
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return a list of all approved articles ordered by creation date.

        Args:
            request: The incoming HTTP request.

        Returns:
            Response: Serialized list of approved articles with HTTP 200.
        """
        articles = Article.objects.filter(
            approved=True
        ).order_by('-created_at')

        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new article attributed to the authenticated journalist.

        The author is set from request.user and approved is set to False
        so the article enters the editor queue for review.

        Args:
            request: The incoming HTTP request containing article data.

        Returns:
            Response: Serialized article data with HTTP 201 on success.
                      HTTP 403 if the user is not a journalist.
                      HTTP 400 if the submitted data is invalid.
        """
        # Only journalists are permitted to create articles
        if not IsJournalist().has_permission(request, self):
            return Response(
                {'error': 'Only journalists can create articles.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ArticleSerializer(data=request.data)

        if serializer.is_valid():
            # Set author from the authenticated user and mark as unapproved
            serializer.save(author=request.user, approved=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Subscribed Article List — GET articles from reader's subscriptions
# ---------------------------------------------------------------------------

class SubscribedArticleListView(APIView):
    """
    API view for retrieving articles from a reader's subscriptions.

    GET: Returns approved articles from the reader's subscribed journalists
         and publishers. Results are deduplicated and ordered by most recent.
         Only accessible by readers — journalists and editors are blocked.

    Endpoint: /api/articles/subscribed/
    """

    # Authentication required — role check is performed inside the view
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return approved articles from the reader's subscribed sources.

        Combines articles from subscribed journalists and subscribed
        publishers into a single deduplicated queryset.

        Args:
            request: The incoming HTTP request.

        Returns:
            Response: Serialized list of subscribed articles with HTTP 200.
                      HTTP 403 if the user is not a reader.
        """
        user = request.user

        # Only readers have subscriptions — block other roles
        if user.role != 'reader':
            return Response(
                {'error': 'Only readers have subscriptions.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch approved articles from journalists the reader follows
        journalist_articles = Article.objects.filter(
            author__in=user.subscribed_journalists.all(),
            approved=True
        )

        # Fetch approved articles from publishers the reader follows
        publisher_articles = Article.objects.filter(
            publisher__in=user.subscribed_publishers.all(),
            approved=True
        )

        # Merge both querysets and remove duplicates using distinct()
        # A reader subscribed to both a journalist and their publisher
        # would otherwise see the same article twice
        articles = (
            journalist_articles | publisher_articles
        ).distinct().order_by('-created_at')

        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Article Detail — GET / PUT / DELETE a single article
# ---------------------------------------------------------------------------

class ArticleDetailView(APIView):
    """
    API view for retrieving, updating, and deleting a single article.

    GET:    Returns the full article data for an approved article.
            Accessible by all authenticated users.

    PUT:    Updates an existing article. Resets approved to False so the
            updated article re-enters the editor queue for review.
            Accessible by editors (any article) and journalists (own only).

    DELETE: Permanently deletes an article.
            Accessible by editors (any article) and journalists (own only).

    Endpoint: /api/articles/<id>/
    """

    # All authenticated users can GET — role checks applied per method
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Return the full data for a single approved article.

        Args:
            request: The incoming HTTP request.
            pk (int): The primary key of the article to retrieve.

        Returns:
            Response: Serialized article data with HTTP 200.
                      HTTP 404 if the article does not exist or is unapproved.
        """
        # Only approved articles are publicly accessible
        article = get_object_or_404(Article, pk=pk, approved=True)
        serializer = ArticleSerializer(article)
        return Response(serializer.data)

    def put(self, request, pk):
        """
        Update an existing article and reset its approval status.

        Partial updates are supported — only the provided fields are updated.
        The approved field is reset to False after every update so the
        article must be re-reviewed by an editor before going live again.

        Args:
            request: The incoming HTTP request containing updated article data.
            pk (int): The primary key of the article to update.

        Returns:
            Response: Serialized updated article data with HTTP 200.
                      HTTP 403 if the user lacks permission.
                      HTTP 400 if the submitted data is invalid.
        """
        # Only editors and journalists can update articles
        if not IsEditorOrJournalist().has_permission(request, self):
            return Response(
                {'error': 'Only editors or journalists can update articles.'},
                status=status.HTTP_403_FORBIDDEN
            )

        article = get_object_or_404(Article, pk=pk)

        # Journalists can only update articles they authored themselves
        if request.user.role == 'journalist' and article.author != request.user:
            return Response(
                {'error': 'You can only update your own articles.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # partial=True allows updating individual fields without requiring all fields
        serializer = ArticleSerializer(article, data=request.data, partial=True)

        if serializer.is_valid():
            # Reset approval so the updated article returns to the editor queue
            serializer.save(approved=False)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Permanently delete an article.

        Args:
            request: The incoming HTTP request.
            pk (int): The primary key of the article to delete.

        Returns:
            Response: Success message with HTTP 204 No Content.
                      HTTP 403 if the user lacks permission.
                      HTTP 404 if the article does not exist.
        """
        # Only editors and journalists can delete articles
        if not IsEditorOrJournalist().has_permission(request, self):
            return Response(
                {'error': 'Only editors or journalists can delete articles.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch the article without the approved=True filter
        # so editors can delete unapproved articles too
        article = get_object_or_404(Article, pk=pk)

        # Journalists can only delete articles they authored themselves
        if request.user.role == 'journalist' and article.author != request.user:
            return Response(
                {'error': 'You can only delete your own articles.'},
                status=status.HTTP_403_FORBIDDEN
            )

        article.delete()
        return Response(
            {'message': 'Article deleted.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ---------------------------------------------------------------------------
# Article Approve — POST approve a pending article (editor only)
# ---------------------------------------------------------------------------

class ArticleApproveView(APIView):
    """
    API view for approving a pending article.

    POST: Sets the article's approved field to True, making it visible
          in the public news feed. Triggers the post_save signal in
          signals.py which sends email notifications to subscribers.
          Only accessible by editors.

    Endpoint: /api/articles/<id>/approve/
    """

    # Authentication required — editor check performed inside the view
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        Approve a pending article for publication.

        Sets approved=True and saves the article, which triggers the
        post_save signal to send subscriber email notifications and
        post to the internal API endpoint.

        Args:
            request: The incoming HTTP request.
            pk (int): The primary key of the article to approve.

        Returns:
            Response: Success message with HTTP 200.
                      HTTP 403 if the user is not an editor.
                      HTTP 404 if the article does not exist.
        """
        # Only editors are permitted to approve articles
        if not IsEditor().has_permission(request, self):
            return Response(
                {'error': 'Only editors can approve articles.'},
                status=status.HTTP_403_FORBIDDEN
            )

        article = get_object_or_404(Article, pk=pk)

        # Approve the article — triggers the post_save signal in signals.py
        article.approved = True
        article.save()

        return Response(
            {'message': f"Article '{article.title}' approved."},
            status=status.HTTP_200_OK
        )


# ---------------------------------------------------------------------------
# Newsletter List — GET all newsletters / POST create newsletter
# ---------------------------------------------------------------------------

class NewsletterListView(APIView):
    """
    API view for listing all newsletters and creating new newsletters.

    GET:  Returns a list of all newsletters ordered by most recent.
          Accessible by all authenticated users.

    POST: Creates a new newsletter attributed to the authenticated user.
          Only accessible by journalists and editors — readers are blocked.

    Endpoint: /api/newsletters/
    """

    # All authenticated users can access this endpoint
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return a list of all newsletters ordered by creation date.

        Args:
            request: The incoming HTTP request.

        Returns:
            Response: Serialized list of newsletters with HTTP 200.
        """
        newsletters = Newsletter.objects.all().order_by('-created_at')
        serializer = NewsletterSerializer(newsletters, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new newsletter attributed to the authenticated user.

        The author is set from request.user automatically.

        Args:
            request: The incoming HTTP request containing newsletter data.

        Returns:
            Response: Serialized newsletter data with HTTP 201 on success.
                      HTTP 403 if the user is not a journalist or editor.
                      HTTP 400 if the submitted data is invalid.
        """
        # Only journalists and editors can create newsletters
        if not IsEditorOrJournalist().has_permission(request, self):
            return Response(
                {'error': 'Only journalists or editors can create newsletters.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = NewsletterSerializer(data=request.data)

        if serializer.is_valid():
            # Set the author from the authenticated user
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Newsletter Detail — GET / PUT / DELETE a single newsletter
# ---------------------------------------------------------------------------

class NewsletterDetailView(APIView):
    """
    API view for retrieving, updating, and deleting a single newsletter.

    GET:    Returns the full newsletter data including nested articles.
            Accessible by all authenticated users.

    PUT:    Updates an existing newsletter.
            Accessible by editors (any newsletter) and journalists (own only).

    DELETE: Permanently deletes a newsletter.
            Accessible by editors (any newsletter) and journalists (own only).

    Endpoint: /api/newsletters/<id>/
    """

    # All authenticated users can GET — role checks applied per method
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Return the full data for a single newsletter including nested articles.

        Args:
            request: The incoming HTTP request.
            pk (int): The primary key of the newsletter to retrieve.

        Returns:
            Response: Serialized newsletter data with HTTP 200.
                      HTTP 404 if the newsletter does not exist.
        """
        newsletter = get_object_or_404(Newsletter, pk=pk)
        serializer = NewsletterSerializer(newsletter)
        return Response(serializer.data)

    def put(self, request, pk):
        """
        Update an existing newsletter.

        Partial updates are supported — only the provided fields are updated.

        Args:
            request: The incoming HTTP request containing updated newsletter data.
            pk (int): The primary key of the newsletter to update.

        Returns:
            Response: Serialized updated newsletter data with HTTP 200.
                      HTTP 403 if the user lacks permission.
                      HTTP 400 if the submitted data is invalid.
        """
        # Only editors and journalists can update newsletters
        if not IsEditorOrJournalist().has_permission(request, self):
            return Response(
                {'error': 'Only journalists or editors can update newsletters.'},
                status=status.HTTP_403_FORBIDDEN
            )

        newsletter = get_object_or_404(Newsletter, pk=pk)

        # Journalists can only update newsletters they authored themselves
        if request.user.role == 'journalist' and newsletter.author != request.user:
            return Response(
                {'error': 'You can only update your own newsletters.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # partial=True allows updating individual fields without requiring all fields
        serializer = NewsletterSerializer(
            newsletter,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Permanently delete a newsletter.

        Args:
            request: The incoming HTTP request.
            pk (int): The primary key of the newsletter to delete.

        Returns:
            Response: Success message with HTTP 204 No Content.
                      HTTP 403 if the user lacks permission.
                      HTTP 404 if the newsletter does not exist.
        """
        # Only editors and journalists can delete newsletters
        if not IsEditorOrJournalist().has_permission(request, self):
            return Response(
                {'error': 'Only journalists or editors can delete newsletters.'},
                status=status.HTTP_403_FORBIDDEN
            )

        newsletter = get_object_or_404(Newsletter, pk=pk)

        # Journalists can only delete newsletters they authored themselves
        if request.user.role == 'journalist' and newsletter.author != request.user:
            return Response(
                {'error': 'You can only delete your own newsletters.'},
                status=status.HTTP_403_FORBIDDEN
            )

        newsletter.delete()
        return Response(
            {'message': 'Newsletter deleted.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ---------------------------------------------------------------------------
# Current User — GET the current authenticated user's profile
# ---------------------------------------------------------------------------

class CurrentUserView(APIView):
    """
    API view for retrieving the current authenticated user's profile.

    GET: Returns the full profile of the currently authenticated user
         including their role and subscription data.
         Accessible by all authenticated users.

    Endpoint: /api/users/me/
    """

    # Authentication required — any authenticated user can access their profile
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return the profile of the currently authenticated user.

        Args:
            request: The incoming HTTP request.

        Returns:
            Response: Serialized user profile data with HTTP 200.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
# Docstrings verified
