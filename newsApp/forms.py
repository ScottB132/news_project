"""
newsApp/forms.py

Django forms for the Speedy Spectator news application.

Forms defined here:
    - ArticleForm:                 Used by journalists to create and edit articles.
                                   Excludes author and approved fields which are
                                   set server-side in the view.

    - NewsletterForm:              Used by journalists and editors to create and
                                   edit newsletters. Accepts an optional user
                                   argument to filter the articles dropdown to
                                   only show the journalist's own approved articles.

    - JournalistRegistrationForm:  Used for all role registrations (reader,
                                   journalist, editor). Extends Django's built-in
                                   UserCreationForm to include email and use the
                                   custom User model.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Newsletter, User, Publisher


# ---------------------------------------------------------------------------
# Article Form
# ---------------------------------------------------------------------------

class ArticleForm(forms.ModelForm):
    """
    Form for creating and editing news articles.

    Exposes only the title, content, and publisher fields to the user.
    The author field is intentionally excluded and set automatically in
    the view from request.user. The approved field is also excluded and
    always defaults to False until an editor approves the article.

    The publisher field is optional — an article can be written by a
    journalist independently without being associated with a publisher.
    """

    class Meta:
        model = Article

        # author is set in the view from request.user — not user-editable
        # approved defaults to False and is set by editors only
        fields = ['title', 'content', 'publisher']

    def clean(self):
        """
        Perform cross-field validation on the article form.

        Calls the parent clean() method to run Django's built-in
        field validation. Additional cross-field validation can be
        added here if required in future.

        Note: Model-level validation (author or publisher required) is
        enforced via Article.clean() which is called by full_clean()
        in the view before saving.

        Returns:
            dict: The cleaned and validated form data.
        """
        cleaned_data = super().clean()
        return cleaned_data


# ---------------------------------------------------------------------------
# Newsletter Form
# ---------------------------------------------------------------------------

class NewsletterForm(forms.ModelForm):
    """
    Form for creating and editing newsletters.

    Exposes title, description, and articles fields. Accepts an optional
    user keyword argument to filter the articles dropdown — when a user
    is provided, only their own approved articles are shown as options.

    This prevents journalists from adding other journalists' articles
    to their newsletters and ensures only approved content is included.
    """

    class Meta:
        model = Newsletter
        fields = ['title', 'description', 'articles']

    def __init__(self, *args, **kwargs):
        """
        Initialise the newsletter form with an optional user filter.

        Pops the user argument from kwargs before calling the parent
        constructor to avoid passing an unexpected keyword argument
        to Django's ModelForm.

        If a user is provided, filters the articles queryset to only
        show articles authored by that user that have been approved.
        This scopes the articles dropdown to the journalist's own content.

        Args:
            *args: Positional arguments passed to the parent constructor.
            **kwargs: Keyword arguments. Accepts an optional 'user' key
                      containing the currently authenticated user.
        """
        # Extract the user argument before passing kwargs to the parent
        # to avoid a TypeError from unexpected keyword arguments
        user = kwargs.pop('user', None)

        # Call the parent constructor to initialise the form fields
        super().__init__(*args, **kwargs)

        if user:
            # Restrict the articles dropdown to the journalist's own
            # approved articles only — prevents cross-user content mixing
            self.fields['articles'].queryset = Article.objects.filter(
                author=user,
                approved=True
            )


# ---------------------------------------------------------------------------
# Registration Form
# ---------------------------------------------------------------------------

class JournalistRegistrationForm(UserCreationForm):
    """
    Registration form used for all user roles.

    Extends Django's built-in UserCreationForm to use the custom User
    model and include the email field alongside username. Despite the
    name, this form is used for reader, journalist, and editor registration
    — the role is assigned in the view, not in the form.

    The form inherits password and password confirmation fields from
    UserCreationForm, along with all of Django's built-in password
    strength validation.

    Fields:
        username (str): The user's chosen login name.
        email (str): The user's email address.
        password1 (str): The user's chosen password.
        password2 (str): Password confirmation — must match password1.
    """

    class Meta(UserCreationForm.Meta):
        model = User

        # Include email alongside the default username field
        # Role is assigned in the view from the registration URL
        fields = ('username', 'email')


# -------------------------
# Publisher Form
# -------------------------
class PublisherForm(forms.ModelForm):
    """
    Form for creating and editing publishers.
    Used by editors to create new publishing houses.
    """
    class Meta:
        model = Publisher
        fields = ['name', 'website']
# Docstrings verified
