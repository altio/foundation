# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError, FieldError

__all__ = 'SingleObjectMixin', 'MultipleObjectMixin'


class SingleObjectMixin(object):

    def get_object(self, queryset=None):

        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        model = queryset.model

        object_id = self.view.kwargs.get(self.model_lookup)

        obj = None
        if object_id:
            field_name = 'pk' if object_id.isdigit() else 'slug'
            try:
                obj = queryset.get(**{field_name: object_id})
            except (model.DoesNotExist, ValidationError, ValueError, FieldError):
                obj = None

        return obj


class MultipleObjectMixin(object):

    def get_ordering(self):
        """ MultipleObjectMixin actually enforces ordering. """
        return self.ordering
