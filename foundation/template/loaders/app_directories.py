import os

from django.apps import apps
from django.template.loaders import app_directories
from django.utils import lru_cache
from django.utils._os import upath

from .base import FoundationMixin


@lru_cache.lru_cache()
def get_app_template_dirs(dirname, app_label=None, model_name=None):
    """
    Return an iterable of paths of directories to load app templates from.

    dirname is the name of the subdirectory containing templates inside
    installed applications.

    Derived from django.template.utils.get_app_template_dirs
    Hard override accepts app_label and model_name
    """
    priority_dirs = []
    template_dirs = []
    for app_config in apps.get_app_configs():
        if not app_config.path:
            continue
        template_dir = os.path.join(app_config.path, dirname)
        if os.path.isdir(template_dir):
            if app_config.label == app_label:
                app_dir = os.path.join(template_dir, app_label)
                if os.path.isdir(app_dir):
                    if model_name:
                        model_dir = os.path.join(app_dir, model_name)
                        if os.path.isdir(model_dir):
                            priority_dirs.append(upath(model_dir))
                    priority_dirs.append(upath(app_dir))
            template_dirs.append(upath(template_dir))
    # Immutable return value because it will be cached and shared by callers.
    return tuple(priority_dirs + template_dirs)


class Loader(FoundationMixin, app_directories.Loader):

    def get_dirs(self, app_label=None, model_name=None):
        """ Hard override accepts app_label and model_name """
        return get_app_template_dirs('templates', app_label=app_label, model_name=model_name)
