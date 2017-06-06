# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from collections import OrderedDict
from django.conf import settings
from django.conf.urls import url, include
from django.forms.widgets import MediaDefiningClass
from django.urls import resolve
from django.utils import six
from django.utils.functional import cached_property

from .. import utils
from .registry import NotRegistered
from .router import Router
from .views import TemplateView

__all__ = 'Backend', 'backends', 'get_backend'

logger = logging.getLogger(__name__)


class Backend(six.with_metaclass(MediaDefiningClass, Router)):

    admin_site = None  # allows for alternate admin site to be provided
    admin_url_prefix = None  # '' to put on root, 'admin' to emulate normal
    auth_url_prefix = None  # '' to put on root, 'accounts' to emulate normal
    create_permissions = False
    routes = ()
    site_index_class = TemplateView
    site_index_name = 'index'
    _empty_value_display = '-'

    @property
    def site(self):
        """
        It may seem like this should need the request but the plan is to make
        a SiteBackend registry at some point... for now we will assume one site.
        """
        from django.contrib.sites.models import Site
        return Site.objects.get(pk=settings.SITE_ID)

    @property
    def site_title(self):
        return self.site.name

    def __init__(self, *args, **kwargs):
        '''
        self.name = name
        self._actions = {'delete_selected': actions.delete_selected}
        self._global_actions = self._actions.copy()
        '''
        self.backend = self
        super(Backend, self).__init__(*args, **kwargs)

    def register(self, model_or_iterable, controller_class=None, **options):
        """
        Registers the given model(s) with the given controller class.

        The model(s) should be Model classes, not instances.

        If a controller class isn't given, it will use Controller (the default
        options). If keyword arguments are given -- e.g., list_display --
        they'll be applied as options to the controller class.

        If a model is already registered, this will raise AlreadyRegistered.

        If a model is abstract, this will raise ImproperlyConfigured.
        """
        from django.db.models.base import ModelBase
        if not controller_class:
            from .controllers import Controller
            controller_class = Controller
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            super(Backend, self).register(controller_class, model, **options)

    @cached_property
    def _routes(self):
        return set(self.routes) | set((None,))

    def get_app_urlpatterns(self, app_config):

        # set backend on app_config since may be using django appconfigs and the
        # kwargs build-out for AppViewSets will look to AppConfig for backend
        app_config.backend = self
        urlpatterns = super(Backend, self).get_urlpatterns(
            source=app_config, app_config=app_config)

        # start by getting all controller urlpatterns in-depth
        for model in app_config.get_models():
            try:
                controller = self.get_registered_controller(model)
            except NotRegistered:
                continue

            # if any controllers have public modes, app is public
            if controller.public_modes:
                app_config.has_public_views = True

            controller_namespace = controller.model_namespace
            controller_prefix = controller.url_prefix

            # get named patterns from controller and extend 
            controller_urlpatterns = controller.get_urlpatterns()
            for name, patterns in controller_urlpatterns.items():
                urlpatterns[name].append(
                    url((r'^{prefix}'.format(prefix=controller_prefix)
                         if controller_prefix
                         else ''),
                        include((patterns, controller_namespace))
                    ),
                )

        # set app_index_class on app to "None" to skip creation
        app_index_class = getattr(app_config, 'app_index_class', None)
        if app_index_class:
            template_name = getattr(app_config, 'template_name', 'app_index.html')
            app_index = app_index_class.as_view(
                app_config=app_config, backend=self, template_name=template_name
            )
            urlpatterns[None].append(url(r'^$', app_index, name='index'))

        return urlpatterns

    def get_urlpatterns(self, urlpatterns=None):
        """
        May be linked to ROOT_URLCONF directly or used to extend URLs from an
        existing urls.py file.
        """

        # gets the set of named urlpatterns from this controller's viewsets
        urlpatterns = super(Backend, self).get_urlpatterns(self)

        # URL auto-loader traverses all installed apps
        for app_config in utils.get_project_app_configs():

            # presume app configs are private
            app_config.has_public_views = False

            app_namespace = getattr(app_config,
                                    'url_namespace',
                                    app_config.label)

            urlprefix = getattr(app_config, 'url_prefix', None)
            urlprefix = (r'^{}/'.format(urlprefix or app_config.label)
                         if urlprefix != ''
                         else r'')
            app_urlpatterns = self.get_app_urlpatterns(app_config)

            # import the app's url patterns (if present)
            import_urls = getattr(app_config, 'import_urls', False)
            if import_urls:
                try:
                    app_urlpatterns[None].append(
                        url(r'', include(r'{}.urls'.format(app_config.name)))
                    )
                except ImportError:
                    pass

            for name, patterns in app_urlpatterns.items():
                urlpatterns[name].append(
                    url(urlprefix, include(
                        (patterns, app_namespace)))
                )

        # add a site index if one was provided
        if self.site_index_class:
            urlpatterns[None].append(
                url(r'^$',
                    self.site_index_class.as_view(
                        backend=self,
                        name=self.site_index_name,
                    ),
                    name='home')
            )

        # flatten urlpatterns
        for key in urlpatterns:
            if key is not None:
                urlpatterns[None].append(
                    url(r'^{}/'.format(key),
                        include((urlpatterns[key], key))),
                )
        urlpatterns = urlpatterns.pop(None, [])

        if self.admin_url_prefix is not None:
            from django.contrib.admin import site, autodiscover_modules
            if self.admin_site is None:
                self.admin_site = site
            autodiscover_modules(site=self.admin_site)
            def context_wrapper(func):
                def each_context(request):
                    kwargs = func(request)
                    kwargs.update(self.each_context(request))
                    return kwargs
                return each_context
            self.admin_site.each_context = context_wrapper(self.admin_site.each_context)
            urlpatterns += [
                url(r'^{}/'.format(self.admin_url_prefix)
                    if self.admin_url_prefix
                    else r'', self.admin_site.urls)
            ]

        if self.auth_url_prefix is not None:
            from django.contrib.auth import urls as auth_urls
            from .views.auth import ToggleSuperuser
            from functools import partial
            from .decorators import backend_context

            auth_urlpatterns = []
            for auth_urlpattern in auth_urls.urlpatterns:
                if auth_urlpattern.name == 'password_reset':
                    auth_urlpattern.callback = partial(
                        auth_urlpattern.callback,
                        email_template_name='registration/password_reset_email.txt',
                        html_email_template_name='registration/password_reset_email.html',
                    )
                auth_urlpattern.callback = backend_context(auth_urlpattern.callback, backend=self)
                auth_urlpatterns.append(auth_urlpattern)
            auth_urlpatterns.append(
                url(r'^toggle_superuser/$', ToggleSuperuser.as_view(), name='toggle_superuser'),
            )
            if self.auth_url_prefix:
                auth_urlpatterns = [
                    url(r'^{}/'.format(self.auth_url_prefix), include(auth_urlpatterns)),
                ]
            urlpatterns.extend(auth_urlpatterns)


        return urlpatterns

    @property
    def urls(self):
        """
        Shortcut for referencing backend URLs as ROOT_URLCONF
        """
        return self.get_urlpatterns()

    def get_available_apps(self, request):
        """
        Returns a sorted list of all the installed apps that have been
        registered in this site.
        """

        user = request.user
        available_apps = OrderedDict()
        for app_config in sorted(utils.get_project_app_configs(),
                                 key=lambda app_config: app_config.label):
            is_visible = False
            if app_config.has_public_views:
                is_visible = True
            elif user.has_module_perms(app_config.label):
                is_visible = True
            if is_visible:
                url_prefix = getattr(app_config, 'url_prefix', None)
                if url_prefix is None:
                    url_prefix = app_config.label
                try:
                    url = '/{}/'.format(url_prefix)
                    resolve(url)
                except:
                    pass
                else:
                    available_apps[app_config] = url

        return available_apps

    def each_context(self, request):
        """
        Returns a dictionary of variables to put in the template context for
        *every* page in the admin site.
        """

        return {
            'backend': self,
            'has_admin_urls': self.admin_site is not None,
            'has_auth_urls': self.auth_url_prefix is not None,
            'site_title': self.site_title,
            'available_apps': self.get_available_apps(request),
        }

    @property
    def empty_value_display(self):
        return self._empty_value_display

    @empty_value_display.setter
    def empty_value_display(self, empty_value_display):
        self._empty_value_display = empty_value_display


"""
Plan is to eventually actually allow for the declaration of per-Site Backends
and get them from a SiteBackend registry.  For now, using a singleton list.
"""

backends = []


def get_backend(site=None):
    global backends
    if not backends:
        backends.append(Backend())
    return backends[0]
