# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import operator
import six
from django.db import models

if six.PY3:
    from functools import reduce

from .....utils import lookup_needs_distinct
from .variables import SEARCH_VAR

__all__ = 'SearchMixin',


class SearchMixin(object):

    def get_search_fields(self):
        """
        Returns a sequence containing the fields to be searched whenever
        somebody submits a search query.
        """
        return self.search_fields

    def get_search_results(self, queryset, search_term):
        """
        Returns a tuple containing a queryset to implement the search,
        and a boolean indicating if the results may contain duplicates.
        """
        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        use_distinct = False
        search_fields = self.get_search_fields()
        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in search_fields]
            for bit in search_term.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(self.model._meta, search_spec):
                        use_distinct = True
                        break

        return queryset, use_distinct

    def get_queryset(self):

        qs = super(SearchMixin, self).get_queryset()

        # Apply search results
        qs, search_use_distinct = self.get_search_results(qs, self.query)

        # Remove duplicates from results, if necessary
        return qs.distinct() if search_use_distinct else qs

    def handle_common(self, handler, request, *args, **kwargs):

        self.query = request.GET.get(SEARCH_VAR, '')

        return super(SearchMixin, self).handle_common(handler, request, *args, **kwargs)
