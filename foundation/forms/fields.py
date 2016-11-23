import sys
from django.forms import fields
from django.forms.fields import *  # NOQA
from .boundfield import BoundField

__all__ = fields.__all__


def get_bound_field(self, form, field_name):
    """ BoundField is probably better thought of as a "FormInstanceField" as it
    is *guaranteed* to be the container class of a field accessed via a form.
    Therefore, it is assessed to be the least hackish place to perform
    formfield callbacks that are form- (and controller) aware.
    """
    bound_field_cls = BoundField
    view = getattr(form, 'view', None)
    if view:
        formfield_callback = getattr(view, 'formfield_callback', None)
        if formfield_callback:
            formfield_callback(self)
        widget_callback = getattr(view, 'widget_callback', None)
        if widget_callback:
            widget_callback(self.widget)
        bound_field_cls = getattr(view, 'bound_field_class', bound_field_cls)
    return bound_field_cls(form, self, field_name)


this_module = sys.modules[__name__]
for name in __all__:
    field_class = getattr(this_module, name)
    field_class.get_bound_field = get_bound_field

del fields
