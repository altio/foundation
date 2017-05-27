# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.http import urlencode

from ...controller import MultipleObjectMixin
from .base import ControllerViewMixin
from .mixins import PaginationMixin, SearchMixin

__all__ = 'ListMixin',


class ListMixin(PaginationMixin, SearchMixin, MultipleObjectMixin,
                ControllerViewMixin):

    mode = 'list'

    def handle_common(self, handler, request, *args, **kwargs):

        # store the query string and prune it as we go
        self.params = dict(request.GET.items())

        return super(ListMixin, self).handle_common(handler, request, *args, **kwargs)

    def get_query_string(self, new_params=None, remove=None):
        """ QueryString to pass back with response. """
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = self.params.copy()
        for r in remove:
            for k in list(p):
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(sorted(p.items()))
