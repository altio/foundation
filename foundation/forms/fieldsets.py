# -*- coding: utf-8 -*-
# CONCEPT: django.contrib.admin.helpers 1.10
from __future__ import unicode_literals

import os
from django import forms
from django.utils import six
from django.utils.safestring import mark_safe


class Fieldline(object):
    def __init__(self, form, fieldline, readonly_fields=None, view_controller=None):
        self.form = form
        self.fields = [fieldline] if not hasattr(fieldline, "__iter__") or isinstance(
            fieldline, six.text_type
        ) else fieldline
        self.has_visible_field = not all(
            field in self.form.fields and
            self.form.fields[field].widget.is_hidden
            for field in self.fields
        )
        self.view_controller = view_controller
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields

    def __iter__(self):
        for field in self.fields:
            yield self.form[field]

    def __len__(self):
        return len(self.fields)

    def errors(self):
        return mark_safe(
            '\n'.join(
                self.form[f].errors.as_ul()
                for f in self.fields
                if f not in self.readonly_fields and not self.form[f].is_proxy
            ).strip('\n')
        )


class Fieldset(object):
    def __init__(self, form, name=None, readonly_fields=(), fields=(),
                 classes=(), description=None, view_controller=None,
                 template_name=None):
        self.form = form
        self.name = name
        self.fields = fields
        self.classes = ' '.join(classes)
        self.description = description
        self.view_controller = view_controller
        self.readonly_fields = readonly_fields
        self.template_name = template_name

    @property
    def media(self):
        return forms.Media()

    @property
    def template(self):
        return os.path.join(
            self.view_controller.template_paths[self.view_controller.object_style],
            self.template_name
        ) if self.template_name else 'fragments/stacked/fieldset.html'

    def __iter__(self):
        for fieldline in self.fields:
            yield Fieldline(form=self.form, fieldline=fieldline,
                            readonly_fields=self.readonly_fields,
                            view_controller=self.view_controller)


class InlineFieldset(Fieldset):
    def __init__(self, formset, *args, **kwargs):
        self.formset = formset
        super(InlineFieldset, self).__init__(*args, **kwargs)

    def __iter__(self):
        fk = getattr(self.formset, "fk", None)
        for field in self.fields:
            if fk and fk.name == field:
                continue
            yield Fieldline(form=self.form, field=field,
                            readonly_fields=self.readonly_fields,
                            view_controller=self.view_controller)
