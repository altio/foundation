# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError, FieldError

from .accessor import QueryMixin

__all__ = 'SingleObjectMixin', 'MultipleObjectMixin'


class SingleObjectMixin(QueryMixin):

    def get_object(self, queryset=None):

        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        model = queryset.model

        object_id = self.view.kwargs.get(self.model_lookup)

        obj = None
        if object_id:
            # TODO: lean on configurable pk/slug_field
            # TODO: add a build-time error if controller patterns yield slug
            # uniqueness constraints that differ from model contraints.
            # i.e. post has a slug, post is subordinated to blog and to user,
            # e.g. /tom/blogs/food/posts/apples and /tom/posts/apples
            # ergo post must have (owner, slug) and (blog, slug)
            field_name = 'pk' if object_id.isdigit() else 'slug'
            try:
                obj = queryset.get(**{field_name: object_id})
            except (model.DoesNotExist, ValidationError, ValueError, FieldError):
                obj = None

        return obj


class MultipleObjectMixin(QueryMixin):

    def get_ordering(self):
        """ MultipleObjectMixin actually enforces ordering. """
        return self.ordering
