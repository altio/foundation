# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
from django.conf import settings
from django.template.exceptions import TemplateDoesNotExist
from django.views.generic import base
from django.urls import resolve

from ...template.response import TemplateResponse
from ...utils import redirect_to_url

__all__ = 'BackendMixin', 'DispatchMixin', 'AppPermissionsMixin', 'AppMixin', \
    'View', 'TemplateView', 'AppView', 'AppTemplateView', 'BackendTemplateMixin'


class DispatchMixin(object):
    """
    HARD OVERRIDE of View's dispatch behavior.
    """

    def get_handler(self, request, *args, **kwargs):
        """
        get_handler will return None to indicate "proceed with the normal
        method handler"
        """

        return None

    def handle_common(self, handler, request, *args, **kwargs):
        """
        Once a handler has been resolved and the the method is confirmed to be
        allowed, perform common work and do any validation needed.
        Return the handler passed or an alternate, as appropriate.
        """

        return handler

    def dispatch(self, request, *args, **kwargs):
        """ HARD OVERRIDE OF View """

        handler = self.get_handler(request, *args, **kwargs)

        # normal behavior
        if handler is None:
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(), None)
        if handler is None:
            handler = self.http_method_not_allowed

        # common work moment before dispatch
        handler = self.handle_common(handler, request, *args, **kwargs)

        # dispatch
        return handler(request, *args, **kwargs)


class BackendMixin(DispatchMixin):
    """
    Makes Views Backend-aware with overrides of core behaviors.

    "backend" to expose backend config to template logic
    "media" to provide media collection for components above and below views
    "get_handler()" to provide common data preparation prior to method handler
    """

    backend = None
    route = None
    name = None


class View(BackendMixin, base.View):
    """ View with override of "dispatch" """


class BackendTemplateMixin(BackendMixin, base.TemplateResponseMixin,
                           base.ContextMixin):

    # TODO: extract mode/mode_title pieces from controller as needed
    mode_title = ''
    response_class = TemplateResponse
    _template_name = None

    def get_media(self):
        return self.backend.media

    def get_context_data(self, **kwargs):
        kwargs.update(**self.backend.each_context(request=self.request))
        # in case backend passed media, overwrite it with backend et al
        kwargs['media'] = self.get_media()
        return super(BackendMixin, self).get_context_data(**kwargs)

    @property
    def template_name(self):
        """
        Returns the setter-set template_name without modification, or the
        template name composed of this view's route and name.
        """
        if not self._template_name:
            if not self.name:
                raise TemplateDoesNotExist(
                    'The view must be provided with a "name" or "template_name"'
                )
            self._template_name = '{}{}.html'.format(
                '{}/'.format(self.route) if self.route else '',
                self.name,
            )
        return self._template_name

    @template_name.setter
    def template_name(self, val):
        self._template_name = val


class TemplateView(BackendTemplateMixin, base.TemplateView):
    """ Backend-aware TemplateView """


class AppPermissionsMixin(BackendMixin):
    """
    Redirect to login if logged in (or anonymous) user lacks access to app and
    it is not public.
    """

    def dispatch(self, request, *args, **kwargs):
        if not (self.app_config.has_public_views or
                request.user.has_module_perms(self.app_config.label)):
            return redirect_to_url(request, settings.LOGIN_URL)
        return super(AppPermissionsMixin, self).dispatch(
            request, *args, **kwargs
        )


class AppMixin(AppPermissionsMixin):
    app_config = None

    def __init__(self, app_config, **kwargs):
        self.app_config = app_config
        super(AppMixin, self).__init__(**kwargs)


class AppView(AppMixin, View):
    """ View with override of "dispatch" """


class AppTemplateMixin(AppMixin):

    def get_app_controllers(self):
        """
        Returns a sorted list of all of the registered model controllers that
        are accessible to the user.
        """
        user = self.request.user
        available_controllers = OrderedDict()

        app_url = getattr(self.app_config, 'url_prefix', None)
        if app_url is None:
            app_url = self.app_config.label
        app_url = ('/' + app_url + '/') if app_url else '/'

        for model in sorted([model
                             for model in self.app_config.get_models()
                             if self.backend.has_registered_controller(model)],
                             key=lambda model: model._meta.verbose_name):
            is_visible = False
            controller = self.backend.get_registered_controller(model)
            verbose_name = model._meta.verbose_name
            if controller.public_modes:
                is_visible = True
            elif user.has_module_perms(verbose_name):
                is_visible = True
            if is_visible:
                try:
                    url = app_url + controller.url_prefix
                    resolve(url)
                except:
                    url = None
            available_controllers[controller] = url

        return available_controllers

    def get_context_data(self, **kwargs):
        kwargs.update(
            app_config=self.app_config,
            app_label=self.app_config.label,
            app_name=self.app_config.verbose_name,
            app_controllers=self.get_app_controllers(),
        )
        return super(AppMixin, self).get_context_data(**kwargs)


class AppTemplateView(AppTemplateMixin, TemplateView):
    """ Backend-aware TemplateView """
