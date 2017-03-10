# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.utils import six

from .accessor import ModelAccessor
from .resolver import ModelResolver

__all__ = 'BaseController',


@six.add_metaclass(forms.MediaDefiningClass)
class BaseController(ModelAccessor, ModelResolver):
    """
    Functionality common to all Controllers:

    - Access to the Models as pass-though queries via ModelAccessor.
    - Resolution of URLs based on naming conventions via ModelResolver.

    At the core of our Controller is the ability to resolve a URL pattern to a
    namespaced name given a set of kwargs.  This single component is safe for
    universal inclusion.
    """

    backend = None
    controller = None

    def __init__(self, backend, controller=None, **kwargs):
        """
        One thing all Controller share is the concept of a "registered"
        Controller.  For all but ViewController-instantiated InlineControllers,
        all Controller are guaranteed to have a registered counterpart.  For
        "registered" Controller, the counterpart is self.  For all others, is
        is resolvable in the underlying Registry and stored for convenience.
        For JIT InlineControllers, it may be None, which is a special case
        where that Controller's Options are not overwritten.
        :param registered_controller: an optional Controller instance
        """
        self.backend = backend
        if controller:
            self.controller = controller
            self.model = controller.model
        super(BaseController, self).__init__(**kwargs)

    def __getattribute__(self, name):
        """
        When a normal lookup fails, perform a secondary lookup in the model.
        """
        super_getattr = super(BaseController, self).__getattribute__

        try:
            return super_getattr(name)
        except AttributeError as e:
            model = super_getattr('model')
            if not model:
                raise ImproperlyConfigured('Controller should have model by now.')

            try:
                return getattr(model._meta, name)
            except AttributeError:
                raise e
