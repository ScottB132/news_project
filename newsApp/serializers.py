"""
newsApp/serializers.py

Django REST Framework serializers for the Speedy Spectator news application.

Serializers convert model instances to and from JSON for the REST API.
They also enforce field-level access control by marking sensitive fields
as read-only to prevent unauthorised modification via the API.

Serializer hierarchy (nested relationships):
    PublisherSerializer
        └── used inside ArticleSerializer and UserSerializer

    ArticleSerializer
        └── used inside NewsletterSerializer

    UserSerializer
        └── includes nested PublisherSerializer for subscriptions

    NewsletterSerializer
        └── includes nested ArticleSerializer for article content
"""

from rest_framework import serializers

from .models import Article, Newsletter, Publisher, User


# ---------------------------------------------------------------------------
# Publisher Serializer
# ---------------------------------------------------------------------------

class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for the Publisher model.

    Exposes basic publisher information for use in nested serializers
    and direct API responses. Used inside ArticleSerializer and
    UserSerializer to provide full publisher details rather than just
    a primary key reference.

    Fields:
        id (int): The publisher's primary key.
        name (str): The publisher's display name.
        website (str): The publisher's optional website URL.
    """

    class Meta:
        model = Publisher
        fields = ['id', 'name', 'website']


# ---------------------------------------------------------------------------
# User Serializer
# ---------------------------------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.

    Exposes user profile information including role and subscription data.
    Used by the /api/users/me/ endpoint to return the current user's details.

    The subscribed_publishers field is nested to return full publisher
    details rather than just IDs. The role field is read-only to prevent
    users from elevating their own privileges via the API.

    Fields:
        id (int): The user's primary key.
        username (str): The user's login name.
        email (str): The user's email address.
        role (str): The user's role (reader/journalist/editor). Read-only.
        subscribed_publishers (list): Nested list of subscribed publishers.
        subscribed_journalists (list): List of subscribed journalist IDs.
    """

    # Nest full publisher details instead of returning raw IDs
    subscribed_publishers = PublisherSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'subscribed_publishers',
            'subscribed_journalists',
        ]
        # Role is managed server-side and must not be changed via the API
        read_only_fields = ['role']


# ---------------------------------------------------------------------------
# Article Serializer
# ---------------------------------------------------------------------------

class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Article model.

    Used for both reading and writing article data via the REST API.
    Author is displayed as a string (username) rather than a raw ID.
    Publisher is nested to include full publisher details.

    The approved, created_at, and author fields are read-only to ensure:
        - Journalists cannot self-approve their own articles.
        - Creation timestamps are set server-side only.
        - Authors are assigned from the authenticated user in the view,
          not from the request body.

    Fields:
        id (int): The article's primary key.
        title (str): The article's headline.
        content (str): The full article body text.
        author (str): String representation of the author. Read-only.
        publisher (dict): Nested publisher details. Read-only.
        created_at (datetime): Timestamp of article creation. Read-only.
        approved (bool): Whether the article has been approved. Read-only.
    """

    # Display author as a human-readable string rather than a numeric ID
    author = serializers.StringRelatedField(read_only=True)

    # Nest full publisher details rather than returning a raw foreign key ID
    publisher = PublisherSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'content',
            'author',
            'publisher',
            'created_at',
            'approved',
        ]
        # These fields are managed server-side and must not be set via the API
        read_only_fields = ['approved', 'created_at', 'author']


# ---------------------------------------------------------------------------
# Newsletter Serializer
# ---------------------------------------------------------------------------

class NewsletterSerializer(serializers.ModelSerializer):
    """
    Serializer for the Newsletter model.

    Used for reading and writing newsletter data via the REST API.
    Author is displayed as a string and articles are fully nested so
    readers receive complete article content within the newsletter
    response without needing to make additional API requests.

    The created_at and author fields are read-only to ensure:
        - Creation timestamps are set server-side only.
        - Authors are assigned from the authenticated user in the view,
          not from the request body.

    Fields:
        id (int): The newsletter's primary key.
        title (str): The newsletter's title.
        description (str): An optional description of the newsletter.
        created_at (datetime): Timestamp of newsletter creation. Read-only.
        author (str): String representation of the author. Read-only.
        articles (list): Nested list of full article objects. Read-only.
    """

    # Display author as a human-readable string rather than a numeric ID
    author = serializers.StringRelatedField(read_only=True)

    # Nest full article details so readers get complete content in one request
    articles = ArticleSerializer(many=True, read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            'id',
            'title',
            'description',
            'created_at',
            'author',
            'articles',
        ]
        # These fields are managed server-side and must not be set via the API
        read_only_fields = ['created_at', 'author']
# Docstrings verified
