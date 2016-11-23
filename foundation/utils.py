from __future__ import unicode_literals

import datetime
import decimal
from collections import defaultdict

from django.apps import apps
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.deletion import Collector
from django.forms.utils import pretty_name
from django.utils import formats, six, timezone
from django.utils.encoding import force_str, force_text, smart_text
from django.utils.html import format_html
from django.utils.text import capfirst
from django.urls.base import reverse
from django.urls.exceptions import NoReverseMatch


def get_content_type_for_model(obj):
    # Since this module gets imported in the application's root package,
    # it cannot import models from other applications at the module level.
    from django.contrib.contenttypes.models import ContentType
    return ContentType.objects.get_for_model(obj, for_concrete_model=False)


def get_eligible_models(app_config):
    for model in app_config.get_models():
        if issubclass(model, models.Model):  # TODO: and model is_eligible
            yield model


def get_project_app_configs():
    for project_app in settings.PROJECT_APPS:
        app_config = apps.get_app_config(project_app.split('.')[-1])
        if list(get_eligible_models(app_config)):
            yield app_config


def quote(s):
    """
    Ensure that primary key values do not confuse the admin URLs by escaping
    any '/', '_' and ':' and similarly problematic characters.
    Similar to urllib.quote, except that the quoting is slightly different so
    that it doesn't get automatically unquoted by the Web browser.
    """
    if not isinstance(s, six.string_types):
        return s
    res = list(s)
    for i in range(len(res)):
        c = res[i]
        if c in """:/_#?;@&=+$,"[]<>%\n\\""":
            res[i] = '_%02X' % ord(c)
    return ''.join(res)


def unquote(s):
    """
    Undo the effects of quote(). Based heavily on urllib.unquote().
    """
    mychr = chr
    myatoi = int
    list = s.split('_')
    res = [list[0]]
    myappend = res.append
    del list[0]
    for item in list:
        if item[1:2]:
            try:
                myappend(mychr(myatoi(item[:2], 16)) + item[2:])
            except ValueError:
                myappend('_' + item)
        else:
            myappend('_' + item)
    return "".join(res)


def flatten(fields):
    """Returns a list which is a single level of flattening of the
    original list."""
    flat = []
    for field in fields:
        if isinstance(field, (list, tuple)):
            flat.extend(field)
        else:
            flat.append(field)
    return flat


def flatten_fieldsets(fieldsets):
    """Returns a list of field names from an admin fieldsets structure."""
    field_names = []
    for name, opts in fieldsets:
        field_names.extend(
            flatten(opts['fields'])
        )
    return field_names


class NestedObjects(Collector):
    def __init__(self, *args, **kwargs):
        super(NestedObjects, self).__init__(*args, **kwargs)
        self.edges = {}  # {from_instance: [to_instances]}
        self.protected = set()
        self.model_objs = defaultdict(set)

    def add_edge(self, source, target):
        self.edges.setdefault(source, []).append(target)

    def collect(self, objs, source=None, source_attr=None, **kwargs):
        for obj in objs:
            if source_attr and not source_attr.endswith('+'):
                related_name = source_attr % {
                    'class': source._meta.model_name,
                    'app_label': source._meta.app_label,
                }
                self.add_edge(getattr(obj, related_name), obj)
            else:
                self.add_edge(None, obj)
            self.model_objs[obj._meta.model].add(obj)
        try:
            return super(NestedObjects, self).collect(objs, source_attr=source_attr, **kwargs)
        except models.ProtectedError as e:
            self.protected.update(e.protected_objects)

    def related_objects(self, related, objs):
        qs = super(NestedObjects, self).related_objects(related, objs)
        return qs.select_related(related.field.name)

    def _nested(self, obj, seen, format_callback):
        if obj in seen:
            return []
        seen.add(obj)
        children = []
        for child in self.edges.get(obj, ()):
            children.extend(self._nested(child, seen, format_callback))
        if format_callback:
            ret = [format_callback(obj)]
        else:
            ret = [obj]
        if children:
            ret.append(children)
        return ret

    def nested(self, format_callback=None):
        """
        Return the graph as a nested list.
        """
        seen = set()
        roots = []
        for root in self.edges.get(None, ()):
            roots.extend(self._nested(root, seen, format_callback))
        return roots

    def can_fast_delete(self, *args, **kwargs):
        """
        We always want to load the objects into memory so that we can display
        them to the user in confirm page.
        """
        return False


def get_deleted_objects(objs, opts, user, backend, using):
    """
    Find all objects related to ``objs`` that should also be deleted. ``objs``
    must be a homogeneous iterable of objects (e.g. a QuerySet).

    Returns a nested list of strings suitable for display in the
    template with the ``unordered_list`` filter.
    """
    collector = NestedObjects(using=using)
    collector.collect(objs)
    perms_needed = set()

    def format_callback(obj):
        has_admin = obj.__class__ in backend._registry
        opts = obj._meta

        no_edit_link = '%s: %s' % (capfirst(opts.verbose_name),
                                   force_text(obj))

        if has_admin:
            try:
                admin_url = reverse('%s:%s:edit'
                                    % (opts.app_label,
                                       opts.model_name),
                                    None, (quote(obj._get_pk_val()),))
            except NoReverseMatch:
                # Change url doesn't exist -- don't display link to edit
                return no_edit_link

            p = '%s:%s:delete' % (opts.app_label, opts.model_name)
            if not user.has_perm(p):
                perms_needed.add(opts.verbose_name)
            # Display a link to the admin page.
            return format_html('{}: <a href="{}">{}</a>',
                               capfirst(opts.verbose_name),
                               admin_url,
                               obj)
        else:
            # Don't display link to edit, because it either has no
            # admin or is edited inline.
            return no_edit_link

    to_delete = collector.nested(format_callback)

    protected = [format_callback(obj) for obj in collector.protected]
    model_count = {model._meta.verbose_name_plural: len(objs) for model, objs in collector.model_objs.items()}

    return to_delete, model_count, perms_needed, protected


def _get_non_gfk_field(opts, name):
    """
    For historical reasons, the admin app relies on GenericForeignKeys as being
    "not found" by get_field(). This could likely be cleaned up.

    Reverse relations should also be excluded as these aren't attributes of the
    model (rather something like `foo_set`).
    """
    field = opts.get_field(name)
    if (field.is_relation and
            # Generic foreign keys OR reverse relations
            ((field.many_to_one and not field.related_model) or field.one_to_many)):
        raise FieldDoesNotExist()
    return field


def lookup_field(name, obj, controller=None):
    opts = obj._meta
    try:
        f = _get_non_gfk_field(opts, name)
    except FieldDoesNotExist:
        # For non-field values, the value is either a method, property or
        # returned via a callable.
        if callable(name):
            attr = name
            value = attr(obj)
        elif (controller is not None and
                hasattr(controller, name) and
                not name == '__str__' and
                not name == '__unicode__'):
            attr = getattr(controller, name)
            value = attr(obj)
        else:
            attr = getattr(obj, name)
            if callable(attr):
                value = attr()
            else:
                value = attr
        f = None
    else:
        attr = None
        value = getattr(obj, name)
    return f, attr, value


def label_for_field(name, model, model_admin=None, return_attr=False):
    """
    Returns a sensible label for a field name. The name can be a callable,
    property (but not created with @property decorator) or the name of an
    object's attribute, as well as a genuine fields. If return_attr is
    True, the resolved attribute (which could be a callable) is also returned.
    This will be None if (and only if) the name refers to a field.
    """
    attr = None
    try:
        field = _get_non_gfk_field(model._meta, name)
        try:
            label = field.verbose_name
        except AttributeError:
            # field is likely a ForeignObjectRel
            label = field.related_model._meta.verbose_name
    except FieldDoesNotExist:
        if name == "__unicode__":
            label = force_text(model._meta.verbose_name)
            attr = six.text_type
        elif name == "__str__":
            label = force_str(model._meta.verbose_name)
            attr = bytes
        else:
            if callable(name):
                attr = name
            elif model_admin is not None and hasattr(model_admin, name):
                attr = getattr(model_admin, name)
            elif hasattr(model, name):
                attr = getattr(model, name)
            else:
                message = "Unable to lookup '%s' on %s" % (name, model._meta.object_name)
                if model_admin:
                    message += " or %s" % (model_admin.__class__.__name__,)
                raise AttributeError(message)

            if hasattr(attr, "short_description"):
                label = attr.short_description
            elif (isinstance(attr, property) and
                  hasattr(attr, "fget") and
                  hasattr(attr.fget, "short_description")):
                label = attr.fget.short_description
            elif callable(attr):
                if attr.__name__ == "<lambda>":
                    label = "--"
                else:
                    label = pretty_name(attr.__name__)
            else:
                label = pretty_name(name)
    if return_attr:
        return (label, attr)
    else:
        return label


def help_text_for_field(name, model):
    help_text = ""
    try:
        field = _get_non_gfk_field(model._meta, name)
    except FieldDoesNotExist:
        pass
    else:
        if hasattr(field, 'help_text'):
            help_text = field.help_text
    return smart_text(help_text)


def display_for_value(value, empty_value_display, boolean=False):
    from django.contrib.admin.templatetags.admin_list import _boolean_icon

    if boolean:
        return _boolean_icon(value)
    elif value is None:
        return empty_value_display
    elif isinstance(value, datetime.datetime):
        return formats.localize(timezone.template_localtime(value))
    elif isinstance(value, (datetime.date, datetime.time)):
        return formats.localize(value)
    elif isinstance(value, six.integer_types + (decimal.Decimal, float)):
        return formats.number_format(value)
    elif isinstance(value, (list, tuple)):
        return ', '.join(force_text(v) for v in value)
    else:
        return smart_text(value)


def display_for_field(value, field, empty_value_display):
    from django.contrib.admin.templatetags.admin_list import _boolean_icon

    if getattr(field, 'flatchoices', None):
        return dict(field.flatchoices).get(value, empty_value_display)
    # NullBooleanField needs special-case null-handling, so it comes
    # before the general null test.
    elif isinstance(field, models.BooleanField) or isinstance(field, models.NullBooleanField):
        return _boolean_icon(value)
    elif value is None:
        return empty_value_display
    elif isinstance(field, models.DateTimeField):
        return formats.localize(timezone.template_localtime(value))
    elif isinstance(field, (models.DateField, models.TimeField)):
        return formats.localize(value)
    elif isinstance(field, models.DecimalField):
        return formats.number_format(value, field.decimal_places)
    elif isinstance(field, (models.IntegerField, models.FloatField)):
        return formats.number_format(value)
    elif isinstance(field, models.FileField) and value:
        return format_html('<a href="{}">{}</a>', value.url, value)
    else:
        return display_for_value(value, empty_value_display)
