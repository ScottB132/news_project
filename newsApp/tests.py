"""
newsApp/tests.py

Automated unit tests for the Speedy Spectator REST API.

Test coverage includes:
    - Authentication (JWT token access per role)
    - Article list, detail, create, approve, and delete
    - Subscription-based article retrieval for readers
    - Newsletter list, create, update, and delete
    - Django signal logic (email and internal API call on approval)
    - Internal API endpoint behaviour

Each test class covers a specific area of functionality.
Both successful and failed requests are tested to ensure
correct access control and error handling.
"""

import json

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

from .models import Article, Newsletter, Publisher, User


# ---------------------------------------------------------------------------
# Base Test Case
# ---------------------------------------------------------------------------

class BaseTestCase(TestCase):
    """
    Base test case providing shared setup for all test classes.

    Creates a standard set of test users, articles, and newsletters
    that can be reused across all test classes to avoid repetition.
    """

    def setUp(self):
        """
        Set up test data before each test method runs.

        Creates:
            - One publisher
            - One reader, two journalists, one editor
            - Two articles (one approved, one pending) by journalist1
            - One approved article by journalist2
            - One newsletter by journalist1 containing the approved article
        """
        # Use the DRF API client for all requests
        self.client = APIClient()

        # --- Create a test publisher ---
        self.publisher = Publisher.objects.create(
            name="Test Publisher",
            website="http://testpublisher.com"
        )

        # --- Create test users with distinct roles ---
        self.reader = User.objects.create_user(
            username='reader1',
            password='testpass123',
            email='reader@test.com',
            role='reader'
        )
        self.journalist = User.objects.create_user(
            username='journalist1',
            password='testpass123',
            email='journalist@test.com',
            role='journalist'
        )
        # Second journalist used to test cross-user access restrictions
        self.journalist2 = User.objects.create_user(
            username='journalist2',
            password='testpass123',
            email='journalist2@test.com',
            role='journalist'
        )
        self.editor = User.objects.create_user(
            username='editor1',
            password='testpass123',
            email='editor@test.com',
            role='editor'
        )

        # --- Create test articles ---

        # Approved article — should be visible in public API responses
        self.approved_article = Article.objects.create(
            title='Approved Article',
            content='This article is approved.',
            author=self.journalist,
            approved=True
        )

        # Pending article — should be hidden from public API responses
        self.pending_article = Article.objects.create(
            title='Pending Article',
            content='This article is pending.',
            author=self.journalist,
            approved=False
        )

        # Article by journalist2 — used to test cross-user access restrictions
        self.other_article = Article.objects.create(
            title='Other Journalist Article',
            content='Written by journalist2.',
            author=self.journalist2,
            approved=True
        )

        # --- Create a test newsletter with one article ---
        self.newsletter = Newsletter.objects.create(
            title='Test Newsletter',
            description='A test newsletter.',
            author=self.journalist
        )
        self.newsletter.articles.add(self.approved_article)

    def get_token(self, username, password):
        """
        Retrieve a JWT access token for the given credentials.

        Args:
            username (str): The username to authenticate with.
            password (str): The password to authenticate with.

        Returns:
            str: The JWT access token string.
        """
        url = reverse('token_obtain_pair')
        response = self.client.post(
            url,
            {'username': username, 'password': password},
            format='json'
        )
        return response.data['access']

    def auth(self, user, password='testpass123'):
        """
        Authenticate the API client as the given user.

        Sets the Authorization header with a fresh JWT token
        so subsequent requests are made as that user.

        Args:
            user (User): The user to authenticate as.
            password (str): The user's password. Defaults to 'testpass123'.
        """
        token = self.get_token(user.username, password)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------

class AuthenticationTests(BaseTestCase):
    """
    Tests for JWT token authentication.

    Verifies that:
        - Unauthenticated requests are rejected
        - All roles can obtain a valid token
        - Invalid credentials are rejected
    """

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests should return 401 Unauthorized."""
        # Make a request without setting any credentials
        response = self.client.get(reverse('api_article_list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reader_can_authenticate(self):
        """Reader should receive a valid JWT token on correct credentials."""
        token = self.get_token('reader1', 'testpass123')
        self.assertIsNotNone(token)

    def test_journalist_can_authenticate(self):
        """Journalist should receive a valid JWT token on correct credentials."""
        token = self.get_token('journalist1', 'testpass123')
        self.assertIsNotNone(token)

    def test_editor_can_authenticate(self):
        """Editor should receive a valid JWT token on correct credentials."""
        token = self.get_token('editor1', 'testpass123')
        self.assertIsNotNone(token)

    def test_invalid_credentials_denied(self):
        """Incorrect password should return 401 Unauthorized."""
        url = reverse('token_obtain_pair')
        response = self.client.post(
            url,
            {'username': 'reader1', 'password': 'wrongpassword'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Article List Tests
# ---------------------------------------------------------------------------

class ArticleListTests(BaseTestCase):
    """
    Tests for GET /api/articles/ — the public approved article list.

    Verifies that:
        - All authenticated roles can retrieve the article list
        - Only approved articles are returned
        - Unapproved articles are excluded
    """

    def test_reader_can_get_articles(self):
        """Authenticated reader should receive a 200 response with approved articles."""
        self.auth(self.reader)
        response = self.client.get(reverse('api_article_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Confirm every article in the response is approved
        for article in response.data:
            self.assertTrue(
                article['approved'],
                "Non-approved article found in public article list."
            )

    def test_unapproved_articles_not_in_list(self):
        """Pending articles should not appear in the public article list."""
        self.auth(self.reader)
        response = self.client.get(reverse('api_article_list'))
        titles = [a['title'] for a in response.data]
        self.assertNotIn('Pending Article', titles)

    def test_journalist_can_get_articles(self):
        """Authenticated journalist should receive a 200 response."""
        self.auth(self.journalist)
        response = self.client.get(reverse('api_article_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_editor_can_get_articles(self):
        """Authenticated editor should receive a 200 response."""
        self.auth(self.editor)
        response = self.client.get(reverse('api_article_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Article Detail Tests
# ---------------------------------------------------------------------------

class ArticleDetailTests(BaseTestCase):
    """
    Tests for GET /api/articles/<id>/ — single article retrieval.

    Verifies that:
        - Approved articles can be retrieved by authenticated users
        - Unapproved articles return 404
    """

    def test_reader_can_get_single_article(self):
        """Reader should retrieve correct data for an approved article."""
        self.auth(self.reader)
        response = self.client.get(
            reverse('api_article_detail', args=[self.approved_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Approved Article')

    def test_unapproved_article_returns_404(self):
        """Requesting an unapproved article should return 404 Not Found."""
        self.auth(self.reader)
        response = self.client.get(
            reverse('api_article_detail', args=[self.pending_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Article Create Tests
# ---------------------------------------------------------------------------

class ArticleCreateTests(BaseTestCase):
    """
    Tests for POST /api/articles/ — article creation.

    Verifies that:
        - Journalists can create articles
        - New articles are saved as unapproved
        - Author is set correctly from the authenticated user
        - Readers and editors are blocked from creating articles
    """

    def test_journalist_can_create_article(self):
        """Journalist should receive 201 Created on valid article submission."""
        self.auth(self.journalist)
        response = self.client.post(
            reverse('api_article_list'),
            {'title': 'New Article', 'content': 'New content.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Article')

        # New articles must require editor approval before going live
        self.assertFalse(
            response.data['approved'],
            "Newly created article should not be approved automatically."
        )

    def test_reader_cannot_create_article(self):
        """Reader should receive 403 Forbidden when attempting to create an article."""
        self.auth(self.reader)
        response = self.client.post(
            reverse('api_article_list'),
            {'title': 'Hack Article', 'content': 'Should fail.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_cannot_create_article(self):
        """Editor should receive 403 Forbidden when attempting to create an article."""
        self.auth(self.editor)
        response = self.client.post(
            reverse('api_article_list'),
            {'title': 'Editor Article', 'content': 'Should fail.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_article_created_with_correct_author(self):
        """Created article should be attributed to the authenticated journalist."""
        self.auth(self.journalist)
        response = self.client.post(
            reverse('api_article_list'),
            {'title': 'Authored Article', 'content': 'Content.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Author should match the authenticated journalist's string representation
        self.assertEqual(response.data['author'], str(self.journalist))


# ---------------------------------------------------------------------------
# Article Approve Tests
# ---------------------------------------------------------------------------

class ArticleApproveTests(BaseTestCase):
    """
    Tests for POST /api/articles/<id>/approve/ — article approval.

    Verifies that:
        - Editors can approve pending articles
        - Journalists and readers are blocked from approving articles
        - The approved field is correctly set to True after approval
    """

    def test_editor_can_approve_article(self):
        """Editor should be able to approve a pending article."""
        self.auth(self.editor)
        response = self.client.post(
            reverse('api_article_approve', args=[self.pending_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh from database to confirm the change was saved
        self.pending_article.refresh_from_db()
        self.assertTrue(
            self.pending_article.approved,
            "Article should be marked as approved after editor action."
        )

    def test_journalist_cannot_approve_article(self):
        """Journalist should receive 403 Forbidden when attempting to approve."""
        self.auth(self.journalist)
        response = self.client.post(
            reverse('api_article_approve', args=[self.pending_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reader_cannot_approve_article(self):
        """Reader should receive 403 Forbidden when attempting to approve."""
        self.auth(self.reader)
        response = self.client.post(
            reverse('api_article_approve', args=[self.pending_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Article Delete Tests
# ---------------------------------------------------------------------------

class ArticleDeleteTests(BaseTestCase):
    """
    Tests for DELETE /api/articles/<id>/ — article deletion.

    Verifies that:
        - Editors can delete any article
        - Journalists can delete their own articles
        - Journalists cannot delete another journalist's articles
        - Readers cannot delete articles
    """

    def test_editor_can_delete_article(self):
        """Editor should be able to delete any article."""
        self.auth(self.editor)
        response = self.client.delete(
            reverse('api_article_detail', args=[self.approved_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Confirm the article no longer exists in the database
        self.assertFalse(
            Article.objects.filter(pk=self.approved_article.pk).exists(),
            "Article should be permanently deleted from the database."
        )

    def test_journalist_can_delete_own_article(self):
        """Journalist should be able to delete their own article."""
        self.auth(self.journalist)
        response = self.client.delete(
            reverse('api_article_detail', args=[self.pending_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_journalist_cannot_delete_others_article(self):
        """Journalist should receive 403 Forbidden when deleting another's article."""
        self.auth(self.journalist)
        response = self.client.delete(
            reverse('api_article_detail', args=[self.other_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reader_cannot_delete_article(self):
        """Reader should receive 403 Forbidden when attempting to delete."""
        self.auth(self.reader)
        response = self.client.delete(
            reverse('api_article_detail', args=[self.approved_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Subscription Tests
# ---------------------------------------------------------------------------

class SubscriptionTests(BaseTestCase):
    """
    Tests for GET /api/articles/subscribed/ — subscription-based article feed.

    Verifies that:
        - Readers receive articles from subscribed journalists
        - Readers receive articles from subscribed publishers
        - Readers do not receive articles from unsubscribed sources
        - Unapproved articles are excluded from the subscribed feed
        - Journalists and editors cannot access the subscribed endpoint
    """

    def setUp(self):
        """
        Extend base setup with subscription-specific test data.

        Subscribes the reader to journalist1 and the test publisher,
        and creates an article from the subscribed publisher.
        """
        super().setUp()

        # Subscribe the reader to journalist1 and the test publisher
        self.reader.subscribed_journalists.add(self.journalist)
        self.reader.subscribed_publishers.add(self.publisher)

        # Create an approved article from the subscribed publisher
        self.publisher_article = Article.objects.create(
            title='Publisher Article',
            content='From subscribed publisher.',
            publisher=self.publisher,
            approved=True
        )

    def test_reader_gets_subscribed_articles(self):
        """Reader should receive articles from their subscribed journalist."""
        self.auth(self.reader)
        response = self.client.get(reverse('api_subscribed_articles'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a['title'] for a in response.data]
        self.assertIn(
            'Approved Article', titles,
            "Subscribed journalist's article should appear in the feed."
        )

    def test_reader_gets_publisher_articles(self):
        """Reader should receive articles from their subscribed publisher."""
        self.auth(self.reader)
        response = self.client.get(reverse('api_subscribed_articles'))
        titles = [a['title'] for a in response.data]
        self.assertIn(
            'Publisher Article', titles,
            "Subscribed publisher's article should appear in the feed."
        )

    def test_reader_does_not_get_unsubscribed_articles(self):
        """Reader should not receive articles from unsubscribed sources."""
        self.auth(self.reader)
        response = self.client.get(reverse('api_subscribed_articles'))
        titles = [a['title'] for a in response.data]
        self.assertNotIn(
            'Other Journalist Article', titles,
            "Unsubscribed journalist's article should not appear in the feed."
        )

    def test_journalist_cannot_access_subscribed_endpoint(self):
        """Journalist should receive 403 Forbidden on the subscribed endpoint."""
        self.auth(self.journalist)
        response = self.client.get(reverse('api_subscribed_articles'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_cannot_access_subscribed_endpoint(self):
        """Editor should receive 403 Forbidden on the subscribed endpoint."""
        self.auth(self.editor)
        response = self.client.get(reverse('api_subscribed_articles'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unapproved_articles_excluded_from_subscriptions(self):
        """Unapproved articles should not appear in the subscribed feed."""
        self.auth(self.reader)
        response = self.client.get(reverse('api_subscribed_articles'))
        titles = [a['title'] for a in response.data]
        self.assertNotIn(
            'Pending Article', titles,
            "Unapproved article should be excluded from the subscribed feed."
        )


# ---------------------------------------------------------------------------
# Newsletter Tests
# ---------------------------------------------------------------------------

class NewsletterTests(BaseTestCase):
    """
    Tests for newsletter API endpoints.

    Verifies that:
        - All authenticated users can retrieve newsletters
        - Newsletters include nested article data
        - Journalists and editors can create newsletters
        - Readers cannot create newsletters
        - Journalists can update their own newsletters
        - Journalists cannot update another journalist's newsletter
        - Editors can delete any newsletter
        - Readers cannot delete newsletters
    """

    def test_reader_can_get_newsletters(self):
        """Reader should receive a list of all newsletters."""
        self.auth(self.reader)
        response = self.client.get(reverse('api_newsletter_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_newsletter_contains_articles(self):
        """Newsletter response should include nested article data."""
        self.auth(self.reader)
        response = self.client.get(reverse('api_newsletter_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Confirm the newsletter contains exactly one nested article
        self.assertEqual(len(response.data[0]['articles']), 1)
        self.assertEqual(
            response.data[0]['articles'][0]['title'],
            'Approved Article'
        )

    def test_journalist_can_create_newsletter(self):
        """Journalist should receive 201 Created on valid newsletter submission."""
        self.auth(self.journalist)
        response = self.client.post(
            reverse('api_newsletter_list'),
            {'title': 'New Newsletter', 'description': 'Test description.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Newsletter')

    def test_editor_can_create_newsletter(self):
        """Editor should receive 201 Created on valid newsletter submission."""
        self.auth(self.editor)
        response = self.client.post(
            reverse('api_newsletter_list'),
            {'title': 'Editor Newsletter', 'description': 'By editor.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_reader_cannot_create_newsletter(self):
        """Reader should receive 403 Forbidden when attempting to create a newsletter."""
        self.auth(self.reader)
        response = self.client.post(
            reverse('api_newsletter_list'),
            {'title': 'Reader Newsletter', 'description': 'Should fail.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_journalist_can_update_own_newsletter(self):
        """Journalist should be able to update their own newsletter."""
        self.auth(self.journalist)
        response = self.client.put(
            reverse('api_newsletter_detail', args=[self.newsletter.pk]),
            {'title': 'Updated Newsletter', 'description': 'Updated.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Newsletter')

    def test_journalist_cannot_update_others_newsletter(self):
        """Journalist should receive 403 Forbidden when updating another's newsletter."""
        self.auth(self.journalist2)
        response = self.client.put(
            reverse('api_newsletter_detail', args=[self.newsletter.pk]),
            {'title': 'Hacked Newsletter', 'description': 'Should fail.'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_can_delete_newsletter(self):
        """Editor should be able to delete any newsletter."""
        self.auth(self.editor)
        response = self.client.delete(
            reverse('api_newsletter_detail', args=[self.newsletter.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Confirm the newsletter no longer exists in the database
        self.assertFalse(
            Newsletter.objects.filter(pk=self.newsletter.pk).exists(),
            "Newsletter should be permanently deleted from the database."
        )

    def test_reader_cannot_delete_newsletter(self):
        """Reader should receive 403 Forbidden when attempting to delete a newsletter."""
        self.auth(self.reader)
        response = self.client.delete(
            reverse('api_newsletter_detail', args=[self.newsletter.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Signal Tests
# ---------------------------------------------------------------------------

class SignalTests(BaseTestCase):
    """
    Tests for Django signal logic triggered on article approval.

    Verifies that:
        - Email is sent to subscribers when an article is approved
        - Email is NOT sent when an article is first created
        - Internal API endpoint is called when an article is approved
        - Publisher subscribers receive email notifications

    Uses unittest.mock.patch to mock external dependencies (email and HTTP)
    so tests run without requiring real email or network connections.
    """

    def setUp(self):
        """
        Extend base setup by subscribing the reader to journalist1.
        """
        super().setUp()

        # Subscribe the reader to journalist1 so they receive notifications
        self.reader.subscribed_journalists.add(self.journalist)
        self.reader.email = 'reader@test.com'
        self.reader.save()

    @patch('newsApp.signals.send_mail')
    def test_email_sent_on_approval(self, mock_send_mail):
        """
        Email should be sent to subscribers when an article is approved.

        Mocks send_mail to avoid sending real emails during testing.
        """
        # Approve the pending article to trigger the signal
        self.pending_article.approved = True
        self.pending_article.save()

        # Confirm send_mail was called at least once
        self.assertTrue(
            mock_send_mail.called,
            "send_mail should be called when an article is approved."
        )

    @patch('newsApp.signals.send_mail')
    def test_email_not_sent_on_create(self, mock_send_mail):
        """
        Email should NOT be sent when an article is first created.

        The signal should only fire on approval, not on initial creation.
        """
        # Create a new unapproved article
        Article.objects.create(
            title='Brand New Article',
            content='Just created.',
            author=self.journalist,
            approved=False
        )

        # Confirm send_mail was not called
        self.assertFalse(
            mock_send_mail.called,
            "send_mail should not be called when an article is first created."
        )

    @patch('newsApp.signals.requests.post')
    def test_api_called_on_approval(self, mock_post):
        """
        Internal API endpoint should be called when an article is approved.

        Mocks requests.post to avoid making real HTTP requests during testing.
        """
        # Set up mock response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'status': 'success'}

        # Approve the article to trigger the signal
        self.pending_article.approved = True
        self.pending_article.save()

        # Confirm requests.post was called
        self.assertTrue(
            mock_post.called,
            "requests.post should be called when an article is approved."
        )

        # Confirm the correct endpoint was called
        call_args = mock_post.call_args
        self.assertIn(
            'api/approved',
            call_args[0][0],
            "The internal /api/approved/ endpoint should be the target."
        )

    @patch('newsApp.signals.requests.post')
    @patch('newsApp.signals.send_mail')
    def test_email_sent_to_publisher_subscribers(self, mock_send_mail, mock_post):
        """
        Email should be sent to readers subscribed to the article's publisher.

        Creates a reader subscribed to the test publisher and verifies
        that send_mail is called when a publisher article is approved.
        """
        # Set up mock API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'status': 'success'}

        # Create a reader subscribed to the test publisher
        publisher_reader = User.objects.create_user(
            username='pub_reader',
            password='testpass123',
            email='pubreader@test.com',
            role='reader'
        )
        publisher_reader.subscribed_publishers.add(self.publisher)
        publisher_reader.save()

        # Create and then approve a publisher article to trigger the signal
        article = Article.objects.create(
            title='Publisher Approved Article',
            content='From publisher.',
            publisher=self.publisher,
            approved=False
        )
        article.approved = True
        article.save()

        # Confirm send_mail was called for the publisher subscriber
        self.assertTrue(
            mock_send_mail.called,
            "send_mail should be called for readers subscribed to the publisher."
        )


# ---------------------------------------------------------------------------
# Internal API Endpoint Tests
# ---------------------------------------------------------------------------

class InternalAPITests(TestCase):
    """
    Tests for the internal POST /api/approved/ endpoint.

    Verifies that:
        - Valid POST requests return 200 with a success response
        - GET requests are rejected with 405 Method Not Allowed
        - Invalid JSON returns 400 Bad Request
    """

    def setUp(self):
        """Set up the API client for internal endpoint tests."""
        self.client = APIClient()

    def test_api_approved_endpoint_accepts_post(self):
        """Valid POST request should return 200 with a success status."""
        response = self.client.post(
            '/news/api/approved/',
            {'title': 'Test', 'author': 'journalist1', 'approved': True},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse the response content and verify the status field
        data = json.loads(response.content)
        self.assertEqual(
            data['status'],
            'success',
            "Response should contain status: success."
        )

    def test_api_approved_endpoint_rejects_get(self):
        """GET request should return 405 Method Not Allowed."""
        response = self.client.get('/news/api/approved/')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_api_approved_endpoint_rejects_invalid_json(self):
        """Invalid JSON body should return 400 Bad Request."""
        response = self.client.post(
            '/news/api/approved/',
            'not valid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
