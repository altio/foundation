# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .. import backend
from . import models
from .views.base import FormChild, FormParent
from .viewsets import PageViewSet
from django.utils.functional import cached_property

__all__ = 'FormController', 'FormInline'


class FormOptions(backend.controllers.PartialViewOptions):

    prepopulated_fields = {}
    readonly_fields = ()

    formfield_overrides = {}
    radio_fields = {}
    raw_id_fields = ()
    classes = None

    modelform_class = models.ModelForm
    formset_form_class = models.FormSetModelForm
    formset_class = models.BaseModelFormSet
    inlineformset_class = models.BaseInlineFormSet

    template_paths = {
        'stacked': 'fragments/stacked',
        'tabular': 'fragments/tabular',
    }

    list_style = 'tabular'
    object_style = 'stacked'
    inline_style = 'tabular'


class FormController(FormOptions, backend.Controller):
    """
    Convenience Controller with FormViewSet attached to default namespace.
    """

    view_child_class = FormChild
    view_parent_class = FormParent
    viewsets = {
        None: PageViewSet,
    }


class FormInline(FormOptions, FormChild):

    @cached_property
    def parent_model(self):
        return self.view.controller.model

    def __getattribute__(self, name):
        """
        When a normal lookup fails, perform a secondary lookup in the model.
        """
        super_getattr = super(FormInline, self).__getattribute__

        try:
            return super_getattr(name)
        except AttributeError as e:
            model = super_getattr('model')
            try:
                return getattr(model._meta, name)
            except AttributeError:
                raise e
