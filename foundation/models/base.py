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

    class Meta:
        abstract = True
