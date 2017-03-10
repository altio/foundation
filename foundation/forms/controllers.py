# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import BaseViewController
from .components import InlineFormsetMixin

__all__ = 'InlineController', 'StackedInline', 'TabularInline'


class ControllerOptions(object):

    fields = None
    exclude = None
    fieldsets = None
    fk_name = None
    model = None
    ordering = None

    modelform_class = forms.ModelForm
    formset_class = forms.BaseModelFormSet
    formset_template = 'inline/tabular.html'

    # unevaluated
    raw_id_fields = ()

    filter_vertical = ()
    filter_horizontal = ()
    radio_fields = {}
    prepopulated_fields = {}
    formfield_overrides = {}
    readonly_fields = ()
    view_on_site = True  # TODO: remove see below
    show_full_result_count = True

    # can_delete = True
    show_change_link = False
    classes = None

    def update(self, attrs):
        for key in dir(self):
            if not key.startswith('_'):
                setattr(self, key, attrs.pop(key, getattr(self, key)))

    def __init__(self, attrs):
        super(ControllerOptions, self).__init__()
        self.update(attrs)

    def __getattribute__(self, name):
        """
        When an attribute is not found, attempt to pass-through to the Model
        Meta (Options).
        """

        super_getattr = super(ControllerOptions, self).__getattribute__
        model = super_getattr('model')
        try:
            return super_getattr(name)
        except AttributeError as e:
            try:
                return getattr(model._meta, name)
            except AttributeError:
                raise e


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
