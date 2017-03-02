# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .... import forms
from .form import BaseModelFormMixin
from .query import MultipleObjectMixin

__all__ = 'BaseFormSetMixin', 'InlineFormsetMixin'


class BaseFormSetMixin(BaseModelFormMixin):

    extra = 1
    min_num = None
    max_num = None
    formset_class = forms.BaseModelFormSet
    inlineformset_class = forms.BaseInlineFormSet
    modelform_class = forms.FormSetModelForm

    def get_extra(self, obj=None, **kwargs):
        """Hook for customizing the number of extra inline forms."""
        return self.extra

    def get_min_num(self, obj=None, **kwargs):
        """Hook for customizing the min number of inline forms."""
        return self.min_num

    def get_max_num(self, obj=None, **kwargs):
        """Hook for customizing the max number of extra inline forms."""
        return self.max_num

    def get_formset_class_kwargs(self, obj=None, **kwargs):
        # TODO: make common field getting logic work across form(set)s?
        # need fields=None in the event fields is missing to indicate "no call
        # to flatten get_fieldsets" which would recur
        # TODO: when a controller base class has fieldsets and it is concretely
        # inherited to make a second controller, the fieldsets are no longer
        # considered-- probably to do with options... FIXME
        FormsetForm = self.get_form_class(obj=obj, modelform_class=self.modelform_class)

        # can_delete = self.can_delete and self.has_delete_permission(request, obj)
        # as it stands, can_delete is a concept only for inline controllers
        # we expect the non-inline formsets to get checkboxes for actions etc.
        extra = self.view.edit and self.get_extra(self, **kwargs) or 0
        can_delete = self.view.mode == 'edit' and self.has_delete_permission()

        defaults = dict(
            form=FormsetForm,
            formset=self.inlineformset_class if obj else self.formset_class,
            extra=extra,
            min_num=self.get_min_num(obj=obj, **kwargs),
            max_num=self.get_max_num(obj=obj, **kwargs),
            can_delete=can_delete,
        )
        # if form is model-derived, tack those kwargs onto the formset kwargs
        form_options = FormsetForm._meta
        if hasattr(form_options, 'model'):
            defaults.update(
                model=form_options.model,
                fields=form_options.fields,
                exclude=form_options.exclude,
                formfield_callback=self.formfield_for_dbfield,
                #**self.get_form_class_kwargs(
                #    view, form=self.formset_form, fields=fields)
            )

        if obj:
            defaults.setdefault('parent_model', self.fk.related_model)
            defaults.setdefault('fk_name', self.fk.name)

        # override with kwargs passed in last
        defaults.update(**kwargs)
        return defaults

    def get_formset_class(self, obj=None, **kwargs):
        """
        SOURCE: options.get_changelist_form(set)
        Returns an (Inline)FormSet class, as appropriate, for use as an inline
        formset on a given page, or as the change list for a list view.
        :param obj: The obj under which the FormSet will inline itself, if
        applicable.
        """

        formset_factory = (forms.inlineformset_factory
                           if obj
                           else forms.modelformset_factory)

        formset_kwargs = self.get_formset_class_kwargs(obj=obj, **kwargs)
        FormSet = formset_factory(**formset_kwargs)
        return FormSet

    def get_formset_kwargs(self, formset_class, obj=None,
                           queryset=None, **kwargs):
        # TODO: Not sure what this was doing for get_inline_formsets
        # if prefixes[prefix] != 1 or not prefix:
        #     prefix = "%s-%s" % (prefix, prefixes[prefix])
        formset_params = {
            'prefix': formset_class.get_default_prefix(),
            # views normally groom the QS and pass it in but not inlines
            'queryset': queryset or self.get_queryset(),
            'view': self,
            'is_readonly': not self.view.edit,
            'fieldsets': list(self.get_fieldsets(mode=self.view.mode)),
            'readonly_fields': list(self.get_readonly_fields(mode=self.view.mode)),
            'prepopulated_fields': dict(self.get_prepopulated_fields(mode=self.view.mode)),
        }
        if obj:
            formset_params['instance'] = obj
        if self.view.request.method == 'POST':
            formset_params.update({
                'data': self.view.request.POST,
                'files': self.view.request.FILES,
                #'save_as_new': '_saveasnew' in self.view.request.POST
            })

        return formset_params

    def get_formset(self, obj=None, queryset=None, **kwargs):
        # SOURCE: get_changelist_formset

        # to avoid any excess "magic", we will assume this is the AUTHORITATIVE
        # place to pass a parent_obj in, which will in turn determine whether
        # to setup as an (inline)formset -- constraining to an FK is JIT and
        # must be treated differently than auth-constraining a QS at a general,
        # bar-to-entry level -- DO NOT TRY TO MIX THE CONCEPTS--IT ENDS POORLY!

        FormSet = self.get_formset_class(obj=obj, **kwargs)
        formset_kwargs = self.get_formset_kwargs(
            formset_class=FormSet, obj=obj, queryset=queryset, **kwargs)
        return FormSet(**formset_kwargs)


class InlineFormsetMixin(MultipleObjectMixin, BaseFormSetMixin):
    pass
