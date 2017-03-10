# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http.response import Http404
from django.utils.translation import ugettext as _

from ...controller import SingleObjectMixin
from .base import ControllerViewMixin

__all__ = 'ObjectMixin',


class ObjectMixin(SingleObjectMixin, ControllerViewMixin):

    mode = 'object'

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        By default this requires `self.queryset` and a `pk` or `slug` argument
        in the URLconf, but subclasses can override this to return any object.
        """

        obj = super(ObjectMixin, self).get_object(queryset=queryset)

        if not obj:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': self.model._meta.verbose_name})
        return obj
