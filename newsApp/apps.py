"""
newsApp/apps.py

Application configuration for the Speedy Spectator news application.

This module defines the AppConfig class which Django uses to configure
the newsApp application. The ready() method is used to import signal
handlers when the application starts, ensuring they are registered
and active for the lifetime of the application.
"""

from django.apps import AppConfig


class NewsAppConfig(AppConfig):
    """
    Application configuration class for the newsApp Django application.

    Inherits from Django's AppConfig to provide application-level
    configuration settings. The ready() method is overridden to import
    signal handlers after the application registry is fully populated,
    which is the recommended way to connect signals in Django.

    Attributes:
        default_auto_field (str): Sets the default primary key field type
                                  to BigAutoField (64-bit integer) for all
                                  models in this application.
        name (str): The full Python path to the application module.
    """

    # Use 64-bit integer primary keys for all models in this application
    default_auto_field = 'django.db.models.BigAutoField'

    # The dotted Python path to the application module
    name = 'newsApp'

    def ready(self):
        """
        Perform application startup tasks after the app registry is ready.

        Called by Django once the application registry is fully populated.
        Imports the signals module to register all signal handlers defined
        in newsApp/signals.py.

        This import must happen here rather than at the module level to
        avoid AppRegistryNotReady errors that occur when signals are
        imported before Django's app registry has finished loading.
        """
        # Import signals here to register all post_save and post_migrate
        # handlers defined in signals.py. This ensures signals are active
        # for the full lifetime of the application.
        import newsApp.signals  # noqa: F401
