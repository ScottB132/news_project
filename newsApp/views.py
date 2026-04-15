"""
newsApp/views.py

Contains all view functions for the Speedy Spectator news application.
Views are organised into the following sections:
    - Internal API endpoint
    - Role helper functions
    - Role-based dashboard redirect
    - Authentication (login/logout)
    - Registration
    - Home and article list
    - Article management (journalist and editor)
    - Newsletter management (journalist and editor)
    - Public newsletter views
"""

import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .forms import ArticleForm, JournalistRegistrationForm, NewsletterForm
from .models import Article, Newsletter, User


# ---------------------------------------------------------------------------
# Internal API Endpoint
# ---------------------------------------------------------------------------

@csrf_exempt
def api_approved(request):
    """
    Internal RESTful API endpoint that receives approved article data.

    Accepts POST requests with JSON payload containing article details.
    Simulates a third-party integration for approved article notifications.

    Returns:
        JsonResponse: Success or error message with appropriate HTTP status.
    """
    if request.method == 'POST':
        try:
            # Parse the incoming JSON payload
            data = json.loads(request.body)
            print(f"API received approved article: {data}")

            return JsonResponse({
                'status': 'success',
                'message': f"Article '{data.get('title')}' received by API."
            }, status=200)

        except json.JSONDecodeError:
            # Return 400 if the request body is not valid JSON
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid JSON.'},
                status=400
            )

    # Only POST requests are accepted
    return JsonResponse(
        {'status': 'error', 'message': 'POST required.'},
        status=405
    )


# ---------------------------------------------------------------------------
# Role Helper Functions
# ---------------------------------------------------------------------------

def is_editor(user):
    """
    Check if a user has the editor role.

    Args:
        user: The user object to check.

    Returns:
        bool: True if the user is authenticated and has the editor role.
    """
    return user.is_authenticated and user.role == 'editor'


def is_journalist(user):
    """
    Check if a user has the journalist role.

    Args:
        user: The user object to check.

    Returns:
        bool: True if the user is authenticated and has the journalist role.
    """
    return user.is_authenticated and user.role == 'journalist'


# ---------------------------------------------------------------------------
# Role-Based Dashboard Redirect
# ---------------------------------------------------------------------------

@login_required
def dashboard_redirect(request):
    """
    Redirect authenticated users to their role-specific dashboard.

    Uses a role map to determine the correct redirect target.
    Defaults to the home page if the role is unrecognised.
    """
    # Map each role to its corresponding named URL
    role_map = {
        'editor':     'pending_articles',
        'journalist': 'journalist_dashboard',
        'reader':     'home',
    }

    # Redirect to the appropriate page, defaulting to home
    return redirect(role_map.get(request.user.role, 'home'))


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def login_user(request):
    """
    Handle user login via a POST form submission.

    Authenticates the user using Django's built-in authentication.
    On success, redirects to the role-based dashboard.
    On failure, displays an error message.
    """
    if request.method == 'POST':
        # Retrieve credentials from the submitted form
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Validate that both fields were provided
        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, 'newsApp/login_register.html')

        # Attempt to authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard_redirect')

        # Authentication failed
        messages.error(request, "Invalid username or password.")

    return render(request, 'newsApp/login_register.html')


def logout_user(request):
    """
    Log the current user out and redirect to the home page.
    """
    logout(request)
    return redirect('home')


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def _register(request, role, template='newsApp/register_journalist.html'):
    """
    Shared registration logic used by all role-specific registration views.

    Handles both GET (display form) and POST (process form) requests.
    On successful registration, logs the user in and redirects to
    their role-specific dashboard.

    Args:
        request: The HTTP request object.
        role (str): The role to assign to the new user.
        template (str): The template to render the registration form.

    Returns:
        HttpResponse: Rendered registration form or redirect on success.
    """
    form = JournalistRegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # Save the user without committing to assign the role first
        user = form.save(commit=False)
        user.role = role
        user.save()

        # Log the new user in immediately after registration
        login(request, user)
        return redirect('dashboard_redirect')

    return render(request, template, {
        'form': form,
        'role': role.capitalize()
    })


def register_reader(request):
    """Register a new user with the Reader role."""
    return _register(request, role='reader')


def register_journalist(request):
    """Register a new user with the Journalist role."""
    return _register(request, role='journalist')


@login_required
@user_passes_test(is_editor)
def register_editor(request):
    """
    Register a new user with the Editor role.
    Only accessible by existing editors.
    """
    return _register(request, role='editor')


# ---------------------------------------------------------------------------
# Home and Article List
# ---------------------------------------------------------------------------

def home(request):
    """
    Render the home page with the latest approved articles and newsletters.

    Limits the display to the 5 most recent items of each type.
    """
    context = {
        # Show only the 5 most recently approved articles
        'articles': Article.objects.filter(
            approved=True
        ).order_by('-created_at')[:5],

        # Show only the 5 most recently created newsletters
        'newsletters': Newsletter.objects.all().order_by('-created_at')[:5],
    }
    return render(request, 'newsApp/home.html', context)


def news_list(request):
    """
    Render the full news list page.

    Editors see all articles (approved and pending).
    All other users see only approved articles.
    """
    if request.user.is_authenticated and request.user.role == 'editor':
        # Editors can see all articles including unapproved ones
        articles = Article.objects.all().order_by('-created_at')
    else:
        # Readers and journalists only see approved articles
        articles = Article.objects.filter(approved=True).order_by('-created_at')

    return render(request, 'newsApp/news_list.html', {'articles': articles})


def article_detail(request, pk):
    """
    Render the full detail view for a single approved article.

    Returns a 404 if the article does not exist or is not approved.
    Unapproved articles are only accessible via the preview_article view.

    Args:
        pk (int): The primary key of the article.
    """
    article = get_object_or_404(Article, pk=pk, approved=True)
    return render(request, 'newsApp/article_detail.html', {'article': article})


# ---------------------------------------------------------------------------
# Article Management — Journalist
# ---------------------------------------------------------------------------

@login_required
def journalist_dashboard(request):
    """
    Render the journalist's personal dashboard showing their own articles.

    Only shows articles authored by the currently logged-in journalist.
    """
    articles = Article.objects.filter(
        author=request.user
    ).order_by('-created_at')

    return render(
        request,
        'newsApp/journalist_dashboard.html',
        {'articles': articles}
    )


@login_required
def create_article(request):
    """
    Allow a logged-in journalist to create a new article.

    The author is set automatically from the current user.
    The article is saved as unapproved and submitted for editor review.
    Runs full_clean() to trigger model-level validation.
    """
    form = ArticleForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # Save without committing to assign author and approval status
        article = form.save(commit=False)
        article.author = request.user
        article.approved = False  # All new articles require editor approval

        try:
            # Trigger model-level validation (e.g. author or publisher required)
            article.full_clean()
            article.save()
            messages.success(request, "Article submitted for review.")
            return redirect('journalist_dashboard')

        except ValidationError as e:
            # Attach model validation errors back to the form
            form.add_error(None, e)

    return render(request, 'newsApp/create_article.html', {'form': form})


@login_required
@user_passes_test(is_journalist)
def edit_article(request, pk):
    """
    Allow a journalist to edit one of their own articles.

    Resets the approved status to False so the article is re-reviewed
    by an editor before going live again.

    Args:
        pk (int): The primary key of the article to edit.
    """
    # Ensure the journalist can only edit their own articles
    article = get_object_or_404(Article, pk=pk, author=request.user)
    form = ArticleForm(request.POST or None, instance=article)

    if request.method == 'POST' and form.is_valid():
        article = form.save(commit=False)

        # Reset approval so the updated article goes back for review
        article.approved = False

        try:
            article.full_clean()
            article.save()
            messages.success(request, "Article updated and resubmitted for review.")
            return redirect('journalist_dashboard')

        except ValidationError as e:
            form.add_error(None, e)

    return render(request, 'newsApp/edit_article.html', {'form': form})


@login_required
@user_passes_test(is_journalist)
def delete_article(request, pk):
    """
    Allow a journalist to delete one of their own articles.

    Requires a POST request to confirm the deletion.

    Args:
        pk (int): The primary key of the article to delete.
    """
    # Ensure the journalist can only delete their own articles
    article = get_object_or_404(Article, pk=pk, author=request.user)

    if request.method == 'POST':
        article.delete()
        messages.success(request, "Article deleted.")
        return redirect('journalist_dashboard')

    return render(request, 'newsApp/delete_confirm.html', {'item': article})


# ---------------------------------------------------------------------------
# Article Management — Editor
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(is_editor)
def pending_articles(request):
    """
    Render the editor queue showing all articles awaiting approval.

    Only accessible by users with the editor role.
    """
    articles = Article.objects.filter(approved=False)
    return render(request, 'newsApp/pending_articles.html', {'articles': articles})


@login_required
@user_passes_test(is_editor)
def approve_article(request, article_id):
    """
    Allow an editor to approve a pending article for publication.

    Requires a POST request to confirm the approval.
    Triggers the post_save signal which sends email notifications.

    Args:
        article_id (int): The ID of the article to approve.
    """
    article = get_object_or_404(Article, id=article_id)

    if request.method == 'POST':
        article.approved = True
        article.save()  # Triggers the post_save signal in signals.py
        messages.success(request, f'"{article.title}" has been approved.')
        return redirect('pending_articles')

    return render(request, 'newsApp/approve_confirm.html', {'article': article})


@login_required
def preview_article(request, pk):
    """
    Allow any authenticated user to preview an article regardless of
    its approval status.

    Used by journalists to view their own pending submissions and by
    editors to review articles before approving or rejecting them.

    Args:
        pk (int): The primary key of the article to preview.
    """
    article = get_object_or_404(Article, pk=pk)
    return render(request, 'newsApp/article_detail.html', {'article': article})


@login_required
@user_passes_test(is_editor)
def reject_article(request, article_id):
    """
    Allow an editor to reject and permanently delete a pending article.

    Only pending (unapproved) articles can be rejected.
    Requires a POST request to confirm the deletion.

    Args:
        article_id (int): The ID of the article to reject.
    """
    # Only allow rejection of unapproved articles
    article = get_object_or_404(Article, id=article_id, approved=False)

    if request.method == 'POST':
        title = article.title  # Store title before deletion for the message
        article.delete()
        messages.success(request, f'"{title}" has been rejected and removed.')

    return redirect('pending_articles')


@login_required
@user_passes_test(is_editor)
def editor_edit_article(request, pk):
    """
    Allow an editor to edit any article.

    Resets the approved status to False so the article returns to the
    pending queue after editing.

    Args:
        pk (int): The primary key of the article to edit.
    """
    article = get_object_or_404(Article, pk=pk)
    form = ArticleForm(request.POST or None, instance=article)

    if request.method == 'POST' and form.is_valid():
        article = form.save(commit=False)

        # Reset approval so the edited article returns to the queue
        article.approved = False
        article.save()
        messages.success(request, "Article updated and moved to pending queue.")
        return redirect('pending_articles')

    return render(request, 'newsApp/edit_article.html', {'form': form})


@login_required
@user_passes_test(is_editor)
def editor_delete_article(request, pk):
    """
    Allow an editor to permanently delete any article.

    Requires a POST request to confirm the deletion.

    Args:
        pk (int): The primary key of the article to delete.
    """
    article = get_object_or_404(Article, pk=pk)

    if request.method == 'POST':
        article.delete()
        messages.success(request, "Article deleted.")
        return redirect('pending_articles')

    return render(request, 'newsApp/delete_confirm.html', {'item': article})


# ---------------------------------------------------------------------------
# Newsletter Management — Editor
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(is_editor)
def editor_create_newsletter(request):
    """
    Allow an editor to create a new newsletter.

    The author is set automatically from the current user.
    Saves ManyToMany article relationships after the initial save.
    """
    form = NewsletterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        newsletter = form.save(commit=False)
        newsletter.author = request.user
        newsletter.save()

        # Save ManyToMany article relationships
        form.save_m2m()
        messages.success(request, "Newsletter created.")
        return redirect('newsletter_list')

    # Show the editor's own newsletters alongside the creation form
    return render(request, 'newsApp/manage_newsletters.html', {
        'form': form,
        'newsletters': Newsletter.objects.filter(author=request.user)
    })


@login_required
@user_passes_test(is_editor)
def editor_edit_newsletter(request, pk):
    """
    Allow an editor to edit any newsletter.

    Args:
        pk (int): The primary key of the newsletter to edit.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)
    form = NewsletterForm(request.POST or None, instance=newsletter)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Newsletter updated.")
        return redirect('newsletter_list')

    return render(request, 'newsApp/edit_newsletter.html', {'form': form})


@login_required
@user_passes_test(is_editor)
def editor_delete_newsletter(request, pk):
    """
    Allow an editor to permanently delete any newsletter.

    Requires a POST request to confirm the deletion.

    Args:
        pk (int): The primary key of the newsletter to delete.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == 'POST':
        newsletter.delete()
        messages.success(request, "Newsletter deleted.")
        return redirect('newsletter_list')

    return render(request, 'newsApp/delete_confirm.html', {'item': newsletter})


# ---------------------------------------------------------------------------
# Newsletter Management — Journalist
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(is_journalist)
def manage_newsletters(request):
    """
    Allow a journalist to view and create their own newsletters.

    Displays all newsletters authored by the current journalist and
    provides a form to create a new one on the same page.
    """
    # Only show newsletters belonging to the current journalist
    newsletters = Newsletter.objects.filter(
        author=request.user
    )

    form = NewsletterForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        newsletter = form.save(commit=False)
        newsletter.author = request.user
        newsletter.save()

        # Save ManyToMany article relationships
        form.save_m2m()
        messages.success(request, "Newsletter created.")
        return redirect('manage_newsletters')

    return render(request, 'newsApp/manage_newsletters.html', {
        'newsletters': newsletters,
        'form': form,
    })


@login_required
@user_passes_test(is_journalist)
def update_newsletter(request, pk):
    """
    Allow a journalist to update one of their own newsletters.

    Args:
        pk (int): The primary key of the newsletter to update.
    """
    # Ensure journalists can only edit their own newsletters
    newsletter = get_object_or_404(Newsletter, pk=pk, author=request.user)
    form = NewsletterForm(request.POST or None, instance=newsletter, user=request.user)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Newsletter updated.")
        return redirect('manage_newsletters')

    return render(request, 'newsApp/edit_newsletter.html', {'form': form})


@login_required
@user_passes_test(is_journalist)
def delete_newsletter(request, pk):
    """
    Allow a journalist to delete one of their own newsletters.

    Requires a POST request to confirm the deletion.

    Args:
        pk (int): The primary key of the newsletter to delete.
    """
    # Ensure journalists can only delete their own newsletters
    newsletter = get_object_or_404(Newsletter, pk=pk, author=request.user)

    if request.method == 'POST':
        newsletter.delete()
        messages.success(request, "Newsletter deleted.")
        return redirect('manage_newsletters')

    return render(request, 'newsApp/delete_confirm.html', {'item': newsletter})


# ---------------------------------------------------------------------------
# Public Newsletter Views
# ---------------------------------------------------------------------------

def newsletter_list(request):
    """
    Render the public newsletter list page showing all newsletters.

    Accessible by all users including unauthenticated visitors.
    """
    newsletters = Newsletter.objects.all().order_by('-created_at')
    return render(
        request,
        'newsApp/newsletter_list.html',
        {'newsletters': newsletters}
    )


def newsletter_detail(request, pk):
    """
    Render the full detail view for a single newsletter.

    Returns a 404 if the newsletter does not exist.

    Args:
        pk (int): The primary key of the newsletter to display.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(
        request,
        'newsApp/newsletter_detail.html',
        {'newsletter': newsletter}
    )