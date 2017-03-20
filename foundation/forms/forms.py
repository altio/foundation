from __future__ import unicode_literals

from collections import OrderedDict
from django.forms import forms

from .boundfield import ProxyField
from .fieldsets import Fieldset

__all__ = 'Form',


class BackendFormMixin(object):
    """
    Django's Base(Model)Form organizes Fields into a single Form.  Django Admin
    had the bright idea of leveraging Fieldsets (even if only one with no extra
    spec).  Let's make that the default treatment.
    """

    fieldset_class = Fieldset

    def __init__(self, fieldsets, prepopulated_fields, view_controller,
                 readonly_fields=None, **kwargs):
        super(BackendFormMixin, self).__init__(**kwargs)
        self.fieldsets = []
        for name, options in fieldsets:
            key = name.lower().replace(' ', '_')
            options = options.copy()
            options['name'] = options.pop('name', name)
            self.fieldsets.append(
                (key, self.fieldset_class(form=self, view_controller=view_controller, **options))
            )
        self.fieldsets = OrderedDict(self.fieldsets)
        self.prepopulated_fields = [{
            'field': self[field_name],
            'dependencies': [self[f] for f in dependencies]
        } for field_name, dependencies in prepopulated_fields.items()]
        self.view_controller = view_controller
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields

    @property
    def empty_value_display(self):
        return self.view_controller.get_empty_value_display()

    def __getitem__(self, name):
        """
        Returns a Bound or Readonly Field with the given name.
        """

        # lazily exit the getter when template tries to access an attr on form
        if hasattr(self, name):
            raise KeyError

        # get the unbound field or name as fallback for non-fields
        field = self.fields.get(name, name)

        # using whatever resolved ^ create the (ReadOnly/Bound)Field if missing
        if field not in self._bound_fields_cache:
            # TODO: implement as a CHECK similar to admin for RO fields
            self._bound_fields_cache[field] = (
                field.get_bound_field(self, name)
                if hasattr(field, 'get_bound_field')
                else ProxyField(self, field, name in self.readonly_fields)
            )
        return self._bound_fields_cache[field]

    @property
    def media(self):
        media = super(BackendFormMixin, self).media
        for fs in self.fieldsets:
            media = media + fs.media
        return media


class Form(BackendFormMixin, forms.Form):
    """ Form with Backend voodoo (e.g. fieldsets) """
