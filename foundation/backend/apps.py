from django import apps
from .views.base import AppTemplateView

__all__ = 'AppConfig',


class AppConfig(apps.AppConfig):

    # set to None to not create an app index
    app_index_class = AppTemplateView

    # set False to disable auto-import of urls module
    import_urls = True

    # default = label, set '' for no prefix, str for alt prefix
    url_prefix = None
