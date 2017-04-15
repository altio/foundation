# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy

from collections import OrderedDict

from django.db import models
from django.core.exceptions import FieldError
from django.forms.widgets import CheckboxSelectMultiple, SelectMultiple
from django.utils.translation import string_concat, ugettext as _

from django import forms
from ....utils import flatten_fieldsets
from ...widgets import RelatedFieldWidgetWrapper

__all__ = ('BaseModelFormMixin', 'HORIZONTAL',
           'VERTICAL', 'FORMFIELD_FOR_DBFIELD_DEFAULTS')


HORIZONTAL, VERTICAL = 1, 2

FORMFIELD_FOR_DBFIELD_DEFAULTS = {
}

def get_ul_class(radio_style):
    return 'radiolist' if radio_style == VERTICAL else 'radiolist inline'


class BaseModelFormMixin(object):
    """
    Common base for ModelForm yielding views that does not make presumptions
    about downstream use in a single- or multiple-object context.
    Additionally, it will presume access to the view (controller) via self.view
    and access to the controller (registered) via self.controller.
    """

    def __init__(self, *args, **kwargs):
        super(BaseModelFormMixin, self).__init__(*args, **kwargs)
        # Merge FORMFIELD_FOR_DBFIELD_DEFAULTS with the formfield_overrides
        # rather than simply overwriting.
        overrides = copy.deepcopy(FORMFIELD_FOR_DBFIELD_DEFAULTS)
        for k, v in self.formfield_overrides.items():
            overrides.setdefault(k, {}).update(v)
        self.formfield_overrides = overrides

    def get_readonly_fields(self, mode, obj=None):
        """
        Hook for specifying custom readonly fields.
        """
        return self.readonly_fields

    def get_prepopulated_fields(self, mode, obj=None):
        """
        Hook for specifying custom prepopulated fields.
        """
        return self.prepopulated_fields

    def get_fields(self, mode, obj=None):
        """
        Return an appropriate fields whitelist for this controller.
        NOTE: There is a feedback loop with get_form here where when fields are
        missing on the controller it will go back to get_form with fields=None
        """

        # fields can be a mode:whitelist dictionary
        if isinstance(self.fields, dict):
            fields = self.fields.get(mode)
            if fields is None:
                if mode not in self.public_modes:
                    fields = self.fields.get('private')
                if fields is None:
                    fields = self.fields.get('public')
        else:
            fields = self.controller.fields

        return fields

    def get_fieldsets(self, mode, obj=None):
        """
        Hook for specifying fieldsets.
        called by get_form(set) to specified fieldsets, used by form(set) FACTORY
        """
        # fieldsets can be a mode:fieldsets dictionary
        if isinstance(self.fieldsets, dict):
            fieldsets = self.fieldsets.get(mode)
            if fieldsets is None:
                if mode not in self.public_modes:
                    fieldsets = self.fieldsets.get('private')
                if fieldsets is None:
                    fieldsets = self.fieldsets.get('public')
        else:
            fieldsets = self.fieldsets

        # fallback make a fieldset from the whitelist
        if not fieldsets:
            fields = self.get_fields(mode=mode, obj=obj)
            # flatten_fieldsets needs an iterable even if  __all__ or None
            fields = fields if hasattr(fields, '__iter__') else [fields]
            fieldsets = [
                ('_fields', {'name': None, 'fields': fields or ()}),
            ]
        return fieldsets

    def get_form_class_kwargs(self, modelform_class, obj=None, **kwargs):
        """
        Returns the (default) kwargs needed to generate the form(set) class via
        a factory.
        """

        # if fields passed as kwarg (even if None), proceed with that as basis
        # otherwise, flatten get_fieldsets which will call get_form_class_kwargs
        # again with fields=None
        fields = (kwargs.pop('fields', None)
                  if 'fields' in kwargs
                  else flatten_fieldsets(self.get_fieldsets(self.view.mode, obj)))

        # it is important to note that there are two "readonly_fields" concepts:
        # 1. the readonly_fields on the controller itself, which persist down to
        #    the view, and;
        # 2. the extra readonly_fields accumulated here and then excluded from
        #    form construction
        exclude = [] if self.exclude is None else list(self.exclude)
        readonly_fields = list(self.get_readonly_fields(obj))

        # had to put '__all__' in a list for it to pass through flatten...
        if len(fields) == 1 and fields[0] in (None, forms.ALL_FIELDS):
            fields = fields[0]
        # otherwise prune attributes, callables, and related object accessors
        else:
            model_fields = tuple(
                field.name for field in self.model._meta.get_fields()
                if not (field.is_relation and (
                    (field.many_to_one and not field.related_model)
                    or field.one_to_many or field.one_to_one
                ))
            )

            # work backwards through field list, pruning readonly fields
            for i in reversed(range(len(fields))):
                if fields[i] not in model_fields:
                    if fields[i] not in readonly_fields:
                        readonly_fields.append(fields[i])
                    del fields[i]
        exclude.extend(readonly_fields)

        # formset_form exists in both model types
        if self.exclude is None and hasattr(modelform_class, '_meta') \
                and modelform_class._meta.exclude:
            # Take the custom ModelForm's Meta.exclude into account only if the
            # InlineModelAdmin doesn't define its own.
            exclude.extend(modelform_class._meta.exclude)
        # If exclude is an empty list we use None, since that's the actual
        # default.
        exclude = exclude or None

        # Remove declared form fields which are in readonly_fields.
        new_attrs = OrderedDict(
            (f, None) for f in readonly_fields
            if f in modelform_class.declared_fields
        )
        modelform_class = type(modelform_class.__name__, (modelform_class,), new_attrs)

        # satisfy the modelform_factory
        defaults = {
            "form": modelform_class,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": self.formfield_for_dbfield,
        }
        defaults.update(kwargs)
        return defaults

    def get_form_class(self, obj=None, modelform_class=None, **kwargs):
        """
        Returns a Form class for use in the add/edit views.
        """
        # form will have been passed by an upstream call to get_formset_class
        # so if it is missing, this must be a single-object view on a non-inline
        # controller
        if modelform_class is None:
            modelform_class = self.modelform_class
        form_class_kwargs = self.get_form_class_kwargs(
            modelform_class=modelform_class, obj=obj, **kwargs)

        try:
            ModelForm = forms.modelform_factory(self.model, **form_class_kwargs)
        except FieldError as e:
            raise FieldError(
                '%s. Check fields/fieldsets/exclude attributes of class %s.'
                % (e, self.__class__.__name__)
            )
        return ModelForm

    def get_form_kwargs(self):
        kwargs = super(BaseModelFormMixin, self).get_form_kwargs()
        obj = kwargs.get('instance')
        kwargs['fieldsets'] = self.get_fieldsets(self.mode)
        kwargs['prepopulated_fields'] = self.get_prepopulated_fields(self.mode, obj=obj)
        kwargs['readonly_fields'] = self.get_readonly_fields(self.mode, obj=obj)
        kwargs['view_controller'] = self
        return kwargs

    def save_form(self, change):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        return self.form.save(commit=False)

    def save_model(self, change):
        """
        Given a model instance save it to the database.
        """
        self.object.save()

    def delete_model(self, obj):
        """
        Given a model instance delete it from the database.
        """
        obj.delete()

    def save_formset(self, formset, change):
        """
        Given an inline formset save it to the database.
        """
        formset.save()

    def save_related(self, change):
        """
        Given the ``HttpRequest``, the parent ``ModelForm`` instance, the
        list of inline formsets and a boolean value based on whether the
        parent is being added or changed, save the related objects to the
        database. Note that at this point save_form() and save_model() have
        already been called.
        """
        self.form.save_m2m()
        for inline_formset in self.inline_formsets.values():
            self.save_formset(inline_formset, change=change)

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Hook for specifying the form Field instance for a given database Field
        instance.

        If kwargs are given, they're passed to the form Field's constructor.
        """
        # If the field specifies choices, we don't need to look for special
        # admin widgets - we just need to use a select widget of some kind.
        if db_field.choices:
            return self.formfield_for_choice_field(db_field, **kwargs)

        # ForeignKey or ManyToManyFields
        if isinstance(db_field, models.ManyToManyField) or isinstance(db_field, models.ForeignKey):
            # Combine the field kwargs with any options for formfield_overrides.
            # Make sure the passed in **kwargs override anything in
            # formfield_overrides because **kwargs is more specific, and should
            # always win.
            if db_field.__class__ in self.formfield_overrides:
                kwargs = dict(self.formfield_overrides[db_field.__class__], **kwargs)

            # Get the correct formfield.
            if isinstance(db_field, models.ForeignKey):
                formfield = self.formfield_for_foreignkey(db_field, **kwargs)
            elif isinstance(db_field, models.ManyToManyField):
                formfield = self.formfield_for_manytomany(db_field, **kwargs)

            # For non-raw_id fields, wrap the widget with a wrapper that adds
            # extra HTML -- the "add other" interface -- to the end of the
            # rendered output. formfield can be None if it came from a
            # OneToOneField with parent_link=True or a M2M intermediary.
            if formfield and db_field.name not in self.raw_id_fields:
                related_model = db_field.remote_field.model
                related_controller = self.view.get_related_controller(related_model)
                wrapper_kwargs = {}
                # if related_controller:
                #     wrapper_kwargs.update(
                #         can_add_related=related_controller.has_permission('add'),
                #         can_change_related=related_controller.has_permission('change'),
                #         can_delete_related=related_controller.has_permission('delete'),
                #     )
                formfield.widget = RelatedFieldWidgetWrapper(
                    formfield.widget, db_field.remote_field, related_controller, **wrapper_kwargs
                )

            return formfield

        # If we've got overrides for the formfield defined, use 'em. **kwargs
        # passed to formfield_for_dbfield override the defaults.
        for klass in db_field.__class__.mro():
            if klass in self.formfield_overrides:
                kwargs = dict(copy.deepcopy(self.formfield_overrides[klass]), **kwargs)
                return db_field.formfield(**kwargs)

        # For any other type of field, just call its formfield() method.
        return db_field.formfield(**kwargs)

    def formfield_for_choice_field(self, db_field, **kwargs):
        """
        Get a form Field for a database Field that has declared choices.
        """
        from django.contrib.admin import widgets

        # If the field is named as a radio_field, use a RadioSelect
        if db_field.name in self.radio_fields:
            # Avoid stomping on custom widget/choices arguments.
            if 'widget' not in kwargs:
                kwargs['widget'] = widgets.AdminRadioSelect(attrs={
                    'class': get_ul_class(self.radio_fields[db_field.name]),
                })
            if 'choices' not in kwargs:
                kwargs['choices'] = db_field.get_choices(
                    include_blank=db_field.blank,
                    blank_choice=[('', _('None'))]
                )
        return db_field.formfield(**kwargs)

    def get_field_queryset(self, db, db_field):
        """
        If the ModelAdmin specifies ordering, the queryset should respect that
        ordering.  Otherwise don't specify the queryset, let the field decide
        (returns None in that case).
        """
        related_model = db_field.remote_field.model
        related_controller = self.view.get_related_controller(related_model)
        if related_controller is not None:
            ordering = related_controller.get_ordering()
            if ordering is not None and ordering != ():
                return db_field.remote_field.model._default_manager.using(db).order_by(*ordering)
        return None

    def formfield_for_foreignkey(self, db_field, **kwargs):
        """
        Get a form Field for a ForeignKey.
        """
        from django.contrib.admin import widgets

        db = kwargs.get('using')
        if db_field.name in self.raw_id_fields:
            kwargs['widget'] = widgets.ForeignKeyRawIdWidget(db_field.remote_field, self.admin_site, using=db)
        elif db_field.name in self.radio_fields:
            kwargs['widget'] = widgets.AdminRadioSelect(attrs={
                'class': get_ul_class(self.radio_fields[db_field.name]),
            })
            kwargs['empty_label'] = _('None') if db_field.blank else None

        if 'queryset' not in kwargs:
            queryset = self.get_field_queryset(db, db_field)
            if queryset is not None:
                kwargs['queryset'] = queryset

        return db_field.formfield(**kwargs)

    def formfield_for_manytomany(self, db_field, **kwargs):
        """
        Get a form Field for a ManyToManyField.
        """
        # If it uses an intermediary model that isn't auto created, don't show
        # a field in admin.
        from django.contrib.admin import widgets

        if not db_field.remote_field.through._meta.auto_created:
            return None
        db = kwargs.get('using')

        if db_field.name in self.raw_id_fields:
            kwargs['widget'] = widgets.ManyToManyRawIdWidget(db_field.remote_field, self.admin_site, using=db)
        elif db_field.name in (list(self.filter_vertical) + list(self.filter_horizontal)):
            kwargs['widget'] = widgets.FilteredSelectMultiple(
                db_field.verbose_name,
                db_field.name in self.filter_vertical
            )

        if 'queryset' not in kwargs:
            queryset = self.get_field_queryset(db, db_field)
            if queryset is not None:
                kwargs['queryset'] = queryset

        form_field = db_field.formfield(**kwargs)
        if isinstance(form_field.widget, SelectMultiple) and not isinstance(form_field.widget, CheckboxSelectMultiple):
            msg = _('Hold down "Control", or "Command" on a Mac, to select more than one.')
            help_text = form_field.help_text
            form_field.help_text = string_concat(help_text, ' ', msg) if help_text else msg
        return form_field
