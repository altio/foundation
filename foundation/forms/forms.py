from __future__ import unicode_literals

from collections import OrderedDict
from django.forms import forms
from django.utils.functional import cached_property

from .fieldsets import Fieldset

__all__ = 'Form',


class BackendFormMixin(object):
    """
    Django's Base(Model)Form organizes Fields into a single Form.  Django Admin
    had the bright idea of leveraging Fieldsets (even if only one with no extra
    spec).  Let's make that the default treatment.
    """

    fieldset_class = Fieldset

    def __init__(self, fieldsets, prepopulated_fields, readonly_fields=None,
                 view=None, **kwargs):
        super(BackendFormMixin, self).__init__(**kwargs)
        self._fieldsets = []
        for name, options in fieldsets:
            key = name.lower().replace(' ', '_')
            if key in self.fields:
                raise KeyError(
                    'Fieldset "{}" conflicts with field of same name.'.format(
                        key))
            options = options.copy()
            options['name'] = options.pop('name', name)
            self._fieldsets.append(
                (key, self.fieldset_class(form=self, view=view, **options))
            )
        self._fieldsets = OrderedDict(self._fieldsets)
        self.prepopulated_fields = [{
            'field': self[field_name],
            'dependencies': [self[f] for f in dependencies]
        } for field_name, dependencies in prepopulated_fields.items()]
        self.view = view
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields

    def __getitem__(self, name):
        "Returns a BoundField with the given name."
        is_field, is_fieldset = False, False
        if name in self.fields:
            is_field = True
        elif name in self._fieldsets:
            is_fieldset = True
        if not (is_field or is_fieldset):
            raise KeyError(
                "Key '%s' not found in '%s'. Choices are: %s." % (
                    name,
                    self.__class__.__name__,
                    ', '.join(sorted(
                        f for f in tuple(self.fields.keys()) +
                        tuple(self._fieldsets.keys()))),
                )
            )
        if is_field:
            if name not in self._bound_fields_cache:
                fld = self.fields[name]
                self._bound_fields_cache[name] = fld.get_bound_field(self, name)
            ret = self._bound_fields_cache[name]
        elif is_fieldset:
            ret = self._fieldsets[name]
        return ret

    @property
    def fieldsets(self):
        for fieldset in self._fieldsets.values():
            yield fieldset

    @property
    def media(self):
        media = super(BackendFormMixin, self).media
        for fs in self.fieldsets:
            media = media + fs.media
        return media

    @cached_property
    def tabs(self):
        tab_list = []
        for tab_name in self.view.controller.tabs:
            try:
                tab = self[tab_name]
            except KeyError:
                tab = self.view.children[tab_name]
            tab_list.append((tab_name, tab))
        return OrderedDict(tab_list)


class Form(BackendFormMixin, forms.Form):
    """ Form with Backend voodoo (e.g. fieldsets) """
