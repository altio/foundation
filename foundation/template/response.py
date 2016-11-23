from django.template import response
from django.utils import six

from .loader import get_template, select_template


class TemplateResponse(response.TemplateResponse):

    def resolve_template(self, template):
        """
        Accepts a template object, path-to-template or list of paths
        Hard override accepts app_label and model_name
        """
        app_label = self.context_data.get('app_label')
        model_name = self.context_data.get('model_name')
        if isinstance(template, (list, tuple)):
            return select_template(template, using=self.using,
                                   model_name=model_name, app_label=app_label)
        elif isinstance(template, six.string_types):
            return get_template(template, using=self.using,
                                model_name=model_name, app_label=app_label)
        else:
            return template

