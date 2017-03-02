# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http.response import Http404
from django.utils.translation import ugettext as _
from django.views.generic import detail

from .base import ControllerMixin
from .controllers.components import query

__all__ = 'DetailView',


class SingleObjectMixin(query.SingleObjectMixin, ControllerMixin):

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        By default this requires `self.queryset` and a `pk` or `slug` argument
        in the URLconf, but subclasses can override this to return any object.
        """

        obj = super(SingleObjectMixin, self).get_object(queryset=queryset)

        # TODO: Consider if we want to support normal pk/slug stuff...

        if not obj:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': self.model._meta.verbose_name})
        return obj


class DetailView(SingleObjectMixin, detail.DetailView):

    mode = 'view'
    template_name = 'detail.html'
