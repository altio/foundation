# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.paginator import PageNotAnInteger, InvalidPage

from .variables import ALL_VAR, PAGE_VAR
from django.contrib.admin.options import IncorrectLookupParameters

__all__ = 'PaginationMixin',


class PaginationMixin(object):
    """ Pagination: execute on QS prior to Filtering... """

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator_class(queryset, per_page, orphans, allow_empty_first_page)

    def get_page_queryset(self, queryset, page):

        return queryset.filter(pk__in=[obj.pk for obj in page])

    def get_queryset(self):

        # auth-constrained queryset
        self.root_queryset = super(PaginationMixin, self).get_queryset()

        # get the paginator but do not apply it yet
        self.paginator = self.get_paginator(
            self.root_queryset,
            self.list_per_page,
            orphans=0,
            allow_empty_first_page=False,
        )

        # Get the number of objects, with controller filters applied.
        self.result_count = self.paginator.count

        # Get the total number of objects, with no admin filters applied.
        self.full_result_count = (
            self.root_queryset.count()
            if self.show_full_result_count
            else None
        )
        self.can_show_all = self.result_count <= self.list_max_show_all
        self.multi_page = self.result_count > self.list_per_page

        # Get the list of objects to display on this page.
        if (self.show_all and self.can_show_all) or not self.multi_page:
            self.page = None
            queryset = self.root_queryset._clone()
        else:
            try:
                self.page = self.paginator.page(self.page_num)
            except PageNotAnInteger:
                self.page = self.paginator.page(1)
            except InvalidPage:
                raise IncorrectLookupParameters

            # queryset = self.paginator.page(self.page_num).object_list
            # TODO: not sure this is needed anymore... leftover?
            queryset = self.get_page_queryset(self.root_queryset, self.page)


        return queryset

    def handle_common(self, handler, request, *args, **kwargs):

        """
        DELETE/RE-LOCATE
        # auth-constrained queryset
        self.root_queryset = self.get_queryset()

        # get paginated page
        self.page = self.get_page(self.root_queryset, self.list_per_page)

        # get paginated queryset
        self.queryset = self.get_page_queryset(self.root_queryset, self.page)
        """

        try:
            self.page_num = int(request.GET.get(PAGE_VAR, 1))
        except ValueError:
            self.page_num = 1
        self.show_all = ALL_VAR in request.GET

        if PAGE_VAR in self.params:
            del self.params[PAGE_VAR]

        return super(PaginationMixin, self).handle_common(handler, request, *args, **kwargs)
