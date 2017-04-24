from foundation import forms, rest
from foundation.backend import register

from . import models


class ViewMixin(object):

    """ Add overrides to view code here, or replace the view classes in the
    dictionary on the controller. """


class APIFormController(forms.FormController):

    viewsets = {
        None: forms.FormViewSet,
        'api': rest.APIViewSet,
        'embed': forms.FormViewSet,
    }

    view_mixin_class = ViewMixin


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
