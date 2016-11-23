# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import six

from django.core.exceptions import ValidationError, ImproperlyConfigured,\
    FieldError
from django.forms.models import _get_foreign_key
from django.utils.functional import cached_property

__all__ = 'QueryMixin', 'SingleObjectMixin', 'MultipleObjectMixin'


class QueryMixin(object):

    # TODO: eventually we could consider putting the FK name on the URL path
    # and thus supporting multiple FK names for *query* purposes and then let
    # the single-object (in-focus) object discern which FK it is using
    # FOR NOW, let's maintain a single FK since that is more typical

    @cached_property
    def parent_model(self):
        parent = self.controller.parent
        return parent.model if parent else None

    @cached_property
    def fk(self):
        if self.controller.is_root and not self.fk_name:
            raise ValueError('Must specify an "fk_name" for root Controllers '
                             'if you intend to lean on fk constraints.')
        return _get_foreign_key(self.parent_model, self.model, self.fk_name)

    @cached_property
    def auth_query(self):
        """
        Combined with get_queryset, this is likely where your custom auth will
        inject itself to yield the desired access control.
        """

        # Controllers serving as local roots ought to have a path to User
        # directly or via their ancestry.  If the root Controller does not spec
        # an fk_name to a User field, it will be treated as "globally
        # accessible" from a QS perspective, and provide only list/display views

        if self.controller.is_root:
            return self.fk_name
        auth_query = self.controller.parent.auth_query
        if auth_query:
            auth_query = '__'.join([self.fk.name, auth_query])
        return auth_query

    def get_ordering(self):
        """ Override this to do something useful when it matters. """
        return None

    def get_queryset(self):
        """
        Get a queryset for this Controller/View, applying ordering and injecting
        view/controller, as required.
        """

        if self.model is not None:
            queryset = self.model._default_manager.get_queryset()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model or override "
                "%(cls)s.get_queryset()." % {
                    'cls': self.__class__.__name__
                }
            )

        # provide the QS a view and controllers
        queryset = queryset.attach(view=self.view, controller=self)

        # we will always "attempt" ordering but it will not be implemented
        # for SingleObjectMixin
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        """
        TODO: look into the intent of this
        if not qs.query.select_related:
            qs = self.apply_select_related(qs)

        """
        return queryset


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
