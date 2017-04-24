# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import auth
from django.core.exceptions import PermissionDenied


__all__ = 'ActiveSuperuserMixin',


RE_USERNAME = r'^[A-Za-z0-9.-]+$'


# NOTE: directly copied form django.contrib.auth.models -- import is unsafe
# A few helper functions for common logic between User and AnonymousUser.
def _user_has_perm(user, perm, obj):
    """
    A backend can raise `PermissionDenied` to short-circuit permission checking.
    """
    for backend in auth.get_backends():
        if not hasattr(backend, 'has_perm'):
            continue
        try:
            if backend.has_perm(user, perm, obj):
                return True
        except PermissionDenied:
            return False
    return False


def _user_has_module_perms(user, app_label):
    """
    A backend can raise `PermissionDenied` to short-circuit permission checking.
    """
    for backend in auth.get_backends():
        if not hasattr(backend, 'has_module_perms'):
            continue
        try:
            if backend.has_module_perms(user, app_label):
                return True
        except PermissionDenied:
            return False
    return False


class ActiveSuperuserMixin(object):
    """
    A mixin class which provides the overrides needed for "opt-in" superuser
    access.
    """

    _acting_as_superuser = False

    @property
    def acting_as_superuser(self):
        return self._acting_as_superuser

    @acting_as_superuser.setter
    def acting_as_superuser(self, value):
        self._acting_as_superuser = value

    @property
    def is_acting_superuser(self):
        return self.is_superuser and self.acting_as_superuser

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission. This method
        queries all available auth backends, but returns immediately if any
        backend returns True. Thus, a user who has permission from a single
        auth backend is assumed to have permission in general. If an object is
        provided, permissions for this specific object are checked.
        """

        # Active, acting superusers have all permissions.
        if self.is_active and self.is_acting_superuser:
            return True

        # Otherwise we need to check the backends.
        return _user_has_perm(self, perm, obj)

    def has_module_perms(self, app_label):
        """
        Returns True if the user has any permissions in the given app label.
        Uses pretty much the same logic as has_perm, above.
        """
        # Active, acting superusers have all permissions.
        if self.is_active and self.is_acting_superuser:
            return True

        return _user_has_module_perms(self, app_label)
