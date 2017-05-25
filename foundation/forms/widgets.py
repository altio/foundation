"""
Form Widget classes specific to the Django admin site.
"""
from __future__ import unicode_literals

import copy

from django.db.models.deletion import CASCADE
from django.forms import widgets
from django.forms.widgets import *
from django.template.loader import render_to_string
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils import six
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import Truncator
from django.utils.translation import ugettext as _

__all__ = widgets.__all__ + (
    'FilteredSelectMultiple', 'ForeignKeyRawIdWidget', 'ForeignKeyRawIdWidget',
    'RelatedFieldWidgetWrapper', 'CurrencyInput'
)
del widgets


class FilteredSelectMultiple(SelectMultiple):
    """
    A SelectMultiple with a JavaScript filter interface.

    Note that the resulting JavaScript assumes that the jsi18n
    catalog has been loaded in the page
    """
    @property
    def media(self):
        js = ["core.js", "SelectBox.js", "SelectFilter2.js"]
        return Media(js=["admin/js/%s" % path for path in js])

    def __init__(self, verbose_name, is_stacked, attrs=None, choices=()):
        self.verbose_name = verbose_name
        self.is_stacked = is_stacked
        super(FilteredSelectMultiple, self).__init__(attrs, choices)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['class'] = 'selectfilter'
        if self.is_stacked:
            attrs['class'] += 'stacked'

        attrs['data-field-name'] = self.verbose_name
        attrs['data-is-stacked'] = int(self.is_stacked)
        output = super(FilteredSelectMultiple, self).render(name, value, attrs)
        return mark_safe(output)


def url_params_from_lookup_dict(lookups):
    """
    Converts the type of lookups specified in a ForeignKey limit_choices_to
    attribute to a dictionary of query parameters
    """
    params = {}
    if lookups and hasattr(lookups, 'items'):
        items = []
        for k, v in lookups.items():
            if callable(v):
                v = v()
            if isinstance(v, (tuple, list)):
                v = ','.join(str(x) for x in v)
            elif isinstance(v, bool):
                v = ('0', '1')[v]
            else:
                v = six.text_type(v)
            items.append((k, v))
        params.update(dict(items))
    return params


class ForeignKeyRawIdWidget(TextInput):
    """
    A Widget for displaying ForeignKeys in the "raw_id" interface rather than
    in a <select> box.
    """
    def __init__(self, rel, view_controller, attrs=None, using=None):
        self.rel = rel
        self.view_controller = view_controller
        self.db = using
        super(ForeignKeyRawIdWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        rel_to = self.rel.model
        if attrs is None:
            attrs = {}
        extra = []
        if rel_to in self.view_controller._registry:
            # The related object is registered with the same AdminSite
            related_url = reverse(
                'admin:%s_%s_changelist' % (
                    rel_to._meta.app_label,
                    rel_to._meta.model_name,
                ),
                current_app=self.view_controller.name,
            )

            params = self.url_parameters()
            if params:
                url = '?' + '&amp;'.join('%s=%s' % (k, v) for k, v in params.items())
            else:
                url = ''
            if "class" not in attrs:
                attrs['class'] = 'vForeignKeyRawIdAdminField'  # The JavaScript code looks for this hook.
            # TODO: "lookup_id_" is hard-coded here. This should instead use
            # the correct API to determine the ID dynamically.
            extra.append(
                '<a href="%s%s" class="related-lookup" id="lookup_id_%s" title="%s"></a>'
                % (related_url, url, name, _('Lookup'))
            )
        output = [super(ForeignKeyRawIdWidget, self).render(name, value, attrs)] + extra
        if value:
            output.append(self.label_for_value(value))
        return mark_safe(''.join(output))

    def base_url_parameters(self):
        limit_choices_to = self.rel.limit_choices_to
        if callable(limit_choices_to):
            limit_choices_to = limit_choices_to()
        return url_params_from_lookup_dict(limit_choices_to)

    def url_parameters(self):
        from django.contrib.admin.views.main import TO_FIELD_VAR
        params = self.base_url_parameters()
        params.update({TO_FIELD_VAR: self.rel.get_related_field().name})
        return params

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.model._default_manager.using(self.db).get(**{key: value})
        except (ValueError, self.rel.model.DoesNotExist):
            return ''

        label = '&nbsp;<strong>{}</strong>'
        text = Truncator(obj).words(14, truncate='...')
        try:
            change_url = reverse(
                '%s:%s_%s_change' % (
                    self.view_controller.name,
                    obj._meta.app_label,
                    obj._meta.object_name.lower(),
                ),
                args=(obj.pk,)
            )
        except NoReverseMatch:
            pass  # Admin not registered for target model.
        else:
            text = format_html('<a href="{}">{}</a>', change_url, text)

        return format_html(label, text)


class ManyToManyRawIdWidget(ForeignKeyRawIdWidget):
    """
    A Widget for displaying ManyToMany ids in the "raw_id" interface rather than
    in a <select multiple> box.
    """
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        if self.rel.model in self.admin_site._registry:
            # The related object is registered with the same AdminSite
            attrs['class'] = 'vManyToManyRawIdAdminField'
        if value:
            value = ','.join(force_text(v) for v in value)
        else:
            value = ''
        return super(ManyToManyRawIdWidget, self).render(name, value, attrs)

    def url_parameters(self):
        return self.base_url_parameters()

    def label_for_value(self, value):
        return ''

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value:
            return value.split(',')


class RelatedFieldWidgetWrapper(Widget):
    """
    This class is a wrapper to a given widget to add the add icon for the
    admin interface.
    """
    template = 'admin/related_widget_wrapper.html'

    def __init__(self, widget, rel, related_controller, can_add_related=None,
                 can_change_related=False, can_delete_related=False):
        self.needs_multipart_form = widget.needs_multipart_form
        self.attrs = widget.attrs
        self.choices = widget.choices
        self.widget = widget
        self.rel = rel

        # related controller is either a ViewController subclass or a
        # registered Controller
        self.controller = (related_controller.controller
                           if related_controller
                           else None)
        self.view_controller = (None
                                if related_controller == self.controller
                                else related_controller)

        # Backwards compatible check for whether a user can add related
        # objects.
        if can_add_related is None:
            can_add_related = self.view_controller is not None
        self.can_add_related = can_add_related
        # XXX: The UX does not support multiple selected values.
        multiple = getattr(widget, 'allow_multiple_selected', False)
        self.can_change_related = not multiple and can_change_related
        # XXX: The deletion UX can be confusing when dealing with cascading deletion.
        cascade = getattr(rel, 'on_delete', None) is CASCADE
        self.can_delete_related = not multiple and not cascade and can_delete_related

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.widget = copy.deepcopy(self.widget, memo)
        obj.attrs = self.widget.attrs
        memo[id(self)] = obj
        return obj

    @property
    def is_hidden(self):
        return self.widget.is_hidden

    @property
    def media(self):
        return self.widget.media

    def get_related_url(self, info, action, *args):
        mode = action if action != 'change' else 'edit'
        return (self.view_controller
                if self.view_controller
                else self.controller).get_url(mode=mode)

    def render(self, name, value, *args, **kwargs):
        from django.contrib.admin.views.main import IS_POPUP_VAR, TO_FIELD_VAR
        rel_opts = self.rel.model._meta
        info = (rel_opts.app_label, rel_opts.model_name)
        self.widget.choices = self.choices
        url_params = '&'.join("%s=%s" % param for param in [
            (TO_FIELD_VAR, self.rel.get_related_field().name),
            (IS_POPUP_VAR, 1),
        ])
        context = {
            'widget': self.widget.render(name, value, *args, **kwargs),
            'name': name,
            'url_params': url_params,
            'model': rel_opts.verbose_name,
        }
        if self.can_change_related:
            change_related_template_url = self.get_related_url(info, 'change', '__fk__')
            context.update(
                can_change_related=True,
                change_related_template_url=change_related_template_url,
            )
        if self.can_add_related:
            add_related_url = self.get_related_url(info, 'add')
            context.update(
                can_add_related=True,
                add_related_url=add_related_url,
            )
        if self.can_delete_related:
            delete_related_template_url = self.get_related_url(info, 'delete', '__fk__')
            context.update(
                can_delete_related=True,
                delete_related_template_url=delete_related_template_url,
            )
        return mark_safe(render_to_string(self.template, context))

    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        self.attrs = self.widget.build_attrs(extra_attrs=None, **kwargs)
        return self.attrs

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)


class CurrencyInput(NumberInput):

    template_name = 'currency.html'
