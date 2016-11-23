# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import list

from .base import ControllerMixin
from .controllers.components import query


__all__ = 'ListView',


class MultipleObjectMixin(query.MultipleObjectMixin, ControllerMixin):
    pass


class ListView(MultipleObjectMixin, list.ListView):

    mode = 'list'
    template_name = 'list.html'
