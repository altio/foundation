# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import router
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.generic import edit

from ... import forms
from ...utils import get_deleted_objects

from ...backend import views
from .base import FormControllerViewMixin
from .components import BaseModelFormMixin


__all__ = 'AddView', 'EditView', 'DisplayView', 'DeleteView'


class ObjectMixin(views.ObjectMixin):

    def get_success_url(self):
        return self.get_url('list')


class DeleteView(ObjectMixin, views.BackendTemplateMixin, edit.BaseDeleteView):

    mode = 'delete'
    mode_title = 'delete'
    template_name = 'delete.html'

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


class ProcessFormView(BaseModelFormMixin, ObjectMixin, FormControllerViewMixin,
                      edit.ModelFormMixin, edit.ProcessFormView):
    """ Single-Object ModelForm View Mixin """

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

    def get_media(self):
        media = super(ProcessFormView, self).get_media()
        media += self.form.media
        for inline_formset in self.inline_formsets:
            media += inline_formset.media
        return media

    def get_context_data(self, **kwargs):
        # from render_change_form
        request = self.request
        opts = self.model._meta

        # from changeform_view
        object_id = None
        if hasattr(self.object, 'pk') and '_saveasnew' not in request.POST:
            object_id = self.object.pk
        add = object_id is None

        kwargs.update({
            'opts': opts,
            'form': self.form,
            'object_id': object_id,
            'inline_formsets': self.inline_formsets,
        })

        return super(ProcessFormView, self).get_context_data(**kwargs)


class AddView(ProcessFormView):

    mode = 'add'
    mode_title = 'add a'
    template_name = 'add.html'


class EditView(ProcessFormView):

    mode = 'edit'
    mode_title = 'Editing'
    template_name = 'edit.html'


class DisplayView(ProcessFormView):

    mode = 'display'
    mode_title = ''
    template_name = 'display.html'
