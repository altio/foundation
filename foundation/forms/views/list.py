# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .edit import MultipleObjectFormsetMixin
from .list import ListView

__all__ = 'ChangeListView',


class ChangeListView(MultipleObjectFormsetMixin, ListView):

    mode = 'list'
    mode_title = 'all'
    template_name = 'change_list.html'

    # get from controller
    # self.list_display = list_display
    # self.list_display_links = list_display_links
    # self.list_filter = list_filter
    # self.date_hierarchy = date_hierarchy
    # self.search_fields = search_fields
    # self.list_select_related = list_select_related
    # self.list_per_page = list_per_page
    # self.list_max_show_all = list_max_show_all
    # self.preserved_filters = controller.get_preserved_filters(view)

    # Get search parameters from the query string.

    def handle_common(self, handler, request, *args, **kwargs):
        handler = super(ChangeListView, self).handle_common(handler, request, *args, **kwargs)

        # auth-constrained queryset
        self.queryset = self.get_queryset()

        # parent_obj will be needed for non-local roots since they will use FK
        # to build out an inline formset and provide add/edit inline
        parent_obj = (self.parent.get_object()
                      if not self.controller.is_local_root
                      else None)

        # feed the par-reduced queryset to formset, which will in turn FK
        # constrain it, as applicable
        self.formset = self.get_formset(
            obj=parent_obj,
            queryset=self.queryset
        )

        return handler

    def get_context_data(self, **kwargs):
        kwargs.update(
            formset=self.formset,
        )
        return super(ChangeListView, self).get_context_data(**kwargs)
