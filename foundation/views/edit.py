# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import router
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.generic import edit

from .. import forms
from ..utils import get_deleted_objects
from .base import ControllerMixin, LoginRequiredMixin
from .controllers.components import form, formset
from .detail import SingleObjectMixin
from .list import MultipleObjectMixin

__all__ = 'AddView', 'EditView', 'DisplayView', 'DeleteView'


class SingleObjectFormMixin(SingleObjectMixin, form.BaseModelFormMixin):
    """
    Mixes the view-and-controller aware SingleObjectMixin with the ModelForm
    Controller helpers.
    """


class MultipleObjectFormsetMixin(MultipleObjectMixin, formset.BaseFormSetMixin):
    """
    Mixes the view-and-controller aware MultipleObjectMixin with the FormSet
    Controller helpers.
    """


class ProcessFormView(ControllerMixin, edit.ProcessFormView):

    def handle_common(self, handler, request, *args, **kwargs):
        handler = super(ProcessFormView, self).handle_common(
            handler, request, *args, **kwargs)
        self.object = None if self.add else self.get_object()
        self.form = self.get_form()
        return handler

    def get(self, request, *args, **kwargs):
        self.inline_formsets = self.get_inline_formsets(
            self.object, change=not self.add
        )
        return super(ProcessFormView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.form.is_valid():
            form_validated = True
            new_object = self.save_form(change=not self.add)
        else:
            form_validated = False
            new_object = self.form.instance
        new_object._controller = self
        self.inline_formsets = self.get_inline_formsets(
            new_object, change=not self.add
        )
        # val all formsets *first* to ensure we report them when invalid
        if forms.all_valid(self.inline_formsets) and form_validated:
            self.object = new_object
            self.save_model(not self.add)
            self.save_related(not self.add)
            return self.form_valid(self.form)
        else:
            return self.form_invalid(self.form)


class BaseChangeFormView(SingleObjectFormMixin, ProcessFormView):

    template_name = 'change_form.html'

    def get_media(self):
        media = super(BaseChangeFormView, self).get_media()
        media += self.form.media
        for inline_formset in self.inline_formsets:
            media += inline_formset.media
        return media

    def get_context_data(self, **kwargs):
        # from render_change_form
        request = self.request
        opts = self.model._meta
        app_label = opts.app_label
        # preserved_filters = self.get_preserved_filters(request)
        # form_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, form_url)

        # from changeform_view
        object_id = None
        if hasattr(self.object, 'pk') and '_saveasnew' not in request.POST:
            object_id = self.object.pk
        add = object_id is None

        kwargs.update({
            'mode': self.mode,
            'has_add_permission': self.has_add_permission(),
            'has_change_permission': self.has_edit_permission(obj=self.object),
            'has_delete_permission': self.has_delete_permission(obj=self.object),
            # 'has_file_field': True,  # FIXME - this should check if form or formsets have a FileField,
            # 'form_url': form_url,
            'opts': opts,
            # 'content_type_id': get_content_type_for_model(self.model).pk,
            # 'save_as': self.save_as,
            # 'save_on_top': self.save_on_top,
            'to_field_var': forms.TO_FIELD_VAR,
            'is_popup_var': forms.IS_POPUP_VAR,
            'app_label': app_label,
            'title': _(self.mode_title),
            'form': self.form,
            'object_id': object_id,
            # is_popup=(IS_POPUP_VAR in request.POST or
            #           IS_POPUP_VAR in request.GET),
            # 'to_field': to_field,
            'inline_formsets': self.inline_formsets,
            # errors=helpers.AdminErrorList(form, formsets),
            # preserved_filters=self.get_preserved_filters(request),
        })

        return super(BaseChangeFormView, self).get_context_data(**kwargs)


class AddView(LoginRequiredMixin, BaseChangeFormView, edit.CreateView):

    mode = 'add'
    mode_title = 'add a'


class EditView(LoginRequiredMixin, BaseChangeFormView, edit.UpdateView):

    mode = 'edit'
    mode_title = 'Editing'


class DisplayView(BaseChangeFormView, edit.UpdateView):

    mode = 'view'
    mode_title = ''


class DeleteView(LoginRequiredMixin, SingleObjectMixin, edit.DeleteView):

    mode = 'delete'
    mode_title = 'delete'
    template_name = 'delete_confirmation.html'

    def get_context_data(self, **kwargs):
        object_name = force_text(self.object._meta.verbose_name)

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        (deleted_objects, model_count, perms_needed, protected) = get_deleted_objects(
            [self.object], self.object._meta, self.request.user,
            self.backend, router.db_for_write(self.model))

        kwargs.update(
            object_name=object_name,
            deleted_objects=deleted_objects,
            model_count=dict(model_count).items(),
        )
        return super(DeleteView, self).get_context_data(**kwargs)

    def get_success_url(self):
        return self.get_list_url()
