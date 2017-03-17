# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .. import backend
from . import models
from .views.base import ViewChild
from .viewsets import FormViewSet

__all__ = 'FormController', 'FormInline'


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

    template_paths = {
        'stacked': 'fragments/stacked',
        'tabular': 'fragments/tabular',
    }

    list_template = 'tabular'
    object_template = 'stacked'
    inline_template = 'tabular'


class FormController(FormOptions, backend.Controller):
    """
    Convenience Controller with FormViewSet attached to default namespace.
    """

    view_child_class = ViewChild
    viewsets = {
        None: FormViewSet,
    }


class FormInline(FormOptions, ViewChild):
    pass
