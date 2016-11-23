from django.template.loader import _engine_list, TemplateDoesNotExist
from django.utils import six


def get_template(template_name, using=None, app_label=None, model_name=None):
    """
    Loads and returns a template for the given name.

    Raises TemplateDoesNotExist if no such template exists.
    Hard override accepts app_label and model_name
    """
    chain = []
    engines = _engine_list(using)
    for engine in engines:
        try:
            return engine.get_template(template_name, app_label=app_label,
                                       model_name=model_name)
        except TemplateDoesNotExist as e:
            chain.append(e)

    raise TemplateDoesNotExist(template_name, chain=chain)


def select_template(template_name_list, using=None, app_label=None,
                    model_name=None):
    """
    Loads and returns a template for one of the given names.

    Tries names in order and returns the first template found.

    Raises TemplateDoesNotExist if no such template exists.
    Hard override accepts app_label and model_name
    """
    if isinstance(template_name_list, six.string_types):
        raise TypeError(
            'select_template() takes an iterable of template names but got a '
            'string: %r. Use get_template() if you want to load a single '
            'template by name.' % template_name_list
        )

    chain = []
    engines = _engine_list(using)
    for template_name in template_name_list:
        for engine in engines:
            try:
                return engine.get_template(template_name, app_label=app_label,
                                           model_name=model_name)
            except TemplateDoesNotExist as e:
                chain.append(e)

    if template_name_list:
        raise TemplateDoesNotExist(', '.join(template_name_list), chain=chain)
    else:
        raise TemplateDoesNotExist("No template names provided")
