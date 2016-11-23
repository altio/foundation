# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import BaseViewController
from .components import MultipleObjectMixin, SingleObjectMixin

__all__ = 'ParentController',


class ParentController(MultipleObjectMixin, SingleObjectMixin, BaseViewController):
    """
    A View-Aware controller representing one of the parents in the chain of
    objects providing access to the current view.
    """

    def __init__(self, view, controller, kwargs):
        """
        Parent Controllers will always have:
        view - View instance from which this ParentController was instantiated
        controller - the registered parent controller this relates to
        kwargs - the reduced view kwargs which act as the object lookup
        """
        super(ParentController, self).__init__(view=view, controller=controller)
        self.kwargs = kwargs
