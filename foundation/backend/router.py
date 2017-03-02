# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .. import views
from ..views.controllers.components import Resolver


__all__ = 'Router',


class Router(Resolver):
    ViewMixin = None

    def __init__(self, **kwargs):
        super(Router, self).__init__(**kwargs)

        # registered_views of the form {model: ['mode', ...], ...}
        self.registered_views = {}

    @property
    def views(self):
        """
        Helper class provides a dict of mode names mapped to view classes.
        Override this to inject alternate view classes for each mode and to
        add new modes.
        """
        return {
            'list': views.ChangeListView,
            'view': views.DisplayView,
            'add': views.AddView,
            'edit': views.EditView,
            'delete': views.DeleteView,
        }

    def get_view(self, mode, controller=None):
        """
        Leveraged by Router to get the view class for a particular mode.
        The act of getting a mode means it is being registered, and thus that
        will happen here.
        """
        if not controller:
            controller = self
        if controller not in self.registered_views:
            self.registered_views[controller] = []
        self.registered_views[controller].append(mode)

        base_view_class = controller.views[mode]
        view_name = str('{0}{1}'.format(
            controller.model.__name__,
            base_view_class.__name__
        ))

        bases = [self.ViewMixin] if self.ViewMixin else []
        bases.append(base_view_class)
        view = type(view_name, tuple(bases), {})
        return view

    def get_urls(self):
        from django.conf.urls import url, include

        # the minimum "contract" of a controller are list and display views
        urlpatterns = [
            url(r'^$',
                self.get_view('list').as_view(
                    backend=self.backend,
                    controller=self
                ),
                name='list'),
        ]

        # if an auth path exists, provide add and single-object views
        if self.auth_query:
            urlpatterns.append(
                url(r'^add$',
                    self.get_view('add').as_view(
                        backend=self.backend,
                        controller=self
                    ),
                    name='add')
            )

            # attach all single-object manipulation modes
            for mode in set(self.views.keys()) - set([
                'list', 'view', 'add',
            ]):
                urlpatterns.append(
                    url(r'^(?P<{lookup}>[-\w]+)/{mode}$'.format(
                            lookup=self.model_lookup,
                            mode=mode,
                        ),
                        self.get_view(mode).as_view(
                            backend=self.backend,
                            controller=self,
                            mode=mode,
                        ),
                        name=mode,
                    )
                )

        # defer the display view until after "add" so it is not mistaken as slug
        urlpatterns += [
            url(r'^(?P<{lookup}>[-\w]+)$'.format(
                    lookup=self.model_lookup
                ),
                self.get_view('view').as_view(
                    backend=self.backend,
                    controller=self
                ),
                name='view'),
        ]

        # next, instantiate and add any related controller's sub-URLs
        # we will
        for child_controller_class in self.children:
            child_model = child_controller_class.opts.model

            # in the event the child self-promoted to the backend, we will add
            # only a list URL under this spec to we can provide naturally
            # filter list views and provide parent-aware add views
            if child_controller_class.force_backend_as_registrar:
                child_controller = self.backend.get_registered_controller(child_model)
                # NOTE: we are applying get_view to THIS controller not the
                # child to ensure the view registration happens on the correct
                # controller

                child_urlpatterns = [
                    url(r'^$',
                        self.get_view('list', child_controller).as_view(
                            backend=self.backend,
                            controller=child_controller
                        ),
                        name='list'),
                ]
                if self.auth_query:
                    child_urlpatterns.append(
                        url(r'^add$',
                            self.get_view('add', child_controller).as_view(
                                backend=self.backend,
                                controller=child_controller
                            ),
                            name='add'),
                    )
            else:
                child_controller = self.get_registered_controller(child_model)
                child_urlpatterns = child_controller.urls

            #  url(model_prefix, include(
            # (model_urlpatterns, model_namespace)))
            child_namespace = child_controller.model_namespace
            child_prefix = child_controller.url_prefix
            urlpatterns.append(
                url(r'^(?P<{lookup}>[-\w]+)/{prefix}'.format(
                        lookup=self.model_lookup,
                        prefix=child_prefix
                    ),
                    include((child_urlpatterns, child_namespace))
                ),
            )

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls()

    @property
    def modes(self):
        """ Return a list of registered modes for *this* controller. """
        return self.registered_views[self]

    def has_url(self, mode, controller=None):
        # we are going to ask this view if it has specific awareness of any
        # child controller's patterns from this perspective (e.g. inline
        # add/list for a child controller)
        if not controller:
            controller = self
        return mode in self.registered_views.get(controller, [])
