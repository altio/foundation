# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ... import forms

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
