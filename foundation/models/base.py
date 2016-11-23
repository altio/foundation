# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from django.db import models
from functools import partial

from .manager import Manager

__all__ = 'Model',


RE_MODE_URL = re.compile('get_(?P<mode>\w+)_url')


class ControllerView(object):

    @property
    def controller(self):
        if not self._controller:
            raise AttributeError(
                'This model instance does not have a controller.  This '
                'means you either attempted to do something from a view that '
                'did not attach itself to the QuerySet, or you tried to '
                'access a model instance method that relies on a view from '
                'outside of a view context.'
            )
        return self._controller

    # Methods
    def get_model(self):
        return self.__class__

    @classmethod
    def get_meta(cls):
        return cls._meta

    def get_absolute_url(self):
        return self.get_view_url()

    def __getattribute__(self, name):
        super_getattr = super(ControllerView, self).__getattribute__

        if name == 'get_absolute_url':
            return super_getattr('get_absolute_url')

        mode_url = re.match(RE_MODE_URL, name)
        if mode_url:
            registered_controller = self.controller.controller
            lookup_key = registered_controller.model_lookup
            try:
                lookup_value = super_getattr('slug')
            except AttributeError:
                lookup_value = super_getattr('pk')
            kwargs = {'mode': mode_url.group('mode'), lookup_key: lookup_value}
            return partial(self.controller.get_url, **kwargs)

        return super_getattr(name)


class Model(ControllerView, models.Model):

    objects = Manager()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        #self.full_clean(exclude=None, validate_unique=True)
        super(Model, self).save(
            force_insert=force_insert, force_update=force_update,
            using=using, update_fields=update_fields
        )

    class Meta:
        abstract = True
