# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
from django.utils.functional import cached_property

from ...controller.base import BaseController
from ...controller import MultipleObjectMixin, SingleObjectMixin
from .accessor import ModelPermissionsMixin
from .resolver import ChainingMixin

__all__ = 'ViewParent', 'ViewChild', 'ControllerViewMixin'


class BaseViewController(ChainingMixin, ModelPermissionsMixin, BaseController):
    """
    A Controller- and View-aware partial View class which is used as a base 
    to implement
    Controller-aware Views for Model and ModelForm views *as well as* any
    related partial ViewParent(s) or ViewChild(ren).

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

    def get_associated_queryset(self):
        queryset = self.model._default_manager.get_queryset()
        return queryset.associate(view_controller=self)

    def __getattribute__(self, name):
        """
        When a normal lookup fails, perform a secondary lookup in the model.
        """
        super_getattr = super(BaseController, self).__getattribute__

        try:
            return super_getattr(name)
        except AttributeError as e:
            controller = super_getattr('controller')
            try:
                return getattr(controller, name)
            except AttributeError:
                raise e


class ViewChild(MultipleObjectMixin, BaseViewController):

    def get_permissions_model(self):
        permissions_model = super(ViewChild, self).get_permissions_model()

        if permissions_model._meta.auto_created:
            # The model was auto-created as intermediary for a
            # ManyToMany-relationship, find the target model
            for field in permissions_model._meta.fields:
                if field.remote_field and field.remote_field.model != self.view.model:
                    permissions_model = field.remote_field.model
                    break

        return permissions_model

    def get_queryset(self):
        # early exit if this is an inline in edit mode and we are not permitted
        if self.view.add or self.view.edit and not self.has_permission('edit'):
            return self.model._default_manager.get_queryset().none()

        return super(ViewChild, self).get_queryset()

    def get_url(self, mode, **kwargs):
        url = self.view.get_url(mode, self.controller, **kwargs)
        if not url:
            url = super(ViewChild, self).get_url(mode, **kwargs)
        return url


class ViewParent(MultipleObjectMixin, SingleObjectMixin, BaseViewController):
    """
    A View-Aware controller representing one of the parents in the chain of
    objects providing access to the current view.
    """

    def __init__(self, view, controller, kwargs):
        """
        Parent Controllers will always have:
        view - View instance from which this ViewParent was instantiated
        controller - the registered parent controller this relates to
        kwargs - the reduced view kwargs which act as the object lookup
        """
        super(ViewParent, self).__init__(view=view, controller=controller)
        self.kwargs = kwargs


class ControllerViewMixin(BaseViewController):

    def __init__(self, controller, **kwargs):
        kwargs.setdefault('view', self)
        super(ControllerViewMixin, self).__init__(controller=controller,
                                                  **kwargs)

    @cached_property
    def view_parents(self):
        """
        A list of view-aware parent controllers linked to their registered
        counterparts.
        """

        kwargs = self.kwargs.copy()
        parents = []
        view = self

        while view.controller.parent:
            kwargs.pop(view.controller.model_lookup, None)
            controller = view.controller.parent
            view = controller.get_view_parent(view=view, kwargs=kwargs)
            parents.append(view)
            kwargs = kwargs.copy()

        return tuple(parents)

    @cached_property
    def view_parent(self):
        return self.view_parents[0] if self.view_parents else None

    @cached_property
    def view_children(self):
        """
        A list of ViewChild (or subclassed) instances representing each of the
        children for this view's controller followed by each inline.
        """
        named_children = []
        for registered_child_class in self.controller.children:
            registered_model = registered_child_class.model
            registered_child = (
                self.controller.get_registered_controller(registered_model)
                if self.controller.has_registered_controller(registered_model)
                else self.backend.get_registered_controller(registered_model)
            )
            child = registered_child.get_view_child(self)
            named_children.append((child.model_name, child))
        for inline_controller_class in self.controller.inlines:
            child = inline_controller_class(self)
            named_children.append((child.model_name, child))
        return OrderedDict(named_children)

    def get_related_controller(self, model):
        """
        Return this or a parent view_controller if any of them is for the
        specified model otherwise return a backend-registered controller, if
        available.
        """
        related_controller = (
            self
            if self.model == model
            else None
        )
        if not related_controller:
            for view_parent in self.view_parents:
                if view_parent.model == model:
                    related_controller = view_parent
                elif view_parent.controller.has_registered_controller(model):
                    related_controller = \
                        view_parent.controller.get_registered_controller(model)
                if related_controller:
                    break
        if not related_controller:
            if self.backend.has_registered_controller(model):
                related_controller = self.backend.get_registered_controller(model)

        return related_controller
