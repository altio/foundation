# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms.models import _get_foreign_key
from django.shortcuts import resolve_url
from django.utils.translation import ugettext_lazy as _

from ..forms import IS_POPUP_VAR, TO_FIELD_VAR
from ..template.response import TemplateResponse
from ..utils import flatten_fieldsets
from .controllers import BaseViewController


class ControllerMixin(BaseViewController, AppAccessMixin, BackendMixin):

    def get_context_data(self, **kwargs):
        opts = self.model._meta
        app_label = opts.app_label
        model_name = opts.model_name

        kwargs.update({
            'mode': self.mode,
            'opts': opts,
            'has_add_permission': self.has_add_permission(),
            'has_change_permission': self.has_edit_permission(),
            'has_delete_permission': self.has_delete_permission(),
            'to_field_var': TO_FIELD_VAR,
            'is_popup_var': IS_POPUP_VAR,
            'app_label': app_label,
            'model_name': model_name,
            'title': _(self.mode_title),
            # 'to_field': to_field,
            # errors=helpers.AdminErrorList(form, formsets),
            # preserved_filters=self.get_preserved_filters(request),
            'is_popup': (IS_POPUP_VAR in self.request.POST or
                         IS_POPUP_VAR in self.request.GET)

        })

        return super(ControllerMixin, self).get_context_data(**kwargs)

    def get_formsets_with_inlines(self, obj=None):
        """
        Yields tuples of FormSet class and InlineController instances.
        """
        for child in self.children.values():
            yield child.get_formset_class(obj), child

    def get_inline_formsets(self, obj, change):
        "Helper function to generate InlineFormSets for add/change_view."
        inline_formsets = []
        obj = obj if change else None
        fields = flatten_fieldsets(self.get_fieldsets(self.mode))
        for InlineFormSet, inline in self.get_formsets_with_inlines(obj):
            inline_fk_field = _get_foreign_key(
                self.model, inline.model, inline.fk_name)
            if inline_fk_field.remote_field.name not in fields:
                continue
            formset_kwargs = inline.get_formset_kwargs(
                formset_class=InlineFormSet, obj=obj)
            inline_formsets.append(InlineFormSet(**formset_kwargs))
        return inline_formsets

    def get_title(self):
        if self.mode == 'list':
            return _('all {}'.format(self.controller.opts.verbose_name_plural))
        else:
            obj = getattr(self, 'object', None)
            return ('{} {}'.format(title(self.mode_title), obj)
                if obj
                else title('{} {}'.format(self.mode_title, self.controller.opts.verbose_name)))

    def get_breadcrumbs(self):

        # start with the app index up top
        breadcrumbs = [(self.app_label,
                        resolve_url('{}:index'.format(self.app_label)))]

        if self.accessed_by_parent:
            parent_crumbs = []
            for parent in self.parents:
                parent_crumbs.append(parent.get_breadcrumb('view'))
                if parent.controller.is_local_root:
                    parent_crumbs.append(parent.get_breadcrumb('list'))
                    break
            breadcrumbs.extend(reversed(parent_crumbs))

        # always add the current view's list if we are not in list mode
        if self.mode != 'list':
            breadcrumbs.append(self.get_breadcrumb('list'))

        breadcrumbs.append(self.get_breadcrumb(self.mode))

        return breadcrumbs
