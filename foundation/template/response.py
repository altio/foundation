from django.template import response
from django.utils import six

from .loader import get_template, select_template


class TemplateResponse(response.TemplateResponse):

    def resolve_template(self, template):
        """
        Accepts a template object, path-to-template or list of paths
        Hard override accepts app_label and model_name
        """

        # always start with view controller
        view_controller = self.context_data.get('view_controller')
        app_label = getattr(view_controller, 'app_label', None)
        model_name = getattr(view_controller, 'model_name', None)

        # then try app_config
        if not app_label:
            app_config = self.context_data.get('app_config')
            if app_config:
                app_label = app_config.label

        if isinstance(template, (list, tuple)):
            return select_template(template, using=self.using,
                                   model_name=model_name, app_label=app_label)
        elif isinstance(template, six.string_types):
            return get_template(template, using=self.using,
                                model_name=model_name, app_label=app_label)
        else:
            return template

