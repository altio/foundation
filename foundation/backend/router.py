# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .registry import Registry


class NamedRouter(dict):

    def __init__(self, backend, *args, **kwargs):
        self.backend = backend
        super(NamedRouter, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if key not in self.backend._routes:
            raise KeyError('"{}" is not a route in this Backend'.format(key))
        return dict.__setitem__(self, key, value)


class NamedRouteList(NamedRouter):

    def __getitem__(self, key):
        if key not in self:
            self[key] = []
        return super(NamedRouteList, self).__getitem__(key)


class NamedRouteDict(NamedRouter):

    def __getitem__(self, key):
        if key not in self:
            self[key] = {}
        return super(NamedRouteDict, self).__getitem__(key)


class Router(Registry):

    backend = None
    viewsets = {}
    view_class_mixin = None

    @staticmethod
    def get_urlpatterns(source, **kwargs):
        """
        Return a dictionary with keys of the backend root namespaces and
        urlpatterns lists for each target.  These will cascade upwards until
        they are received by the Backend's implementation of the Router which
        will in turn flatten them into a single urlpattern set.
        """
        source._modes = NamedRouteList(source.backend)
        urlpatterns = NamedRouteList(source.backend)

        # be nice and getattr to accommodate Django app_configs
        view_kwargs = dict(router=source, **kwargs)
        for route, viewset in getattr(source, 'viewsets', {}).items():
            # will store instances on source
            if not hasattr(source, '_viewsets'):
                source._viewsets = NamedRouter(source.backend)
            if not route in source._viewsets:
                source._viewsets[route] = viewset(**view_kwargs)
            viewset_urlpatterns = source._viewsets[route].get_urlpatterns()
            if viewset_urlpatterns:
                urlpatterns[route].extend(viewset_urlpatterns)
                existing_view_names = set(source._modes[route]) & \
                    set(source._viewsets[route])
                if existing_view_names:
                    raise ValueError('Attempted to overwrite existing view'
                                     'names: {}'.format(existing_view_names))
                source._modes[route].extend(source._viewsets[route])
        return urlpatterns

    def get_modes(self, route=None):
        """ Return a list of named views for the specified route. """
        return self._modes[route]

    def has_mode(self, mode, route=None):
        """ Return mode if it exists, else None. """
        return mode in self.get_modes(route=route)
