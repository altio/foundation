from django.forms import boundfield, fields
from django.forms.utils import flatatt
from django.utils import six
from django.utils.encoding import force_text, smart_text
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.reverse_related import ManyToManyRel
from django.template.defaultfilters import linebreaksbr, capfirst

from ..utils import lookup_field, display_for_field, label_for_field, \
    help_text_for_field

__all__ = ('BoundField', 'ProxyField')


class BoundField(boundfield.BoundField):
    """ Based on django.contrib.admin.helpers 1.10 """
    is_readonly = False
    view_controller = None

    @property
    def empty_value_display(self):
        return self.view_controller.get_empty_value_display() \
            if self.view_controller else ''

    @property
    def is_checkbox(self):
        return isinstance(self.field.widget, fields.CheckboxInput)

    def contents(self):

        name, obj, controller = self.name, self.form.instance, self.view_controller
        try:
            f, attr, value = lookup_field(name, obj, controller)
        except (AttributeError, ValueError, ObjectDoesNotExist):
            result_repr = self.empty_value_display
        else:
            if isinstance(f.remote_field, ManyToManyRel) and value is not None:
                result_repr = ", ".join(map(six.text_type, value.all()))
            else:
                result_repr = display_for_field(value, f, self.empty_value_display)
            result_repr = linebreaksbr(result_repr)

        return conditional_escape(result_repr)


class ProxyField(object):

    def __init__(self, form, field, is_readonly):
        self.form = form
        self.view_controller = form.view_controller
        self.is_checkbox = False
        self.is_readonly = is_readonly

        # Make self.field look a little bit like a field. This means that
        # {{ field.name }} must be a useful class name to identify the field.
        # For convenience, store other field-related data here too.
        self.name = (
            (field.__name__ if field.__name__ != '<lambda>' else '')
            if callable(field)
            else field
        )
        self.label = (
            form._meta.labels[self.name]
            if form._meta.labels and self.name in form._meta.labels
            else label_for_field(field, form._meta.model, self.view_controller)
        )
        self.help_text = (
            form._meta.help_texts[self.name]
            if form._meta.help_texts and self.name in form._meta.help_texts
            else help_text_for_field(self.name, form._meta.model)
        )

        try:
            self.field, self.attr, self.value = lookup_field(
                self.name, self.form.instance, self.view_controller
            )
        except (AttributeError, ValueError, ObjectDoesNotExist):
            self.field = None
            self.attr = None
            self.value = self.empty_value_display

    @property
    def empty_value_display(self):
        return self.view_controller.get_empty_value_display() \
            if self.view_controller else ''

    def label_tag(self):
        attrs = {}
        label = self.label
        return format_html('<label{}>{}:</label>',
                           flatatt(attrs),
                           capfirst(force_text(label)))

    def __str__(self):
        return str(self.value)

    @property
    def contents(self):
        if self.field is None:
            if hasattr(self.value, "__html__"):
                result_repr = self.value
            else:
                result_repr = smart_text(self.value)
                if getattr(self.attr, "allow_tags", False):
                    result_repr = mark_safe(self.value)
                else:
                    result_repr = linebreaksbr(result_repr)
        else:
            if isinstance(self.field.remote_field, ManyToManyRel) and self.value is not None:
                result_repr = ", ".join(map(six.text_type, self.value.all()))
            else:
                result_repr = display_for_field(self.value, self.field, self.empty_value_display)
            result_repr = linebreaksbr(result_repr)

        return conditional_escape(result_repr)
