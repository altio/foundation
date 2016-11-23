from __future__ import absolute_import

from django.conf import settings
from django.template.backends import django
from django.template.backends.django import reraise, Template, TemplateDoesNotExist

from ..engine import Engine


class DjangoTemplates(django.DjangoTemplates):

    def __init__(self, params):
        """ Hard override of init to use our engine. """
        params = params.copy()
        options = params.pop('OPTIONS').copy()
        options.setdefault('autoescape', True)
        options.setdefault('debug', settings.DEBUG)
        options.setdefault('file_charset', settings.FILE_CHARSET)
        libraries = options.get('libraries', {})
        options['libraries'] = self.get_templatetag_libraries(libraries)
        super(django.DjangoTemplates, self).__init__(params)
        self.engine = Engine(self.dirs, self.app_dirs, **options)

    def get_template(self, template_name, app_label=None, model_name=None):
        """ Hard override accepts app_label and model_name """
        try:
            return Template(
                self.engine.get_template(
                    template_name, app_label=app_label, model_name=model_name
                ),
                self
            )
        except TemplateDoesNotExist as exc:
            reraise(exc, self)
