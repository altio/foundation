# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import resolve_url


class ModelResolver(object):
    """
    ModelResolver provides URL resolution by calling the appropriate Controller with
    a specified mode.  The Router uses some components (specifically, views,
    modes, get_view, url_prefix, and model_namespace, but the ModelResolver is
    attached to the registered controllers in-whole because the view controllers
    previously leaned on the registered state to generate the correct URLs.
    There may be a case for splitting the behaviors between those which truly
    belong on all Controllers, and those which belong on Registered (Router) and
    View Controllers only.
    """

    @property
    def url_prefix(self):
        url_prefix = getattr(
            self,
            'url_model_prefix',
            self.verbose_name_plural.lower().replace(' ', '-')
        )
        return (r'{}/'.format(url_prefix)
                if url_prefix is not None and url_prefix != ''
                else r'')

    @property
    def model_lookup(self):
        return '{}_{}'.format(self.app_label,
                              self.model_name)

    @property
    def app_namespace(self):
        namespace = getattr(self, 'url_app_namespace', self.app_label)
        return namespace or self.app_label

    @property
    def model_namespace(self):
        namespace = getattr(self, 'url_model_namespace', self.model_name)
        return namespace or self.model_name

    def get_namespace(self, route=None):
        """
        Used only by get_url_name during the resolution phase POST-construction.
        Router deals with app_namespace and model_namespace directly.
        :param route: optional, defaults to None
        """

        # look for registered controller, early exit if inline
        if not self.controller:
            return None

        controller = self.controller
        parent = controller.parent

        namespace_args = (
            [parent.get_namespace()]
            if parent and not controller.is_local_root
            else ([route, controller.app_namespace]
                  if route
                  else [controller.app_namespace]))
        namespace_args.append(controller.model_namespace)

        return ':'.join(namespace_args)

    def get_url_name(self, mode, route=None):

        # determine namespace, early exit if inline
        namespace = self.get_namespace(route=route)
        if not namespace:
            return None

        # re-map index to list view (for now) if permitted
        # TODO: make configurable?
        if mode == 'index':
            if not self.controller.is_local_root:
                raise NotImplementedError(
                    'Index URL for sub-controllers cannot be determined.')
            mode = 'list'

        has_mode = self.controller.has_mode(mode, route=route)
        return ':'.join((namespace, mode)) if has_mode else None

    def get_url_kwargs(self, mode, **kwargs):
        """
        This version of get_url_kwargs does no grooming and thus it will only
        work for a top-level Controller.
        See components.views.ChainingMixin for view kwargs injection.
        """

        return kwargs

    def get_url(self, mode, obj=None, route=None, **kwargs):

        # look for registered controller, bail if inline
        if not self.controller:
            return ValueError(
                'You attempted to use BaseController.get_url from an inline.  '
                'Refactor to use BaseViewController.get_url'
            )

        url_name = self.get_url_name(mode, route=route)

        if url_name:
            url_kwargs = self.get_url_kwargs(mode, **kwargs)

        return resolve_url(url_name, **url_kwargs) if url_name else None
