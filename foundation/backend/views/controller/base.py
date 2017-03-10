# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ...controller import BaseController
from .accessor import PermissionsMixin
from .resolver import ChainingMixin

__all__ = 'BaseViewController',


class BaseViewController(ChainingMixin, PermissionsMixin, BaseController):
    """
    A View-Aware Controller with view-pertinent helper methods and an opts
    property that will route back to the parent opts, as appropriate.

    All view-aware Controllers will be able to:
    - resolve chained URLs (ChainingMixin)
    - provide permissions determination for objects above, at, and below their
      level

    This base class will be used in one of four ways:
    - As a base class for a View itself (will get Single/MultipleObject pieces
      from that usage)
    - As a base class for a Parent View-Aware Controller, which will be used
      for permission determination, access-control, and parent object URLs.
    - As a base class for Inline, View-Aware Controllers from child registered
      Controllers.
    - As a base class for Inline, View-Aware Controller for unregistered
      inlines (providing inline editing only).

    ** Need to pass kwargs through since this will get combined with View class.
    """

    def __init__(self, view, controller=None, **kwargs):
        self._view = view
        kwargs.setdefault('backend', view.backend)
        super(BaseViewController, self).__init__(controller=controller,
                                                 **kwargs)

    @property
    def view(self):
        return self._view
