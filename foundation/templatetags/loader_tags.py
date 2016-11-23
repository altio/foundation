import logging

from django.template import loader_tags
from django.template.loader_tags import ExtendsError
from django.utils import six

logger = logging.getLogger('django.template')


class ExtendsNode(loader_tags.ExtendsNode):

    def find_template(self, template_name, context):
        """
        This is a wrapper around engine.find_template(). A history is kept in
        the render_context attribute between successive extends calls and
        passed as the skip argument. This enables extends to work recursively
        without extending the same template twice.
        Make tag aware of contextual use of app_label and model_name
        """

        app_label = context.get('app_label')
        model_name = context.get('model_name')

        # RemovedInDjango20Warning: If any non-recursive loaders are installed
        # do a direct template lookup. If the same template name appears twice,
        # raise an exception to avoid system recursion.
        for loader in context.template.engine.template_loaders:
            if not loader.supports_recursion:
                history = context.render_context.setdefault(
                    self.context_key, [context.template.origin.template_name],
                )
                if template_name in history:
                    raise ExtendsError(
                        "Cannot extend templates recursively when using "
                        "non-recursive template loaders",
                    )
                template = context.template.engine.get_template(
                    template_name, app_label=app_label, model_name=model_name
                )
                history.append(template_name)
                return template

        history = context.render_context.setdefault(
            self.context_key, [context.template.origin],
        )
        template, origin = context.template.engine.find_template(
            template_name, skip=history, app_label=app_label,
            model_name=model_name,
        )
        history.append(origin)
        return template


class IncludeNode(loader_tags.IncludeNode):

    def __init__(self, template, *args, **kwargs):
        self.template = template
        self.extra_context = kwargs.pop('extra_context', {})
        self.isolated_context = kwargs.pop('isolated_context', False)
        loader_tags.Node.__init__(self, *args, **kwargs)  # prevent recursion


    def render(self, context):
        """
        Render the specified template and context. Cache the template object
        in render_context to avoid reparsing and loading when used in a for
        loop.
        Make tag aware of contextual use of app_label and model_name
        """
        try:
            template = self.template.resolve(context)
            # Does this quack like a Template?
            if not callable(getattr(template, 'render', None)):
                # If not, we'll try our cache, and get_template()
                template_name = template
                cache = context.render_context.setdefault(self.context_key, {})
                template = cache.get(template_name)
                if template is None:
                    app_label = (
                        self.extra_context['app_label'].var
                        if 'app_label' in self.extra_context
                        else context.get('app_label')
                    )
                    model_name = (
                        self.extra_context['model_name'].var
                        if 'model_name' in self.extra_context
                        else context.get('model_name')
                    )
                    template = context.template.engine.get_template(
                        template_name,
                        app_label=app_label,
                        model_name=model_name
                    )
                    cache[template_name] = template
            values = {
                name: var.resolve(context)
                for name, var in six.iteritems(self.extra_context)
            }
            if self.isolated_context:
                return template.render(context.new(values))
            with context.push(**values):
                return template.render(context)
        except Exception:
            if context.template.engine.debug:
                raise
            template_name = getattr(context, 'template_name', None) or 'unknown'
            logger.warning(
                "Exception raised while rendering {%% include %%} for "
                "template '%s'. Empty string rendered instead.",
                template_name,
                exc_info=True,
            )
            return ''


loader_tags.ExtendsNode = ExtendsNode
loader_tags.IncludeNode = IncludeNode
