# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import BaseViewController
from .components import InlineFormsetMixin

__all__ = 'InlineController', 'StackedInline', 'TabularInline'


class InlineModeTemplates(object):
    STACKED = 'inline/stacked.html'
    TABULAR = 'inline/tabular.html'


class InlineController(InlineFormsetMixin, BaseViewController):

    INLINE_MODES = InlineModeTemplates()

    def get_permissions_model(self):
        permissions_model = super(InlineController, self).get_permissions_model()

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

        return super(InlineController, self).get_queryset()

    def get_url(self, mode, **kwargs):
        url = self.view.get_url(mode, self.controller, **kwargs)
        if not url:
            url = super(InlineController, self).get_url(mode, **kwargs)
        return url


class StackedInline(InlineController):
    formset_template = InlineController.INLINE_MODES.STACKED


class TabularInline(InlineController):
    formset_template = InlineController.INLINE_MODES.TABULAR
