# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ...controller import MultipleObjectMixin
from .base import ControllerViewMixin

__all__ = 'ListMixin',


class ListMixin(MultipleObjectMixin, ControllerViewMixin):

    mode = 'list'
