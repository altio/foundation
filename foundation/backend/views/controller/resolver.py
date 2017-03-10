# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ...controller.resolver import Resolver

__all__ = 'ChainingMixin',


class ChainingMixin(Resolver):
    """
    Adds URL chaining to the BaseViewController, providing view, parent, and
    inline controllers (with registered counterparts) a URL to the appropriate
    mode.
    """

    def get_url_kwargs(self, mode, **kwargs):
        """
        This version of get_url_kwargs grooms them from the Controller (in this
        case, a BaseViewController subclass).
        """
        kwargs.update(**self.kwargs)
        kwargs = super(ChainingMixin, self).get_url_kwargs(mode, **kwargs)

        if mode in ('list', 'add'):
            kwargs.pop(self.model_lookup, None)

        return kwargs

    def get_label(self, mode):
        return ''.format(self.verbose_name_plural
                         if mode == 'list'
                         else (self.verbose_name
                               if mode == 'add'
                               else self.get_object()))

    def get_breadcrumb(self, mode):
        """
        Helper method to return the components of a breadcrumb.
        :param mode: (str) a valid view mode for this controller
        :param kwargs: (dict str:str) a dictionary of view kwargs to use
        :rtype: 2-tuple of strings: label, url
        """

        url = self.get_url(mode)
        label = self.get_label(mode) if url else None
        return label, url
