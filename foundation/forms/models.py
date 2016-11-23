# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import router
from django.db.models import ManyToOneRel
from django.forms import models
from django.forms.formsets import DELETION_FIELD_NAME, ORDERING_FIELD_NAME
from django.template.defaultfilters import capfirst
from django.urls import reverse
from django.utils.text import get_text_list
from django.utils.translation import ugettext

from ..utils import label_for_field, help_text_for_field, quote, NestedObjects
from .forms import BackendFormMixin


__all__ = ('ModelForm', 'FormSetModelForm', 'BaseModelFormSet',
           'BaseInlineFormSet', 'IS_POPUP_VAR', 'TO_FIELD_VAR')


# Changelist settings
ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
SEARCH_VAR = 'q'
ERROR_FLAG = 'e'

IS_POPUP_VAR = '_popup'
TO_FIELD_VAR = '_to_field'

IGNORED_PARAMS = (
    ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, TO_FIELD_VAR)


class ModelForm(BackendFormMixin, models.ModelForm):
    """ ModelForm with a Controller and Fieldsets """


class FormSetModelForm(ModelForm):
    """
    A ModelForm for use by FormSets with awareness of the generating Formset.
    """
    def __init__(self, formset, fieldsets, prepopulated_fields, instance=None,
                 readonly_fields=None, **kwargs):
        self.formset = formset

        # The BaseModelForm will guarantee an "instance," which will either be
        # the original or a new object.  We want something that only represents
        # the original, if provided.
        self.original = instance

        self.show_url = True  # original and view_on_site_url is not None
        # self.absolute_url = view_on_site_url
        super(FormSetModelForm, self).__init__(
            fieldsets, prepopulated_fields, readonly_fields, instance=instance, **kwargs)

    def needs_explicit_pk_field(self):
        # Auto fields are editable (oddly), so need to check for auto or non-editable pk
        if self._meta.model._meta.has_auto_field or not self._meta.model._meta.pk.editable:
            return True
        # Also search any parents for an auto field. (The pk info is propagated to child
        # models so that does not need to be checked in parents.)
        for parent in self._meta.model._meta.get_parent_list():
            if parent._meta.has_auto_field:
                return True
        return False

    def pk_field(self):
        field = self[self.formset._pk_field.name]
        field.is_first = False
        return field

    def fk_field(self):
        fk = getattr(self.formset, "fk", None)
        if fk:
            field = self[fk.name]
            field.is_first = False
            return field
        else:
            return ""

    def deletion_field(self):
        field = self[DELETION_FIELD_NAME]
        field.is_first = False
        return field

    def ordering_field(self):
        field = self[ORDERING_FIELD_NAME]
        field.is_first = False
        return field

    # SOURCE: get_formset_class class DeleteProtectedModelForm
    def hand_clean_DELETE(self):
        """
        We don't validate the 'DELETE' field itself because on
        templates it's not rendered using the field information, but
        just using a generic "deletion_field" of the InlineModelAdmin.
        """
        if self.cleaned_data.get(DELETION_FIELD_NAME, False):
            using = router.db_for_write(self._meta.model)
            collector = NestedObjects(using=using)
            if self.instance.pk is None:
                return
            collector.collect([self.instance])
            if collector.protected:
                objs = []
                for p in collector.protected:
                    objs.append(
                        # Translators: Model verbose name and instance representation,
                        # suitable to be an item in a list.
                        _('%(class_name)s %(instance)s') % {
                            'class_name': p._meta.verbose_name,
                            'instance': p}
                    )
                params = {'class_name': self._meta.model._meta.verbose_name,
                          'instance': self.instance,
                          'related_objects': get_text_list(objs, _('and'))}
                msg = _("Deleting %(class_name)s %(instance)s would require "
                        "deleting the following protected related objects: "
                        "%(related_objects)s")
                raise ValidationError(msg, code='deleting_protected', params=params)

    def is_valid(self):
        result = super(FormSetModelForm, self).is_valid()
        self.hand_clean_DELETE()
        return result


class BackendFormSetMixin(object):
    """
    We will also need to extend our FormSets to provide those Forms the extra
    love they need now.
    """

    def __init__(self, fieldsets, prepopulated_fields=None,
                 readonly_fields=None, view=None, is_readonly=False,
                 **kwargs):
        super(BackendFormSetMixin, self).__init__(**kwargs)
        # they chose to trojan the controller in lieu of model._meta
        self.opts = view
        self.fieldsets = fieldsets
        self.is_readonly = is_readonly
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields
        if prepopulated_fields is None:
            prepopulated_fields = {}
        self.prepopulated_fields = prepopulated_fields
        self.classes = ' '.join(view.classes) if view.classes else ''

    def get_form_kwargs(self, index):
        # satisfy extra kwargs needed by FieldsetForm
        kwargs = super(BackendFormSetMixin, self).get_form_kwargs(index)
        kwargs.update(formset=self, fieldsets=self.fieldsets,
                      prepopulated_fields=self.prepopulated_fields,
                      readonly_fields=self.readonly_fields,
                      view=self.opts)
        return kwargs

    def fields(self):
        for field_name in self.form.base_fields:
            if field_name in self.readonly_fields:
                yield {
                    'name': field_name,
                    'label': label_for_field(field_name, self.opts.model, self.opts),
                    'widget': {'is_hidden': False},
                    'required': False,
                    'help_text': help_text_for_field(field_name, self.opts.model),
                }
            else:
                form_field = self.empty_form.fields[field_name]
                label = form_field.label
                if label is None:
                    label = label_for_field(field_name, self.opts.model, self.opts)
                yield {
                    'name': field_name,
                    'label': label,
                    'widget': form_field.widget,
                    'required': form_field.required,
                    'help_text': form_field.help_text,
                }

    @property
    def media(self):
        # get the media for the controller and the formset('s form)
        media = self.opts.media + super(BackendFormSetMixin, self).media
        for fs in self:
            media = media + fs.media
        return media


class BaseModelFormSet(BackendFormSetMixin, models.BaseModelFormSet):
    """
    An extension of the formset that provides fieldsets and table construction
    with ability to edit specified fields.
    ADMIN SOURCE: ChangeList
    """

    def apply_select_related(self, qs):
        if self.list_select_related is True:
            return qs.select_related()

        if self.list_select_related is False:
            if self.has_related_field_in_list_display():
                return qs.select_related()

        if self.list_select_related:
            return qs.select_related(*self.list_select_related)
        return qs

    def has_related_field_in_list_display(self):
        for field_name in self.list_display:
            try:
                field = self.opts.get_field(field_name)
            except FieldDoesNotExist:
                pass
            else:
                if isinstance(field.remote_field, ManyToOneRel):
                    return True
        return False

    def url_for_result(self, result):
        pk = getattr(result, self.pk_attname)
        return reverse('admin:%s_%s_change' % (self.opts.app_label,
                                               self.opts.model_name),
                       args=(quote(pk),),
                       current_app=self.opts.site.name)


class BaseInlineFormSet(BackendFormSetMixin, models.BaseInlineFormSet):
    """
    A wrapper around an inline formset that carries the associated inline
    controller around and provides other help.
    """

    def fields(self):
        fk = getattr(self, "fk", None)
        for field in super(BaseInlineFormSet, self).fields():
            if fk and fk.name == field['name']:
                continue
            yield field

    def inline_formset_data(self):
        verbose_name = self.opts.verbose_name
        return json.dumps({
            'name': '#%s' % self.prefix,
            'options': {
                'prefix': self.prefix,
                'addText': ugettext('Add another %(verbose_name)s') % {
                    'verbose_name': capfirst(verbose_name),
                },
                'deleteText': ugettext('Remove'),
            }
        })
