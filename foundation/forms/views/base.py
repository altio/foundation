# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.shortcuts import resolve_url
from django.template.defaultfilters import title
from django.utils.translation import ugettext_lazy as _
from django.urls.exceptions import NoReverseMatch

from ...backend import views
from .components import FormSetMixin
from ...backend.views.controller.mixins import variables

IS_POPUP_VAR = '_popup'

IGNORED_PARAMS = variables.IGNORED_PARAMS + (IS_POPUP_VAR, )


class TitleMixin(object):
    """
    Provides FormViewControllers with ability to determine their title.
    """

    def get_title(self):
        if self.mode == 'list':
            ret = (
                str(self.view_parent.get_object())
                if self.view_parent
                else _('all') if self.public_modes else str(self.user) + "'s"
            )
            ret += ' {}'.format(self.verbose_name_plural)
        else:
            obj = getattr(self, 'object', None)
            return ('{} {}'.format(title(self.view.mode_title), obj)
                if obj
                else title('{} {}'.format(self.view.mode_title, self.verbose_name)))
        return ret


class FormChild(TitleMixin, FormSetMixin, views.ViewChild):

    mode = 'list'

    @property
    def inline_template(self):
        return os.path.join(
            self.template_paths[self.inline_style],
            'list.html'
        )

    def get_formset_kwargs(self, formset_class, obj=None, queryset=None, **kwargs):
        if self.view.add and not queryset:
            queryset = self.get_associated_queryset().none()
        return super(FormChild, self).get_formset_kwargs(formset_class, obj=obj, queryset=queryset, **kwargs)


class BreadcrumbMixin(TitleMixin):

    def get_label(self, mode):
        return '{}'.format(self.verbose_name_plural
                           if mode == 'list'
                           else (self.verbose_name
                                 if mode == 'add'
                                 else self.get_object()))

    def get_breadcrumb(self, mode):
        """
        Helper method to return the components of a breadcrumb.
        :param mode: (str) a valid view mode for this controller
        :param kwargs: (dict str:str) a dictionary of view kwargs to use
        :rtype: 2-tuple of strings: label, url
        """

        url = self.get_url(mode)
        label = self.get_label(mode) if url else None
        return label, url


class FormParent(BreadcrumbMixin, views.ViewParent):

    pass


class ControllerTemplateMixin(BreadcrumbMixin, views.ControllerViewMixin, views.BackendTemplateMixin):

    def handle_common(self, handler, request, *args, **kwargs):
        handler = super(ControllerTemplateMixin, self).handle_common(handler, request, *args, **kwargs)

        self.is_popup = (IS_POPUP_VAR in self.request.POST or
                         IS_POPUP_VAR in self.request.GET)

        return handler

    def get_breadcrumbs(self):

        # start with the app index up top
        try:
            breadcrumbs = [(self.app_label,
                            resolve_url('{}:index'.format(self.app_label)))]
        except NoReverseMatch:
            breadcrumbs = []

        parent_crumbs = []
        for view_parent in self.view_parents:
            parent_crumbs.append(view_parent.get_breadcrumb('display'))
            if view_parent.controller.is_local_root:
                parent_crumbs.append(view_parent.get_breadcrumb('list'))
                break
        breadcrumbs.extend(reversed(parent_crumbs))

        # always add the current view's list if we are not in list mode
        if self.mode != 'list':
            breadcrumbs.append(self.get_breadcrumb('list'))

        breadcrumbs.append((self.get_title(), self.request.path))

        return breadcrumbs

    def get_context_data(self, **kwargs):
        kwargs.update({
            'view_controller': self,
            'is_popup_var': IS_POPUP_VAR,
        })
        return super(ControllerTemplateMixin, self).get_context_data(**kwargs)

    @property
    def embed_template(self):
        return os.path.join('embed', self.template_name)

    @property
    def form_template(self):
        return os.path.join(
            self.template_paths[self.list_style
                                if self.mode=='list'
                                else self.object_style],
            self.template_name
        )
