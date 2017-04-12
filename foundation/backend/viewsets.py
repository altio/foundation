# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from django.conf.urls import url
from .views import ViewParent, ViewChild


class BackendViewSet(OrderedDict):

    view_class_mixin = None
    named_view_classes = ()

    def __init__(self, router, route):
        self.router = router
        self.route = route
        super(BackendViewSet, self).__init__(self.named_view_classes)
        mixins = self._get_view_class_mixins()
        for mode in self:
            #if mode in router:
            #    raise KeyError(
            #        'View mode "{}" already registered for {}'.format(
            #            mode, router))
            base_class = self[mode]
            view_name = self._get_view_class_name(base_class, mode, route)
            view_class = type(view_name, tuple(mixins + [base_class]),
                              {'__module__': __name__})
            self[mode] = self._get_view_as_callable(view_class, mode, route)

    def _get_view_class_name(self, view_class, mode, route):
        return view_class.__name__

    def _get_view_class_mixins(self):
        mixins = [self.view_class_mixin] if self.view_class_mixin else []
        if self.router.backend.view_class_mixin:
            mixins.append(self.router.backend.view_class_mixin)
        return mixins

    def _get_view_as_callable(self, view_class, mode, route, **kwargs):
        return view_class.as_view(
            backend=self.router.backend,
            name=mode,
            route=route,
            **kwargs)

    def get_urlpatterns(self):
        urlpatterns = []

        for mode in self:
            urlpatterns.append(
                url(r'^{mode}$'.format(mode=mode), self[mode], name=mode)
            )

        return urlpatterns


class AppViewSet(BackendViewSet):

    def __init__(self, app_config, *args, **kwargs):
        self.app_config = app_config
        super(AppViewSet, self).__init__(*args, **kwargs)

    def _get_view_class_name(self, *args, **kwargs):
        return str('{0}{1}'.format(
            self.app_config.name.title(),
            super(AppViewSet, self)._get_view_class_name(*args, **kwargs)
        ))

    def _get_view_class_mixins(self):
        mixins = super(AppViewSet, self)._get_view_class_mixins()
        mixin = getattr(self.app_config, 'view_class_mixin', None)
        if mixin:
            mixins.append(mixin)
        return mixins

    def _get_view_as_callable(self, *args, **kwargs):
        return super(AppViewSet, self)._get_view_as_callable(
            *args, app_config=self.app_config, **kwargs)


class ControllerViewSet(BackendViewSet):

    view_parent_class = ViewParent
    view_child_class = ViewChild

    def __init__(self, router, route):
        # need to ensure any view mixins are applied to partial view classes
        super(ControllerViewSet, self).__init__(router, route)
        mixins = self._get_view_class_mixins()
        for name in 'view_parent_class', 'view_child_class':
            klass = getattr(self, name)
            setattr(self, name, type(klass.__name__, tuple(mixins + [klass]), {}))

    def _get_view_class_name(self, *args, **kwargs):
        return str('{0}{1}'.format(
            self.router.controller.model.__name__,
            super(ControllerViewSet, self)._get_view_class_name(*args, **kwargs)
        ))

    def _get_view_class_mixins(self):
        mixins = super(ControllerViewSet, self)._get_view_class_mixins()
        controller = self.router.controller
        for mixin_source in controller.app_config, controller:
            mixin = getattr(mixin_source, 'view_mixin_class', None)
            if mixin:
                mixins.append(mixin)
        return mixins

    def _get_view_as_callable(self, *args, **kwargs):
        view = super(ControllerViewSet, self)._get_view_as_callable(
            *args, controller=self.router.controller, **kwargs)
        view.view_class.view_child_class = self.view_child_class
        view.view_class.view_parent_class = self.view_parent_class
        return view
