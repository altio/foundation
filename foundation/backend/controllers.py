# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include

from .controller import BaseController
from .router import Router

__all__ = 'Controller',


class Controller(Router, BaseController):
    """
    Controllers need the ability to:
    a) generate the URLs needed for the Backend
    b) generate the JIT (View, Inline, and Parent) Controller for each View
    """

    fields = None
    exclude = None
    fieldsets = None
    fk_name = None
    model = None
    ordering = None

    checks_class = None
    children = ()
    inlines = ()
    parent = None
    registrar = None
    force_backend_as_registrar = False

    def __init__(self, parent, registrar=None):
        """
        Initializes a Model Controller for eventual registration as a Backend
        controller or a Controller sub-controller.
        :param parent: the Backend or Controller instance from which
            this Controller was created
        :param registrar: the Backend or Controller instance under which
            this Controller is to be registered
        """

        # only registered Controller will be aware of their registered parent
        from .base import Backend
        if isinstance(parent, Backend):
            if registrar and registrar != parent:
                raise ValueError('"registrar" cannot be set to non-backend when'
                                 ' "backend" is also set.')
            self.registrar = backend = parent
        else:
            if not registrar:
                registrar = parent
            backend = parent.backend
            self.parent = parent
            self.registrar = registrar

        # this Controller will be its own registered controller
        super(Controller, self).__init__(backend=backend, controller=self)

    @property
    def is_root(self):
        return self.parent is None

    @property
    def is_local_root(self):
        return self.registrar is self.backend

    def check(self, **kwargs):
        return (self.checks_class().check(self, **kwargs)
                if self.checks_class else [])

    def get_associated_queryset(self):
        queryset = self.model._default_manager.get_queryset()
        queryset.attach(controller=self)

    def get_view_parent(self, view, kwargs):
        view_parent = view.view_parent_class(
            view=view, controller=self, kwargs=kwargs)
        view_parent.__class__.__name__ =  str('{}ViewParent'.format(
            view_parent.controller.model.__name__
        ))
        return view_parent

    def get_view_child(self, view):
        view_child = view.view_child_class(view=view, controller=self)
        return view_child

    def get_urlpatterns(self):

        # gets the set of named urlpatterns from this controller's viewsets
        urlpatterns = super(Controller, self).get_urlpatterns(self)

        # gets the urlpatterns from each child and makes additional entries
        # in the patterns as needed
        for child_controller_class in self.children:
            child_model = child_controller_class.model
            child_controller = self.get_registered_controller(child_model)
            child_namespace = child_controller.model_namespace
            child_prefix = child_controller.url_prefix

            # get named patterns from child and extend
            child_urlpatterns = child_controller.get_urlpatterns()
            for name, patterns in child_urlpatterns.items():
                urlpatterns[name].append(
                    url(r'^(?P<{lookup}>[-\w]+)/{prefix}/'.format(
                            lookup=self.model_lookup,
                            prefix=child_prefix
                        ),
                        include((patterns, child_namespace))
                    ),
                )

        return urlpatterns
