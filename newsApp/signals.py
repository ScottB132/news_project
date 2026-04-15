"""
newsApp/signals.py

Django signal handlers for the Speedy Spectator news application.

Contains three signal handlers:
    - create_groups: Creates Reader, Editor, and Journalist permission
      groups after each migration run.
    - assign_user_group: Automatically assigns new users to their
      corresponding permission group based on their role.
    - article_approved: Fires when an article is approved by an editor.
      Sends email notifications to subscribers and posts to the
      internal REST API endpoint to simulate third-party integration.
"""

import requests

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import Article, Newsletter, User


# ---------------------------------------------------------------------------
# Permission Group Creation
# ---------------------------------------------------------------------------

@receiver(post_migrate)
def create_groups(sender, **kwargs):
    """
    Create and configure user permission groups after each migration.

    Runs automatically after every migration but only processes the
    newsApp application to avoid unnecessary database operations.

    Permission assignments:
        - Reader:     view only
        - Editor:     view, change, delete
        - Journalist: view, add, change, delete (all permissions)

    Args:
        sender: The app that triggered the post_migrate signal.
        **kwargs: Additional keyword arguments from the signal.
    """
    # Only run this signal handler for the newsApp application
    if sender.name != 'newsApp':
        return

    # Get content types for the models we want to assign permissions for
    article_ct = ContentType.objects.get_for_model(Article)
    newsletter_ct = ContentType.objects.get_for_model(Newsletter)

    # Fetch all permissions related to Article and Newsletter models
    perms = Permission.objects.filter(
        content_type__in=[article_ct, newsletter_ct]
    )

    # Create groups if they don't already exist
    reader_group, _     = Group.objects.get_or_create(name='Reader')
    editor_group, _     = Group.objects.get_or_create(name='Editor')
    journalist_group, _ = Group.objects.get_or_create(name='Journalist')

    # Clear existing permissions to prevent duplicates on re-migration
    reader_group.permissions.clear()
    editor_group.permissions.clear()
    journalist_group.permissions.clear()

    # Assign permissions based on the role specification
    for perm in perms:
        # Readers can only view articles and newsletters
        if perm.codename.startswith('view'):
            reader_group.permissions.add(perm)

        # Editors can view, update, and delete articles and newsletters
        if perm.codename.startswith(('view', 'change', 'delete')):
            editor_group.permissions.add(perm)

        # Journalists have full access: create, view, update, and delete
        journalist_group.permissions.add(perm)


# ---------------------------------------------------------------------------
# User Group Assignment
# ---------------------------------------------------------------------------

@receiver(post_save, sender=User)
def assign_user_group(sender, instance, created, **kwargs):
    """
    Automatically assign a new user to their corresponding permission group.

    Runs after a User object is saved. Only processes newly created users
    to avoid reassigning groups when existing user data is updated.

    Maps user roles to Django permission groups:
        - reader     → Reader group
        - journalist → Journalist group
        - editor     → Editor group

    Args:
        sender: The model class that sent the signal (User).
        instance (User): The user instance that was saved.
        created (bool): True if this is a new user, False if updating.
        **kwargs: Additional keyword arguments from the signal.
    """
    # Only assign groups to newly created users
    if not created:
        return

    # Map role strings to their corresponding group names
    role_to_group = {
        'reader':     'Reader',
        'journalist': 'Journalist',
        'editor':     'Editor',
    }

    # Look up the group name for this user's role
    group_name = role_to_group.get(instance.role)

    if group_name:
        # Fetch the group — filter used instead of get to avoid exceptions
        # if the group hasn't been created yet (e.g. before first migration)
        group = Group.objects.filter(name=group_name).first()

        if group:
            instance.groups.add(group)


# ---------------------------------------------------------------------------
# Article Approval Signal
# ---------------------------------------------------------------------------

def _collect_subscriber_emails(instance):
    """
    Collect email addresses of all readers subscribed to the article's
    journalist or publisher.

    Uses a set to automatically deduplicate emails in case a reader
    is subscribed to both the journalist and the publisher.

    Args:
        instance (Article): The approved article instance.

    Returns:
        set: A set of unique subscriber email addresses.
    """
    subscriber_emails = set()

    # Collect emails from readers subscribed to the article's author
    if instance.author:
        journalist_subscribers = User.objects.filter(
            subscribed_journalists=instance.author,
            role='reader'
        )
        for reader in journalist_subscribers:
            if reader.email:
                subscriber_emails.add(reader.email)

    # Collect emails from readers subscribed to the article's publisher
    if instance.publisher:
        publisher_subscribers = User.objects.filter(
            subscribed_publishers=instance.publisher,
            role='reader'
        )
        for reader in publisher_subscribers:
            if reader.email:
                subscriber_emails.add(reader.email)

    return subscriber_emails


def _send_approval_emails(instance, subscriber_emails):
    """
    Send email notifications to all subscribers of the approved article.

    Uses fail_silently=True so email failures do not interrupt the
    article approval process.

    In development, emails are printed to the console via the
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    setting in settings.py.

    Args:
        instance (Article): The approved article instance.
        subscriber_emails (set): Set of recipient email addresses.
    """
    if not subscriber_emails:
        return

    # Determine the author display name for the email body
    author_display = (
        instance.author.username if instance.author else 'Publisher'
    )

    send_mail(
        subject=f"New Article: {instance.title}",
        message=(
            f"A new article has been published on The Speedy Spectator.\n\n"
            f"Title: {instance.title}\n"
            f"Author: {author_display}\n\n"
            f"Visit the site to read the full article."
        ),
        from_email='noreply@speedyspectator.com',
        recipient_list=list(subscriber_emails),
        fail_silently=True,  # Do not raise exceptions on email failure
    )

    print(f"Emails sent to: {subscriber_emails}")


def _post_to_internal_api(instance):
    """
    Send a POST request to the internal REST API endpoint to simulate
    a third-party integration when an article is approved.

    Constructs a JSON payload with the article details and posts it
    to /news/api/approved/. Handles connection errors gracefully so
    that API failures do not interrupt the approval process.

    Args:
        instance (Article): The approved article instance.
    """
    # Build the payload with article details
    payload = {
        'title':     instance.title,
        'author':    instance.author.username if instance.author else None,
        'publisher': str(instance.publisher) if instance.publisher else None,
        'approved':  instance.approved,
    }

    try:
        response = requests.post(
            'http://127.0.0.1:8000/news/api/approved/',
            json=payload,
            timeout=5,  # Fail fast if the server is unavailable
        )
        print(f"API response: {response.status_code} — {response.json()}")

    except requests.exceptions.RequestException as e:
        # Log the failure but do not raise — approval should not be blocked
        print(f"API call failed: {e}")


@receiver(post_save, sender=Article)
def article_approved(sender, instance, created, **kwargs):
    """
    Handle post-save signal for Article — fires when an article is approved.

    Triggered every time an Article is saved. Only processes the approval
    event (i.e. when an existing article has approved=True). Skips newly
    created articles since they are always created as unapproved.

    On approval:
        1. Collects subscriber emails from the article's journalist
           and publisher subscriptions.
        2. Sends email notifications to all subscribers.
        3. Posts article data to the internal REST API endpoint.

    Args:
        sender: The model class that sent the signal (Article).
        instance (Article): The article instance that was saved.
        created (bool): True if this is a new article, False if updating.
        **kwargs: Additional keyword arguments from the signal.
    """
    # Skip newly created articles — they are always unapproved on creation
    if created:
        return

    # Skip if the article has not been approved
    if not instance.approved:
        return

    # Step 1: Collect all subscriber emails
    subscriber_emails = _collect_subscriber_emails(instance)

    # Step 2: Send email notifications to subscribers
    _send_approval_emails(instance, subscriber_emails)

    # Step 3: Notify the internal API endpoint
    _post_to_internal_api(instance)
