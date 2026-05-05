"""
newsApp/models.py

Database models for the Speedy Spectator news application.

Models defined here:
    - User:        Custom user model extending Django's AbstractUser.
                   Supports three roles: reader, journalist, and editor.
                   Readers have publisher and journalist subscriptions.
                   Journalists have articles and newsletters via reverse relations.

    - Publisher:   Represents a news organisation. Can have many journalists
                   and editors associated with it.

    - Article:     A news article written by a journalist or on behalf of
                   a publisher. Must be approved by an editor before publishing.

    - Newsletter:  A curated collection of articles created by a journalist
                   or editor. Can be viewed by all users.
"""

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Custom User Model
# ---------------------------------------------------------------------------

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Adds a role field to distinguish between readers, journalists, and editors.
    Readers have subscription fields (ManyToMany) for following publishers
    and journalists. Journalist content (articles and newsletters) is accessed
    via reverse ForeignKey relations defined on the Article and Newsletter models.

    Role behaviour:
        - reader:     Can subscribe to publishers and journalists.
                      Subscriptions are cleared if the role changes.
        - journalist: Has articles and newsletters via reverse relations.
                      Subscription fields are cleared on save.
        - editor:     Manages article approval and content moderation.
                      Subscription fields are cleared on save.

    Attributes:
        role (str): The user's role. One of 'reader', 'journalist', 'editor'.
        subscribed_publishers (ManyToManyField): Publishers the reader follows.
        subscribed_journalists (ManyToManyField): Journalists the reader follows.
    """

    # Available role choices for the role field
    ROLE_CHOICES = [
        ('journalist', 'Journalist'),
        ('reader',     'Reader'),
        ('editor',     'Editor'),
    ]

    # Role field — defaults to reader for public registrations
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='reader'
    )

    # --- Reader subscription fields ---
    # Readers can subscribe to publishers to receive article notifications
    subscribed_publishers = models.ManyToManyField(
        'Publisher',
        blank=True,
        related_name='subscribed_readers'
    )

    # Readers can subscribe to individual journalists
    # symmetrical=False means following is one-directional (not mutual)
    subscribed_journalists = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='subscribed_readers_by'
    )

    # --- Journalist reverse relations ---
    # Journalist articles are accessible via: user.articles.all()
    # (defined by related_name='articles' on Article.author ForeignKey)
    #
    # Journalist newsletters are accessible via: user.newsletters.all()
    # (defined by related_name='newsletters' on Newsletter.author ForeignKey)

    def save(self, *args, **kwargs):
        """
        Override save to enforce role-based field restrictions.

        Clears subscription fields for journalists and editors since
        these roles do not have subscriptions. This ensures the database
        stays consistent if a user's role is changed after registration.

        Args:
            *args: Positional arguments passed to the parent save method.
            **kwargs: Keyword arguments passed to the parent save method.
        """
        # Save the user first before modifying ManyToMany relationships
        super().save(*args, **kwargs)

        # Clear subscription fields for roles that don't use them
        if self.role in ('journalist', 'editor'):
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()

    def get_articles(self):
        """
        Return all articles authored by this user if they are a journalist.

        Returns:
            QuerySet: All articles by this journalist, or None if not a journalist.
        """
        if self.role == 'journalist':
            return self.articles.all()
        return None

    def get_newsletters(self):
        """
        Return all newsletters authored by this user if they are a journalist.

        Returns:
            QuerySet: All newsletters by this journalist, or None if not a journalist.
        """
        if self.role == 'journalist':
            return self.newsletters.all()
        return None

    def get_subscribed_publishers(self):
        """
        Return all publishers this user is subscribed to if they are a reader.

        Returns:
            QuerySet: Subscribed publishers, or None if not a reader.
        """
        if self.role == 'reader':
            return self.subscribed_publishers.all()
        return None

    def get_subscribed_journalists(self):
        """
        Return all journalists this user is subscribed to if they are a reader.

        Returns:
            QuerySet: Subscribed journalists, or None if not a reader.
        """
        if self.role == 'reader':
            return self.subscribed_journalists.all()
        return None

    def __str__(self):
        """Return a human-readable string representation of the user."""
        return f"{self.username} ({self.role})"


# ---------------------------------------------------------------------------
# Publisher Model
# ---------------------------------------------------------------------------

class Publisher(models.Model):
    """
    Represents a news organisation or publication house.

    Publishers can have multiple journalists and editors associated with them.
    Articles can be published on behalf of a publisher rather than
    (or in addition to) an individual journalist author.

    Attributes:
        name (str): The publisher's display name.
        website (str): An optional URL for the publisher's website.
        journalists (ManyToManyField): Journalists associated with this publisher.
        editors (ManyToManyField): Editors associated with this publisher.
    """

    # The publisher's display name — required
    name = models.CharField(max_length=100)

    # Optional website URL for the publisher
    website = models.URLField(blank=True, null=True)

    # Journalists who work for or are associated with this publisher
    journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name='publisher_journalists'
    )

    # Journalists waiting for editor approval to join
    pending_journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name='pending_publishers'
    )

    # Editors who work for or are associated with this publisher
    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name='publisher_editors'
    )

    def __str__(self):
        """Return the publisher's name as its string representation."""
        return self.name


# ---------------------------------------------------------------------------
# Article Model
# ---------------------------------------------------------------------------

class Article(models.Model):
    """
    Represents a news article on The Speedy Spectator.

    Articles must be associated with either an author (journalist) or a
    publisher — this is enforced via the clean() method. Articles are
    created as unapproved and must be reviewed and approved by an editor
    before they appear in the public news feed.

    Attributes:
        title (str): The article's headline.
        content (str): The full article body text.
        author (ForeignKey): The journalist who wrote the article. Optional.
        publisher (ForeignKey): The publisher the article is written for. Optional.
        created_at (datetime): Timestamp of when the article was created.
        approved (bool): Whether the article has been approved by an editor.
    """

    # Article headline — required
    title = models.CharField(max_length=200)

    # Full article body text — required
    content = models.TextField()

    # The journalist author — nullable to allow publisher-only articles
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='articles'
    )

    # The publisher — nullable to allow journalist-only articles
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='articles'
    )

    # Automatically set to the current time when the article is created
    created_at = models.DateTimeField(default=timezone.now)

    # All articles start as unapproved and require editor review
    approved = models.BooleanField(default=False)

    def clean(self):
        """
        Validate that the article has at least one of author or publisher.

        Called automatically by full_clean() in the view before saving.
        Raises a ValidationError if neither field is set, ensuring data
        integrity at the model level.

        Raises:
            ValidationError: If both author and publisher are None.
        """
        if not self.author and not self.publisher:
            raise ValidationError(
                "An article must have either an author or a publisher."
            )

    def __str__(self):
        """Return the article title as its string representation."""
        return self.title


# ---------------------------------------------------------------------------
# Newsletter Model
# ---------------------------------------------------------------------------

class Newsletter(models.Model):
    """
    Represents a curated newsletter created by a journalist or editor.

    Newsletters are collections of approved articles grouped together
    under a title and description. They can be created and managed by
    journalists and editors, and viewed by all users including readers.

    Attributes:
        title (str): The newsletter's title.
        description (str): An optional description of the newsletter's content.
        created_at (datetime): Timestamp of when the newsletter was created.
        author (ForeignKey): The journalist or editor who created the newsletter.
        articles (ManyToManyField): The articles included in this newsletter.
    """

    # Newsletter title — required
    title = models.CharField(max_length=200)

    # Optional description summarising the newsletter's content
    description = models.TextField(blank=True, null=True)

    # Automatically set to the current time when the newsletter is created
    created_at = models.DateTimeField(default=timezone.now)

    # The journalist or editor who created this newsletter
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='newsletters'
    )

    # The articles curated into this newsletter — optional and flexible
    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name='newsletters'
    )

    def __str__(self):
        """Return the newsletter title as its string representation."""
        return self.title

# Docstrings verified
