# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from collections import OrderedDict
from django.conf import settings
from django.core.exceptions import ViewDoesNotExist
from django.forms.widgets import MediaDefiningClass
from django.urls.resolvers import LocaleRegexURLResolver, RegexURLResolver,\
    RegexURLPattern
from django.utils import six, translation
from django.utils.functional import cached_property

from .. import utils
from .registry import Registry, NotRegistered

__all__ = 'Backend', 'backends', 'get_backend'

logger = logging.getLogger(__name__)


def render(urlpatterns, base='', namespace=None, depth=0):

    views = {'patterns': {}, 'resolvers': {}}
    for p in urlpatterns:
        if isinstance(p, RegexURLPattern):
            try:
                if not p.name:
                    name = p.name
                elif namespace:
                    name = '{0}:{1}'.format(namespace, p.name)
                else:
                    name = p.name
                print('{}({}) {}'.format(('| '*(depth-1) + '|-') if depth else '', name, p.regex.pattern))
            except ViewDoesNotExist:
                continue
        elif isinstance(p, RegexURLResolver):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            if namespace and p.namespace:
                _namespace = '{0}:{1}'.format(namespace, p.namespace)
            else:
                _namespace = (p.namespace or namespace)
            print('{}({}) {}'.format(('| '*(depth-1) + '|-') if depth else '', _namespace, p.regex.pattern))
            if isinstance(p, LocaleRegexURLResolver):
                for langauge in settings.LANGUAGES:
                    with translation.override(langauge[0]):
                        render(patterns, base + p.regex.pattern, namespace=_namespace, depth=depth+1)
            else:
                render(patterns, base + p.regex.pattern, namespace=_namespace, depth=depth+1)

    return views


class Backend(six.with_metaclass(MediaDefiningClass, Registry)):

    create_permissions = False

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

    def get_urls(self, urlpatterns=None):
        """
        May be linked to ROOT_URLCONF directly or used to extend URLs from an
        existing urls.py file.  If it is extending patterns, auto-loading
        of urls.py files is disabled since that should have been done already.
        """
        existing_patterns = urlpatterns is not None
        if not existing_patterns:
            urlpatterns = []
        from django.conf.urls import url, include

        # URL auto-loader traverses all installed apps
        for app_config in utils.get_project_app_configs():
            app_namespace = getattr(app_config,
                                    'url_namespace',
                                    app_config.label)
            app_urlpatterns = utils.namespace_in_urlpatterns(
                urlpatterns, app_namespace
            )
            existing_patterns = bool(app_urlpatterns)
            if not existing_patterns:
                model_urlpatterns = []

            # only auto-load app URLs if defined
            if not existing_patterns:
                # attempt to append from the app's URLs
                try:
                    app_urlpatterns.append(
                        url(r'', include(r'{}.urls'.format(app_config.name)))
                    )
                except ImportError:
                    pass

            for model in app_config.get_models():
                model_name = model._meta.model_name
                model_urlpatterns = utils.namespace_in_urlpatterns(
                    app_urlpatterns, model_name
                )
                model_namespace_exists = bool(model_urlpatterns)
                if not model_urlpatterns:
                    model_urlpatterns = []
                try:
                    controller = self.get_registered_controller(model)
                except NotRegistered:
                    controller = None
                else:
                    controller.url_app_namespace = app_namespace
                    model_urlpatterns.extend(controller.urls)

                # if the namespace exists we already appended/extended in place
                if model_urlpatterns and not model_namespace_exists:
                    if controller:
                        model_namespace = controller.model_namespace
                        model_prefix = controller.url_prefix
                    else:
                        model_namespace = model._meta.model_name
                        model_prefix = model._meta.verbose_name_plural.lower(
                            ).replace(' ', '-')
                    app_urlpatterns.append(
                        url(('^{}'.format(model_prefix)
                             if model_prefix else ''), include(
                                (model_urlpatterns, model_namespace)
                            )),
                    )
            # add app-aware urls specified on the app config
            app_urlpatterns.extend(
                app_config.app_urls(self) if hasattr(app_config, 'app_urls') else []
            )

            # create an app index view if a named view is not provided
            # TODO: this is being added unconditionally right now... what we
            # really want to do is see if an index was specified (naturally or
            # explcitly) and only add this if we do not have one
            from .. import views
            AppIndex = getattr(app_config, 'AppIndexView', views.AppIndexView)
            app_index = AppIndex.as_view(app_config=app_config, backend=self)
            app_urlpatterns.append(url(r'^$', app_index, name='index'))
            # TODO: implement get_FOO_url for app_config
            app_config.index_url_name = '{}:index'.format(app_namespace)


            # if the namespace exists we already appended/extended in place
            if app_urlpatterns and not app_namespace_exists:
                urlprefix = getattr(app_config, 'url_prefix', app_config.label)
                urlprefix = (r'^{}/'.format(urlprefix)
                             if urlprefix is not None and urlprefix != ''
                             else r'')
                urlpatterns.append(
                    url(urlprefix, include(
                        (app_urlpatterns, app_namespace)))
                )

        SiteIndex = getattr(self, 'SiteIndex', None)
        if SiteIndex:
            urlpatterns.append(
                url(r'^$',
                    SiteIndex.as_view(backend=self),
                    name='home')
            )

        # render(urlpatterns)

        return urlpatterns

    @cached_property
    def urls(self):
        return self.get_urls()  # , 'admin', 'admin'

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
            if getattr(app_config, 'is_public', False):
                is_visible = True
            elif user.has_module_perms(app_config.label):
                is_visible = True
            available_apps[app_config] = is_visible

        return available_apps

    def each_context(self, request):
        """
        Returns a dictionary of variables to put in the template context for
        *every* page in the admin site.
        """

        return {
            'site_title': self.site_title,
            # 'site_header': self.site_header,
            # 'site_url': self.site_url,
            # 'has_permission': self.has_permission(view),
            'available_apps': self.get_available_apps(request),
        }
