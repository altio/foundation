# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.shortcuts import resolve_url
from functools import partial

__all__ = 'Resolver',


RE_MODE_URL = re.compile('get_(?P<mode>\w+)_url')
RE_MODE_URL_NAME = re.compile('get_(?P<mode>\w+)_url_name')


class Resolver(object):
    """
    Resolver provides URL resolution by calling the appropriate Controller with
    a specified mode.  The Router uses some components (specifically, views,
    modes, get_view, url_prefix, and model_namespace, but the Resolver is
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
            self.opts.verbose_name_plural.lower().replace(' ', '-')
        )
        return (r'{}/'.format(url_prefix)
                if url_prefix is not None and url_prefix != ''
                else r'')

    @property
    def model_lookup(self):
        return '{}_{}'.format(self.opts.app_label,
                              self.opts.model_name)

    @property
    def app_namespace(self):
        namespace = getattr(self, 'url_app_namespace', self.opts.app_label)
        return namespace or self.opts.app_label

    @property
    def model_namespace(self):
        namespace = getattr(self, 'url_model_namespace', self.opts.model_name)
        return namespace or self.opts.model_name

    def get_namespace(self, subcontroller=None):
        """
        Used only by get_url_name during the resolution phase POST-construction.
        Router deals with app_namespace and model_namespace directly.
        :param subcontroller: optional, defaults to self
        """

        # early exit if the subcontroller is specified and not present
        controller = self.controller
        if subcontroller and subcontroller not in controller.registered_views:
            return None

        # normal namespace determination for *this* controller
        parent = controller.parent

        namespace_args = [
            parent.get_namespace()
            if parent and not controller.is_local_root
            else controller.app_namespace,
            controller.model_namespace
        ]

        # by this point we know if a subcontroller was specified it exists
        if subcontroller:
            namespace_args.append(subcontroller.model_namespace)

        return ':'.join(namespace_args)

    def get_url_name(self, mode, subcontroller=None):

        # if there is no registered Controller (some inlines), return None
        if not self.controller:
            return None

        # re-map index to list view (for now) if permitted
        # TODO: make configurable?
        if mode == 'index':
            if subcontroller or not self.controller.is_local_root:
                raise NotImplementedError(
                    'Index URL for sub-controllers cannot be determined.')
            mode = 'list'

        namespace = None

        # if subcontroller provided, use that for internal namespace lookup
        if subcontroller:

            if self.controller.has_url(mode, subcontroller):
                namespace = self.get_namespace(subcontroller)

        # fall back to normal lookup if no subcontroller
        else:
            """
            TODO: Issue dev warning if we get here?  On one hand, None is used
            to indicated there was no path.  On the other hand, such a silent
            fail could be hard to debug
            """
            namespace = self.get_namespace()

        return ':'.join((namespace, mode)) if namespace else None

    def get_url_kwargs(self, mode, **kwargs):
        """
        This version of get_url_kwargs does no grooming and thus it will only
        work for a top-level Controller.
        See views.components.ChainingMixin for view kwargs injection.
        """

        return kwargs

    def get_url(self, mode, subcontroller=None, **kwargs):

        url_name, url_kwargs = None, None

        # if there is a subcontroller request, never consider self
        if subcontroller:
            # try to get the subcontroller directly attached to this view
            url_name = self.get_url_name(mode, subcontroller)

            # if found, use the current single-object kwargs as the path
            if url_name:
                url_kwargs = self.get_url_kwargs('view', **kwargs)

            # otherwise, perform a direct lookup
            else:
                url_name = subcontroller.get_url_name(mode)

                # if a url is found there, look at the subcontroller to see if
                # if needs any additional help (e.g. the path)
                url_kwargs = (
                    subcontroller.get_url_kwargs(mode, **kwargs)
                    if subcontroller.is_local_root
                    else self.get_url_kwargs('view', **kwargs)
                )


        else:
            url_name = self.get_url_name(mode)
            url_kwargs = self.get_url_kwargs(mode, **kwargs)

        return resolve_url(url_name, **url_kwargs) if url_name else None

    def __getattribute__(self, name):
        super_getattr = super(Resolver, self).__getattribute__

        mode_url_name = re.match(RE_MODE_URL_NAME, name)
        if mode_url_name:
            method = super_getattr('get_url_name')
            return partial(method, mode=mode_url_name.group('mode'))

        mode_url = re.match(RE_MODE_URL, name)
        if mode_url and name not in ('get_success_url', 'get_absolute_url'):
            method = super_getattr('get_url')
            return partial(method, mode=mode_url.group('mode'))

        return super_getattr(name)
