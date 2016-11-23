import os

from django.apps import apps
from django.core.exceptions import SuspiciousFileOperation
from django.template.loaders import app_directories
from django.template.base import Template, Origin
from django.template.exceptions import TemplateDoesNotExist
from django.utils import lru_cache
from django.utils._os import upath, safe_join


@lru_cache.lru_cache()
def get_app_template_dirs(dirname, app_label=None, model_name=None):
    """
    Return an iterable of paths of directories to load app templates from.

    dirname is the name of the subdirectory containing templates inside
    installed applications.

    Derived from django.template.utils.get_app_template_dirs
    Hard override accepts app_label and model_name
    """
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
                            template_dirs.append(upath(model_dir))
                    template_dirs.append(upath(app_dir))
            foundation_dir = os.path.join(template_dir, 'foundation')
            if os.path.isdir(foundation_dir):
                template_dirs.append(upath(foundation_dir))
            template_dirs.append(upath(template_dir))
    # Immutable return value because it will be cached and shared by callers.
    return tuple(template_dirs)


class Loader(app_directories.Loader):

    def get_dirs(self, app_label=None, model_name=None):
        """ Hard override accepts app_label and model_name """
        return get_app_template_dirs('templates', app_label=app_label, model_name=model_name)

    def get_template_sources(self, template_name, template_dirs=None, app_label=None, model_name=None):
        """
        Return an Origin object pointing to an absolute path in each directory
        in template_dirs. For security reasons, if a path doesn't lie inside
        one of the template_dirs it is excluded from the result set.

        Source: django.template.loaders.filesystem.Loader
        Hard override accepts app_label and model_name
        """
        if not template_dirs:
            template_dirs = self.get_dirs(app_label=app_label, model_name=model_name)
        for template_dir in template_dirs:
            try:
                name = safe_join(template_dir, template_name)
            except SuspiciousFileOperation:
                # The joined path was located outside of this template_dir
                # (it might be inside another one, so this isn't fatal).
                continue

            yield Origin(
                name=name,
                template_name=template_name,
                loader=self,
            )

    def get_template(self, template_name, template_dirs=None, skip=None, app_label=None, model_name=None):
        """
        Calls self.get_template_sources() and returns a Template object for
        the first template matching template_name. If skip is provided,
        template origins in skip are ignored. This is used to avoid recursion
        during template extending.

        Source: django.template.loaders.base.Loader
        Hard override accepts app_label and model_name
        """
        tried = []

        args = [template_name, template_dirs, app_label, model_name]

        for origin in self.get_template_sources(*args):
            if skip is not None and origin in skip:
                tried.append((origin, 'Skipped'))
                continue

            try:
                contents = self.get_contents(origin)
            except TemplateDoesNotExist:
                tried.append((origin, 'Source does not exist'))
                continue
            else:
                return Template(
                    contents, origin, origin.template_name, self.engine,
                )

        raise TemplateDoesNotExist(template_name, tried=tried)
