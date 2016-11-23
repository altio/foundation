# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase


system_check_errors = []


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class registry(dict):

    def __setitem__(self, key, value):
        if key in self:
            raise AlreadyRegistered(
                '{} is already registered'.format(key)
            )
        super(registry, self).__setitem__(key, value)

    def __getitem__(self, key):
        if key not in self:
            raise NotRegistered(
                '{} is not registered'.format(key)
            )
        return super(registry, self).__getitem__(key)


class Registry(object):

    def __init__(self, *args, **kwargs):
        self._registry = registry()
        super(Registry, self).__init__(*args, **kwargs)

    def register(self, controller_class, model=None, parent=None, **options):
        """
        Given a Controller class with a model attribute specified, registers
        an instance of the Controller mapped to its model for this Registry,
        where a Registry will be a Backend, Controller, or child Controller.
        """
        # ensure the base either had a model or one was passed
        if controller_class.opts.model:
            if model and model != controller_class.opts.model:
                raise ValueError(
                    'You cannot use a Controller with a "model" specified as '
                    'a generic Controller class.'
                )
            model = controller_class.opts.model
        else:
            if not model:
                raise ValueError(
                    'You must provide a "model" for this Controller.'
                )
            controller_class.opts.model = model

        if model._meta.abstract:
            raise ImproperlyConfigured(
                'The model {} is abstract, so it cannot be registered '
                'with a controller.'.format(model.__name__)
            )

        # Ignore the registration if the model has been
        # swapped out.
        if not model._meta.swapped:
            # If we got **options then dynamically construct a subclass of
            # admin_class with those **options.
            if options:
                # For reasons I don't quite understand, without a
                # __module__ the created class appears to "live" in the
                # wrong place, which causes issues later on.
                options['__module__'] = __name__
                controller_class = type(
                    "%sController" % model.__name__,
                    (controller_class,),
                    options
                )

            # Instantiate the controller and save in the appropriate registry
            parent = parent or self
            controller_obj = controller_class(parent=parent, registrar=self)
            if settings.DEBUG:
                system_check_errors.extend(controller_obj.check())

            self._registry[model] = controller_obj

            # handle all child registrations at this time
            for child_controller_class in controller_class.children:

                if child_controller_class.force_backend_as_registrar:
                    child_model = child_controller_class.opts.model
                    controller_obj.backend.register(child_model,
                                                    child_controller_class,
                                                    parent=controller_obj)
                else:
                    controller_obj.register(child_controller_class,
                                            parent=controller_obj)


    def unregister(self, model_or_iterable):
        """
        Unregisters the given model(s).

        If a model isn't already registered, this will raise NotRegistered.
        """
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            del self._registry[model]

    def has_registered_controller(self, model):
        """
        Check if a model class is registered in this backend/controller's
        registry.
        """
        return model in self._registry

    def get_registered_controller(self, model):
        """
        Get the Controller for a given model.

        If a model isn't already registered, this will raise NotRegistered.
        """
        return self._registry[model]
