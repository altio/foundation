# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
from django.forms.models import _get_foreign_key
from django.shortcuts import resolve_url
from django.template.defaultfilters import title
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ..forms import IS_POPUP_VAR, TO_FIELD_VAR
from ..template.response import TemplateResponse
from ..utils import flatten_fieldsets


from ...controller import BaseController
from .accessor import PermissionsMixin
from .resolver import ChainingMixin

__all__ = 'BaseViewController', 'ParentController', 'ControllerMixin'


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


class ControllerMixin(BaseViewController, AppAccessMixin, BackendMixin):

    def __init__(self, controller, **kwargs):
        # model and fields exist on View itself and need to be overwritten
        super(ControllerMixin, self).__init__(view=self,
                                              controller=controller,
                                              model=controller.model,
                                              fields=controller.fields,
                                              **kwargs)

    @cached_property
    def parents(self):
        """
        A list of view-aware parent controllers linked to their registered
        counterparts.
        """

        kwargs = self.kwargs.copy()
        parents = []
        controller = self.controller

        while controller.parent:
            kwargs.pop(controller.model_lookup, None)
            controller = controller.parent
            parent = controller.get_parent_controller(view=self, kwargs=kwargs)
            parents.append(parent)
            kwargs = kwargs.copy()

        return tuple(parents)

    @cached_property
    def parent(self):
        return self.parents[0] if self.parents else None

    @cached_property
    def accessed_by_parent(self):
        parent_namespace = (self.parent.get_namespace(self.controller)
                            if self.parent
                            else None)
        return parent_namespace == self.request.resolver_match.namespace

    @cached_property
    def children(self):
        named_children = []
        # replaces get_inline_instances -- TODO: do we need obj?
        # TODO: cached?
        for registered_child_class in self.controller.children:
            registered_model = registered_child_class.opts.model
            registered_child = (
                self.controller.get_registered_controller(registered_model)
                if self.controller.has_registered_controller(registered_model)
                else self.backend.get_registered_controller(registered_model)
            )
            child = registered_child.get_child_controller(self)
            named_children.append((child.model_name, child))
        for inline_controller_class in self.controller.inlines:
            child = inline_controller_class(self)
            named_children.append((child.model_name, child))
            """
            if request:
                if not (inline.has_add_permission(request) or
                        inline.has_change_permission(request, obj) or
                        inline.has_delete_permission(request, obj)):
                    continue
                if not inline.has_add_permission(request):
                    inline.max_num = 0
            """
        return OrderedDict(named_children)

    def get_url_kwargs(self, mode, **kwargs):
        kwargs = super(ControllerMixin, self).get_url_kwargs(mode, **kwargs)
        if self.accessed_by_parent and mode not in ('list', 'add'):
            kwargs.pop(self.parent.model_lookup, None)

        return kwargs

    def get_url(self, mode, subcontroller=None, **kwargs):

        # custom override for VIEW ONLY to handle special case of list/add
        url = None

        if not subcontroller and self.accessed_by_parent and mode in ('list', 'add'):
            # attempt to get mode as a parent subcontroller url
            url = self.parent.get_url(mode, self.controller, **kwargs)

        # normal lookup
        if not url:
            url = super(ControllerMixin, self).get_url(mode, subcontroller, **kwargs)

        return url

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
            for parent in self.parents:
                if parent.model == model:
                    related_controller = parent
                elif parent.controller.has_registered_controller(model):
                    related_controller = \
                        parent.controller.get_registered_controller(model)
                if related_controller:
                    break
        if not related_controller:
            if self.backend.has_registered_controller(model):
                related_controller = self.backend.get_registered_controller(model)

        return related_controller
