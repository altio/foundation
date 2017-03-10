# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .. import backend
from . import models
from .views.base import ViewChild
from .viewsets import FormViewSet

__all__ = 'Controller', 'ViewChild', 'StackedInline', 'TabularInline'


class FormOptions(object):

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

    list_templates = {
        'stacked': 'fragments/list/stacked.html',
        'tabular': 'fragments/list/tabular.html',
    }


class Controller(FormOptions, backend.Controller):
    """
    Convenience Controller with FormViewSet attached to default namespace.
    """

    view_child_class = ViewChild
    viewsets = {
        None: FormViewSet,
    }


class FormInline(FormOptions, ViewChild):
    pass


class StackedInline(FormInline):
    list_template_name = 'stacked'


class TabularInline(FormInline):
    list_template_name = 'tabular'
