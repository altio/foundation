# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from .exceptions import AssociativeAttributeError
from .manager import Manager

__all__ = 'Model',


class AssociativeMixin(object):

    @property
    def view_controller(self):
        if not self._view_controller:
            raise AssociativeAttributeError(
                self.__class__.__name__, 'view_controller'
            )
        return self._view_controller

    # Methods
    def get_model(self):
        return self.__class__

    @classmethod
    def get_meta(cls):
        return cls._meta


class Model(AssociativeMixin, models.Model):

    objects = Manager()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.full_clean(exclude=None, validate_unique=True)
        super(Model, self).save(
            force_insert=force_insert, force_update=force_update,
            using=using, update_fields=update_fields
        )

    """
    NOTE: original approach was to associate all objects with the vc that
    yielded them.  This was especially useful when lazily using regex to provide
    attr-style lookups e.g. obj.has_edit_permission.  After more consideration
    I am leaning toward template tags instead of obj attrs and thus calling
    helpers with explicit params... I think that will yield better debugging.
    """

    def has_permission(self, view_controller, mode):

        # if no view-level permission, bail
        has_permission = view_controller.has_permission(mode)

        # otherwise, refer to the view controller's private (auth) queryset
        if has_permission:
            has_permission = self in view_controller.private_queryset

        return has_permission

    class Meta:
        abstract = True
