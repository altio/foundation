# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from functools import partial

from django.contrib.auth import get_permission_codename
from django.utils.functional import cached_property

__all__ = 'PermissionsMixin',


RE_MODE_PERMISSION = re.compile('has_(?P<mode>\w+)_permission')


def get_full_permission_codename(action, opts):
    action_map = {'edit': 'change'}
    if action in action_map:
        action = action_map[action]
    return '{}.{}'.format(opts.app_label, get_permission_codename(action, opts))


class PermissionsMixin(object):

    def get_permissions_model(self):
        return self.model

    def has_permission(self, mode, obj=None, is_parent=False):
        """
        The normal has_perm behavior in the PermissionsMixin gets and caches
        the static Group and User Permissions and then evaluates whether the
        User is permitted to take the action against the given Model.
        This is an adequate entry-level behavior, since all Users will be able
        to manage their profiles, subscriptions, and registrations.

        That said, our permissions framework has a little more intricacy.  We
        are going to map all Model instances to an Authoritative tree that
        understands the relationships of all models in the system and is able to
        quickly deduce whether a User can act upon a given Model or Model
        instance.

        Since the normal user permissions are restrictive in nature, we can
        first see if a generic action is *permitted* by the normal means (we
        expect the answer to be "no" for non-superusers since we do not expect
        to align many permissions or groups directly to Users.  In the case
        the normal means returns False, we can invoke the JIT logic as needed.
        """

        # reject inactive and unverified users
        user = self.view.request.user
        if not user.is_active:
            return False

        # attempt to get a user permission the normal way
        codename = self.get_url_name(mode)
        has_permission = user.has_perm(codename)

        return has_permission

    def get_model_perms(self, view):
        return {
            'add': self.has_add_permission(view),
            'change': self.has_edit_permission(view),
            'delete': self.has_delete_permission(view),
        }

    def has_module_perm(self, view):
        has_module_perm = view.request.has_module_perms(self.opts.app_label)
        return has_module_perm

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

    def is_superuser(self, user):
        return user.is_superuser

    def get_queryset(self):
        queryset = super(PermissionsMixin, self).get_queryset()

        # auth constrain when:
        # - app is NOT public
        # - user is NOT an acting superuser
        user = self.view.request.user
        if not (getattr(self.app_config, 'is_public', False) or self.is_superuser(user)):
            auth_query = self.auth_query
            if auth_query:
                queryset = queryset.filter(**{auth_query: user})

        return queryset

    def __getattribute__(self, name):
        super_getattr = super(PermissionsMixin, self).__getattribute__

        mode_url = re.match(RE_MODE_PERMISSION, name)
        if mode_url:
            method = super_getattr('has_permission')
            return partial(method, mode=mode_url.group('mode'))

        return super_getattr(name)
