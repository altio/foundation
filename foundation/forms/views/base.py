# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.shortcuts import resolve_url
from django.template.defaultfilters import title
from django.utils.translation import ugettext_lazy as _
from django.urls.exceptions import NoReverseMatch

from ...backend import views
from .components import FormSetMixin


class TitleMixin(object):
    """
    Provides FormViewControllers with ability to determine their title.
    """

    def get_title(self):
        if self.mode == 'list':
            ret = (
                self.view_parent.get_object()
                if self.view_parent
                else _('all') if self.public_modes else str(self.user) + "'s"
            )
            ret += ' {}'.format(self.controller.verbose_name_plural)
        else:
            obj = getattr(self, 'object', None)
            return ('{} {}'.format(title(self.mode_title), obj)
                if obj
                else title('{} {}'.format(self.mode_title, self.controller.verbose_name)))
        return ret


class FormChild(TitleMixin, FormSetMixin, views.ViewChild):

    def get_permissions_model(self):
        permissions_model = super(FormChild, self).get_permissions_model()

        if permissions_model._meta.auto_created:
            # The model was auto-created as intermediary for a
            # ManyToMany-relationship, find the target model
            for field in permissions_model._meta.fields:
                if field.remote_field and field.remote_field.model != self.view.model:
                    permissions_model = field.remote_field.model
                    break

        return permissions_model

    def get_queryset(self):
        # early exit if this is an inline in edit mode and we are not permitted
        if self.view.add or self.view.edit and not self.has_permission('edit'):
            return self.model._default_manager.get_queryset().none()

        return super(FormChild, self).get_queryset()

    def get_url(self, mode, **kwargs):
        url = self.view.get_url(mode, self.controller, **kwargs)
        if not url:
            url = super(FormChild, self).get_url(mode, **kwargs)
        return url

    @property
    def inline_template(self):
        return os.path.join(
            self.template_paths[self.inline_template],
            self.template_name
        )


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


class FormControllerViewMixin(BreadcrumbMixin, views.ControllerViewMixin, views.BackendTemplateMixin):

    def get_context_data(self, **kwargs):
        opts = self.model._meta
        app_label = opts.app_label
        model_name = opts.model_name

        kwargs.update({
            'mode': self.mode,
            'opts': opts,
            'app_label': app_label,
            'model_name': model_name,
            'title': _(self.mode_title),
        })

        return super(FormControllerViewMixin, self).get_context_data(**kwargs)

    def get_breadcrumbs(self):

        # start with the app index up top
        try:
            breadcrumbs = [(self.app_label,
                            resolve_url('{}:index'.format(self.app_label)))]
        except NoReverseMatch:
            breadcrumbs = []

        parent_crumbs = []
        for view_parent in self.view_parents:
            parent_crumbs.append(view_parent.get_breadcrumb('view'))
            if view_parent.controller.is_local_root:
                parent_crumbs.append(view_parent.get_breadcrumb('list'))
                break
        breadcrumbs.extend(reversed(parent_crumbs))

        # always add the current view's list if we are not in list mode
        if self.mode != 'list':
            breadcrumbs.append(self.get_breadcrumb('list'))

        breadcrumbs.append((self.get_title(), self.request.path))

        return breadcrumbs

    @property
    def view_template(self):
        return os.path.join(
            self.template_paths[self.list_template
                                if self.mode=='list'
                                else self.object_template],
            self.template_name
        )
