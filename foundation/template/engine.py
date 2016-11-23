from django import template
from django.template.base import Template
from django.template.exceptions import TemplateDoesNotExist


class Engine(template.Engine):

    def find_template(self, name, dirs=None, skip=None, app_label=None,
                      model_name=None):
        """ Hard override accepts app_label and model_name """
        tried = []
        for loader in self.template_loaders:
            if loader.supports_recursion:
                try:
                    template = loader.get_template(
                        name, template_dirs=dirs, skip=skip,
                        app_label=app_label, model_name=model_name,
                    )
                    return template, template.origin
                except TemplateDoesNotExist as e:
                    tried.extend(e.tried)
            else:
                # RemovedInDjango20Warning: Use old api for non-recursive
                # loaders.
                try:
                    return loader(name, dirs)
                except TemplateDoesNotExist:
                    pass
        raise TemplateDoesNotExist(name, tried=tried)

    def get_template(self, template_name, app_label=None, model_name=None):
        """
        Returns a compiled Template object for the given template name,
        handling template inheritance recursively.
        Hard override accepts app_label and model_name
        """
        template, origin = self.find_template(template_name,
                                              app_label=app_label,
                                              model_name=model_name)
        if not hasattr(template, 'render'):
            # template needs to be compiled
            template = Template(template, origin, template_name, engine=self)
        return template
