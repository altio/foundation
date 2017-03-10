from foundation import forms, rest
from foundation.decorators import register

from . import models


class ViewMixin(object):

    """ Add overrides to view code here, or replace the view classes in the
    dictionary on the controller. """


class APIFormController(forms.Controller):

    viewsets = {
        None: forms.FormViewSet,
        'api': rest.APIViewSet,
    }


class PostController(APIFormController):

    # view_class_mixin = ViewMixin

    model = models.Post
    fields = ('blog', 'title', 'body')


@register(models.Blog)
class BlogController(APIFormController):

    # auth
    fk_name = 'owner'

    fieldsets = {
        'public': (
            ('main', {'name': None, 'fields': ('title', 'owner')}),
        ),
    }

    children = [PostController]
    url_model_prefix = ''
