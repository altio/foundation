# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .. import backend
from . import models
from .views.base import FormChild, FormParent
from .viewsets import PageViewSet, EmbedViewSet
from django.utils.functional import cached_property

__all__ = 'PageController', 'EmbedController', 'FormInline'


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


class PageController(FormOptions, backend.Controller):
    """
    Convenience Controller with PageViewSet attached to default namespace.
    """

    view_child_class = FormChild
    view_parent_class = FormParent
    viewsets = {
        None: PageViewSet,
    }


class EmbedController(PageController):
    """
    Convenience Controller with PageViewSet attached to default namespace and
    EmbedViewSet attached to "embed" namespace to allow for AHAH calls using
    complete forms.
    """

    viewsets = {
        None: PageViewSet,
        'embed': EmbedViewSet,
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
