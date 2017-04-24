# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import backends
from django.contrib.auth.models import Permission


class ModelBackend(backends.ModelBackend):

    def _get_user_permissions(self, obj):
        return set(obj.user_permissions.values_list('codename', flat=True))

    def _get_group_permissions(self, obj):
        groups = obj.groups.all()
        group_codenames = set(groups.values_list('name', flat=True))
        group_permissions = set(Permission.objects.filter(
            group__in=groups).values_list('codename', flat=True))
        return group_codenames | group_permissions

    def _get_permissions(self, user_obj, obj, from_name):
        """
        Returns the permissions of `user_obj` from `from_name`. `from_name` can
        be either "group" or "user" to return permissions from
        `_get_group_permissions` or `_get_user_permissions` respectively.
        """
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        perm_cache_name = '_%s_perm_cache' % from_name
        if not hasattr(user_obj, perm_cache_name):
            if user_obj.is_acting_superuser:
                perms = Permission.objects.all()
            else:
                perms = getattr(self, '_get_%s_permissions' % from_name)(user_obj)
            setattr(user_obj, perm_cache_name, set(perms))
        return getattr(user_obj, perm_cache_name)

    def has_module_perms(self, user_obj, app_label):
        """
        Returns True if user_obj has any permissions in the given app_label.
        """
        if not user_obj.is_active:
            return False
        for perm in self.get_all_permissions(user_obj):
            if perm.partition(':')[0] == app_label:
                return True
        return False
