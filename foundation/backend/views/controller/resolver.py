# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ...controller.resolver import ModelResolver


class ChainingMixin(ModelResolver):
    """
    Provides ViewControllers with an ability to introspect and determine the URL
    for a particular mode given the current view and an optional, in-focus
    object.  This may be a View, ViewParent, or ViewChild (including inlines).
    """

    def get_url_kwargs(self, mode, **kwargs):
        """
        This version of get_url_kwargs grooms them from the Controller (in this
        case, a BaseModelView subclass).
        """
        kwargs.update(**self.kwargs)
        kwargs = super(ChainingMixin, self).get_url_kwargs(mode, **kwargs)

        if mode in ('list', 'add'):
            kwargs.pop(self.model_lookup, None)

        return kwargs

    def get_url(self, mode, obj=None, route=None, **kwargs):

        # if obj passed to this call, add to kwargs, then ditch it
        if obj and self.controller.model_lookup not in kwargs:
            try:
                lookup_value = getattr(obj, 'slug')
            except AttributeError:
                lookup_value = getattr(obj, 'pk')
            kwargs.update({self.controller.model_lookup: lookup_value})

        return super(ChainingMixin, self).get_url(mode, route=route, **kwargs)
