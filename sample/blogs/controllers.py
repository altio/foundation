from foundation import forms, rest
from foundation.backend import register

from . import models


class FormViewMixin(object):

    """ Add overrides to view code here, or replace the view classes in the
    dictionary on the controller. """

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(FormViewMixin, self).formfield_for_dbfield(db_field,
                                                                     **kwargs)
        # if formfield:  # concrete inheritance
        widget = formfield.widget

        # do not apply to templated widgets
        # if not isinstance(widget, forms.widgets.WidgetTemplateMixin):
        widget.attrs['class'] = ' '.join((
            widget.attrs.get('class', ''), 'form-control'
        ))

        return formfield


class APIFormController(forms.FormController):

    viewsets = {
        None: forms.PageViewSet,
        'api': rest.APIViewSet,
        'embed': forms.EmbedViewSet,
    }

    view_mixin_class = FormViewMixin


class PostController(APIFormController):

    # view_class_mixin = ViewMixin

    model = models.Post
    public_modes = ('list', 'display')
    fields = ('blog', 'title', 'body')


@register(models.Blog)
class BlogController(APIFormController):

    # auth
    fk_name = 'owner'
    public_modes = ('list', 'display')

    fieldsets = {
        'public': (
            ('form', {
                'name': None,
                'fields': ('owner', 'title'),
                'description': 'The purpose of this fieldset.',
                # classes
                # readonly_fields
                # template_name?
            }),
            ('tabs', {
                'fields': ('description', 'blog_entries'),
                'template_name': 'tabs.html'
            }),
        ),
    }
    readonly_fields = ('description',)

    children = [PostController]
    url_model_prefix = ''
