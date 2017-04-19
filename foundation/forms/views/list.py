# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import list

from .base import ControllerTemplateMixin
from .components import FormSetMixin
from ...backend.views import ListMixin

__all__ = 'ListView',


class ListView(FormSetMixin, ControllerTemplateMixin, ListMixin, list.ListView):
    """ Multiple-Object ModelFormSet View Mixin """

    mode_title = 'all'

    def handle_common(self, handler, request, *args, **kwargs):
        handler = super(FormSetMixin, self).handle_common(
            handler, request, *args, **kwargs
        )

        parent_obj = (self.view_parent.get_object()
                      if self.view_parent
                      else None)

        # feed the par-reduced queryset to formset, which will in turn FK
        # constrain it, as applicable
        self.formset = self.get_formset(
            obj=parent_obj,
            queryset=self.queryset
        )

        return handler

    def get_context_data(self, **kwargs):
        kwargs.update({
            'formset': self.formset,
        })
        return super(ListView, self).get_context_data(**kwargs)
