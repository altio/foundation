# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms.models import _get_foreign_key
from django.utils import six
from django.utils.functional import cached_property

__all__ = 'ModelAccessor',


class ModelAccessor(object):

    model = None

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

    def get_ordering(self):
        """
        Ordering will always be attempted but will not be implemented until the
        it is in a multiple-object context.
        """
        return None

    def get_associated_queryset(self):
        """
        Should get the default manager's queryset and perform appropriate
        association with a (View)Controller.
        """
        raise NotImplementedError

    def get_queryset(self):
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
