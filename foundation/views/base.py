# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.forms.models import _get_foreign_key
from django.shortcuts import resolve_url
from django.template.defaultfilters import title
from django.utils.functional import cached_property
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import base

from ..forms import IS_POPUP_VAR, TO_FIELD_VAR
from ..template.response import TemplateResponse
from ..utils import flatten_fieldsets
from .controllers import BaseViewController


__all__ = 'View', 'TemplateView', 'AppIndexView'


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

        # re-map mode name to permission name
        mode = self.mode if self.mode != 'edit' else 'change'

        # helpers used throughout
        self.add = self.mode == 'add' or '_saveasnew' in request.POST
        self.edit = self.mode in ('add', 'edit')

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


class LoginRequiredMixin(object):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class BackendMixin(DispatchMixin):
    """
    Makes Views Backend-aware with overrides of core behaviors.

    "backend" to expose backend config to template logic
    "media" to provide media collection for components above and below views
    "get_handler()" to provide common data preparation prior to method handler
    """

    backend = None
    mode = None
    mode_title = ''
    response_class = TemplateResponse

    def get_media(self):
        return self.backend.media

    def get_context_data(self, **kwargs):
        kwargs.update(**self.backend.each_context(request=self.request))
        # in case backend passed media, overwrite it with backend et al
        kwargs['media'] = self.get_media()
        return super(BackendMixin, self).get_context_data(**kwargs)


class AppAccessMixin(DispatchMixin):

    def handle_common(self, handler, request, *args, **kwargs):
        """
        Raise 403 if logged in user does not have access to this app.
        """
        handler = super(AppAccessMixin, self).handle_common(
            handler, request, *args, **kwargs)
        if not getattr(self.app_config, 'is_public', False):
            if not request.user.has_module_perms(self.app_config.label):
                raise PermissionDenied('User does not have access to application.')
        return handler


class View(DispatchMixin, base.View):
    """ View with override of "dispatch" """


class TemplateView(BackendMixin, base.TemplateView):
    """ Backend-aware TemplateView """


class AppIndexView(AppAccessMixin, TemplateView):
    mode = "list"
    app_config = None
    backend = None
    template_name = 'app_index.html'

    def __init__(self, app_config, backend, **kwargs):
        self.app_config = app_config
        self.backend = backend
        super(AppIndexView, self).__init__(**kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update(
            app_label=self.app_config.label,
            app_name=self.app_config.verbose_name,
            app_controllers=[self.backend.get_registered_controller(model)
                             for model in self.app_config.get_models()
                             if self.backend.has_registered_controller(model)],
        )
        return super(AppIndexView, self).get_context_data(**kwargs)


class ControllerMixin(BaseViewController, AppAccessMixin, BackendMixin):
    """
    To be mixed in with Django CBV base classes.

    ** Need to pass kwargs through since this will get combined with View class.
    """

    def __init__(self, controller, **kwargs):
        # model and fields exist on View itself and need to be overwritten
        super(ControllerMixin, self).__init__(view=self,
                                              controller=controller,
                                              model=controller.model,
                                              fields=controller.fields,
                                              **kwargs)

    def get_title(self):
        if self.mode == 'list':
            return _('all {}'.format(self.controller.opts.verbose_name_plural))
        else:
            obj = getattr(self, 'object', None)
            return ('{} {}'.format(title(self.mode_title), obj)
                if obj
                else title('{} {}'.format(self.mode_title, self.controller.opts.verbose_name)))

    def get_context_data(self, **kwargs):
        opts = self.model._meta
        app_label = opts.app_label
        model_name = opts.model_name

        kwargs.update({
            'mode': self.mode,
            'opts': opts,
            'has_add_permission': self.has_add_permission(),
            'has_change_permission': self.has_edit_permission(),
            'has_delete_permission': self.has_delete_permission(),
            'to_field_var': TO_FIELD_VAR,
            'is_popup_var': IS_POPUP_VAR,
            'app_label': app_label,
            'model_name': model_name,
            'title': _(self.mode_title),
            # 'to_field': to_field,
            # errors=helpers.AdminErrorList(form, formsets),
            # preserved_filters=self.get_preserved_filters(request),
            'is_popup': (IS_POPUP_VAR in self.request.POST or
                         IS_POPUP_VAR in self.request.GET)

        })

        return super(ControllerMixin, self).get_context_data(**kwargs)

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

    def get_formsets_with_inlines(self, obj=None):
        """
        Yields tuples of FormSet class and InlineController instances.
        """
        for child in self.children.values():
            yield child.get_formset_class(obj), child

    def get_inline_formsets(self, obj, change):
        "Helper function to generate InlineFormSets for add/change_view."
        inline_formsets = []
        obj = obj if change else None
        fields = flatten_fieldsets(self.get_fieldsets(self.mode))
        for InlineFormSet, inline in self.get_formsets_with_inlines(obj):
            inline_fk_field = _get_foreign_key(
                self.model, inline.model, inline.fk_name)
            if inline_fk_field.remote_field.name not in fields:
                continue
            formset_kwargs = inline.get_formset_kwargs(
                formset_class=InlineFormSet, obj=obj)
            inline_formsets.append(InlineFormSet(**formset_kwargs))
        return inline_formsets

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

    def get_breadcrumbs(self):

        # start with the app index up top
        breadcrumbs = [(self.app_label,
                        resolve_url('{}:index'.format(self.app_label)))]

        if self.accessed_by_parent:
            parent_crumbs = []
            for parent in self.parents:
                parent_crumbs.append(parent.get_breadcrumb('view'))
                if parent.controller.is_local_root:
                    parent_crumbs.append(parent.get_breadcrumb('list'))
                    break
            breadcrumbs.extend(reversed(parent_crumbs))

        # always add the current view's list if we are not in list mode
        if self.mode != 'list':
            breadcrumbs.append(self.get_breadcrumb('list'))

        breadcrumbs.append(self.get_breadcrumb(self.mode))

        return breadcrumbs

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
