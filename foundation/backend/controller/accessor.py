# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.forms.models import _get_foreign_key
from django.utils import six
from django.utils.functional import cached_property

__all__ = 'ModelAccessor',


class ModelAccessor(object):

    model = None

    def get_associated_queryset(self):
        """
        Should get the default manager's queryset and perform appropriate
        association with a (View)Controller.
        """
        raise NotImplementedError

    def get_ordering(self):
        """
        Ordering will always be attempted but will not be implemented until the
        it is in a multiple-object context.
        """
        return None

    def get_root_queryset(self):
        """
        Get a queryset for this Controller/View, applying ordering and injecting
        view/controller, as required.
        """

        queryset = self.get_associated_queryset()

        # we will always "attempt" ordering but it will not be implemented
        # for SingleObjectMixin
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset

    @cached_property
    def auth_model(self):
        return get_user_model()

    @cached_property
    def parent_model(self):
        parent = self.controller.parent
        return parent.model if parent else None

    @cached_property
    def fk(self):
        # if controller exists (not inline) and is root and no FK name spec'ed
        if (self.controller and self.controller.is_root) and not self.fk_name:
            raise ValueError('Must specify an "fk_name" for root Controllers '
                             'if you intend to lean on fk constraints.')
        return _get_foreign_key(self.parent_model, self.model, self.fk_name)

    @cached_property
    def auth_lookup(self):
        """ Returns the lookup for reducing the queryset. """
        auth_lookup = (
            self.fk_name
            if self.controller.is_root
            else (
                '__'.join([self.fk.name, self.view_parent.auth_lookup])
                if self.view_parent.auth_lookup
                else None
        ))
        return auth_lookup

    def is_auth_obj_permitted(self, auth_obj):
        """ Returns True if auth_obj is permitted to constrain. """
        return getattr(auth_obj, 'is_active', False)

    def get_auth_query(self, auth_obj):
        """
        Returns query for auth-reducing the queryset given an auth_obj.
        Fails safe: returning an empty dict means "nothing is permitted."
        """
        return (
            {self.auth_lookup: auth_obj}
            if self.auth_lookup and self.is_auth_obj_permitted(auth_obj)
            else {}
        )

    def get_auth_queryset(self, auth_obj):
        auth_query = self.get_auth_query(auth_obj)
        queryset = (
            self.get_root_queryset().filter(**auth_query)
            if auth_query
            else self.get_associated_queryset().none()
        )
        return queryset

    def get_queryset(self, auth_obj=None):
        """
        Returns an auth-constrainted queryset for this Model given its
        controller relationships.
        Passing an auth_obj of None will get the root queryset.
        """
        return (
            self.get_auth_queryset(auth_obj)
            if auth_obj
            else self.get_root_queryset()
        )
