"""
newsApp/urls.py

URL configuration for the Speedy Spectator news application.

URL patterns are organised into the following sections:
    - Home
    - News and article views
    - Article management (journalist and editor actions)
    - Newsletter views and management
    - Authentication (login and logout)
    - User registration
    - Dashboards and redirects
    - Internal API endpoint
    - REST API endpoints (JWT authentication required)
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import api_views, views

urlpatterns = [

    # ---------------------------------------------------------------------------
    # Home
    # ---------------------------------------------------------------------------
    path('', views.home, name='home'),

    # ---------------------------------------------------------------------------
    # News — public article browsing
    # ---------------------------------------------------------------------------

    # Full news list (editors see all, others see approved only)
    path('news/', views.ArticleListView.as_view(), name='news_list'),

    # Full article detail — approved articles only
    path('article/<int:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),

    # Article preview — any authenticated user, no approval filter
    path('article/<int:pk>/preview/', views.preview_article, name='preview_article'),

    # ---------------------------------------------------------------------------
    # Article Management — shared journalist and editor actions
    # ---------------------------------------------------------------------------

    # Journalist: create a new article
    path('create-article/', views.create_article, name='create_article'),

    # Journalist: edit their own article (resets to pending)
    path('article/<int:pk>/edit/', views.edit_article, name='edit_article'),

    # Journalist: delete their own article
    path('article/<int:pk>/delete/', views.delete_article, name='delete_article'),

    # Editor: view all pending articles awaiting approval
    path('pending/', views.pending_articles, name='pending_articles'),

    # Editor: approve a pending article for publication
    path('approve/<int:article_id>/', views.approve_article, name='approve_article'),

    # Editor: reject and permanently delete a pending article
    path('reject/<int:article_id>/', views.reject_article, name='reject_article'),

    # Editor: edit any article (resets to pending)
    path('article/<int:pk>/editor-edit/', views.editor_edit_article, name='editor_edit_article'),

    # Editor: delete any article
    path('article/<int:pk>/editor-delete/', views.editor_delete_article, name='editor_delete_article'),

    # ---------------------------------------------------------------------------
    # Newsletters — public views
    # Note: static paths (all/, create/) must come before dynamic paths (<int:pk>/)
    # to prevent Django matching 'all' or 'create' as integer primary keys
    # ---------------------------------------------------------------------------

    # Public newsletter list — visible to all users
    path('newsletters/all/', views.newsletter_list, name='newsletter_list'),

    # Editor: create a new newsletter
    path('newsletters/create/', views.editor_create_newsletter, name='editor_create_newsletter'),

    # Journalist: manage (view and create) their own newsletters
    path('newsletters/', views.manage_newsletters, name='manage_newsletters'),

    # Journalist: edit their own newsletter
    path('newsletters/edit/<int:pk>/', views.update_newsletter, name='update_newsletter'),

    # Journalist: delete their own newsletter
    path('newsletters/delete/<int:pk>/', views.delete_newsletter, name='delete_newsletter'),

    # Public newsletter detail — single newsletter view
    path('newsletters/<int:pk>/', views.newsletter_detail, name='newsletter_detail'),

    # Editor: edit any newsletter
    path('newsletters/<int:pk>/editor-edit/', views.editor_edit_newsletter, name='editor_edit_newsletter'),

    # Editor: delete any newsletter
    path('newsletters/<int:pk>/editor-delete/', views.editor_delete_newsletter, name='editor_delete_newsletter'),

    path('newsletters/all/', views.NewsletterListView.as_view(), name='newsletter_list'),
    path('newsletters/<int:pk>/', views.NewsletterDetailView.as_view(), name='newsletter_detail'),

    # ---------------------------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------------------------

    # Unified login page for all roles
    path('login/', views.login_user, name='login_user'),

    # Logout and redirect to home
    path('logout/', views.logout_user, name='logout_user'),

    # ---------------------------------------------------------------------------
    # Registration
    # ---------------------------------------------------------------------------

    # Public registration for readers
    path('register/reader/', views.register_reader, name='register_reader'),

    # Public registration for journalists
    path('register/journalist/', views.register_journalist, name='register_journalist'),

    # Restricted registration for editors — existing editors only
    path('register/editor/', views.register_editor, name='register_editor'),

    # ---------------------------------------------------------------------------
    # Dashboards and Redirects
    # ---------------------------------------------------------------------------

    # Role-based redirect — sends users to their appropriate dashboard
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),

    # Journalist personal dashboard showing their submitted articles
    path('my-articles/', views.journalist_dashboard, name='journalist_dashboard'),

    # ---------------------------------------------------------------------------
    # Internal API Endpoint
    # ---------------------------------------------------------------------------

    # Receives approved article data — simulates third-party integration
    path('api/approved/', views.api_approved, name='api_approved'),

    # ---------------------------------------------------------------------------
    # REST API — JWT authentication required for all endpoints below
    # ---------------------------------------------------------------------------

    # JWT token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Article endpoints
    # GET: list approved articles / POST: create article (journalist only)
    path('api/articles/', api_views.ArticleListView.as_view(), name='api_article_list'),

    # GET: articles from subscribed journalists/publishers (reader only)
    path('api/articles/subscribed/', api_views.SubscribedArticleListView.as_view(), name='api_subscribed_articles'),

    # GET: single article / PUT: update / DELETE: delete
    path('api/articles/<int:pk>/', api_views.ArticleDetailView.as_view(), name='api_article_detail'),

    # POST: approve an article (editor only)
    path('api/articles/<int:pk>/approve/', api_views.ArticleApproveView.as_view(), name='api_article_approve'),

    # Newsletter endpoints
    # GET: list all newsletters / POST: create newsletter (journalist/editor only)
    path('api/newsletters/', api_views.NewsletterListView.as_view(), name='api_newsletter_list'),

    # GET: single newsletter / PUT: update / DELETE: delete
    path('api/newsletters/<int:pk>/', api_views.NewsletterDetailView.as_view(), name='api_newsletter_detail'),

    # GET: current authenticated user's profile and role
    path('api/users/me/', api_views.CurrentUserView.as_view(), name='api_current_user'),

    # Publishers
    path('publishers/', views.publisher_list, name='publisher_list'),
    path('publishers/create/', views.create_publisher, name='create_publisher'),
    path('publishers/<int:pk>/', views.publisher_detail, name='publisher_detail'),
    path('publishers/<int:pk>/join/', views.join_publisher, name='join_publisher'),
    path('publishers/<int:pk>/leave/', views.leave_publisher, name='leave_publisher'),
    path('publishers/<int:pk>/add-journalist/', views.add_journalist_to_publisher, name='add_journalist_to_publisher'),
    path('publishers/<int:pk>/remove-journalist/<int:journalist_id>/', views.remove_journalist_from_publisher, name='remove_journalist_from_publisher'),
    path('publishers/<int:pk>/approve-journalist/<int:journalist_id>/', views.approve_journalist_join, name='approve_journalist_join'),
    path('publishers/<int:pk>/reject-journalist/<int:journalist_id>/', views.reject_journalist_join, name='reject_journalist_join'),


    # Reader subscriptions
    path('journalists/', views.journalist_list, name='journalist_list'),
    path('publishers/<int:pk>/subscribe/', views.subscribe_publisher, name='subscribe_publisher'),
    path('publishers/<int:pk>/unsubscribe/', views.unsubscribe_publisher, name='unsubscribe_publisher'),
    path('journalists/<int:pk>/subscribe/', views.subscribe_journalist, name='subscribe_journalist'),
    path('journalists/<int:pk>/unsubscribe/', views.unsubscribe_journalist, name='unsubscribe_journalist'),

]
