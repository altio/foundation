# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import list

from .base import FormControllerViewMixin
from .components import FormSetMixin
from ...backend.views import ListMixin

__all__ = 'ListView',


class ListView(FormSetMixin, FormControllerViewMixin, ListMixin, list.ListView):
    """ Multiple-Object ModelFormSet View Mixin """

    template_name = 'list.html'
    mode_title = 'all'

    def get_context_data(self, **kwargs):
        kwargs.update(
            formset=self.formset,
        )
        return super(ListView, self).get_context_data(**kwargs)
