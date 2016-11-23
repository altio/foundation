from foundation import register, Controller

from . import models


class ViewMixin(object):

    """ Add overrides to view code here, or replace the view classes in the
    dictionary on the controller. """


class PostController(Controller):

    # ViewMixin = ViewMixin

    model = models.Post
    fields = ('blog', 'title', 'body')


@register(models.Blog)
class BlogController(Controller):

    model = models.Blog

    # auth
    fk_name = 'owner'

    fieldsets = {
        'public': (
            ('main', {'name': None, 'fields': ('title', 'owner')}),
        ),
    }

    children = [PostController]
    url_model_prefix = ''
