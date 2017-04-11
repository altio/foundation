# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property

from ..base import AppPermissionsMixin


class ModelPermissionsMixin(AppPermissionsMixin):

    @cached_property
    def view_parent(self):
        view_parent = None

        # if registered controller [guarantee on View(Parent)] has parent
        if self.controller.parent:
            kwargs = self.kwargs.copy()
            kwargs.pop(self.controller.model_lookup, None)
            parent = self.controller.parent
            view_parent = parent.get_view_parent(view=self.view, kwargs=kwargs)

        return view_parent

    @property
    def view_parents(self):
        view_parent = self.view_parent
        while view_parent:
            yield view_parent
            view_parent = view_parent.view_parent

    @cached_property
    def user(self):
        return self.view.request.user

    @cached_property
    def auth_user_query(self):
        auth_user_query = (
            self.fk_name
            if self.controller.is_root
            else (
                '__'.join([self.fk.name, self.view_parent.auth_user_query])
                if self.view_parent.auth_user_query
                else None
        ))
        return auth_user_query 

    @cached_property
    def auth_query(self):
        return (
            {self.auth_user_query: self.user}
            if self.auth_user_query and self.user.is_active
            else {}
        )

    @property
    def has_acting_superuser(self):
        return self.user.is_superuser and \
            self.view.request.session.get('act_as_superuser')

    @cached_property  # TODO: test this is safe... cloning still works, right?
    def private_queryset(self):

        # avoid cyclic dependency
        queryset = super(ModelPermissionsMixin, self).get_queryset()

        # if not acting as superuser, apply access controls, filtering down to
        # none if there are no authorized objects
        if not self.has_acting_superuser:
            queryset = (
                queryset.filter(**self.auth_query)
                if self.auth_query
                else queryset.none()
            )
        return queryset

    def get_queryset(self):

        # do not auth constrain default queryset if controller has public modes
        return (
            super(ModelPermissionsMixin, self).get_queryset()
            if self.public_modes
            else self.private_queryset
        )

    def get_permissions_model(self):
        return self.model

    @cached_property
    def permissions(self):
        """
        Returns the list of permissions this ViewController has available to it
        given the user attached to the View.
        """

        # get the model for determining permissions for this view (this matters
        # for auto-generated through tables)
        permissions_model = self.get_permissions_model()

        # now resolve to a registered controller for the permissions model
        # -- this is allowed to be None in the case of an inline controller
        permissions_controller = (
            self.controller
            if self.controller and self.controller.model == permissions_model
            else self.view.get_related_controller(permissions_model)
        )

        # get the list of all modes across all routes for this controller
        if permissions_controller:
            modes = permissions_controller.all_modes
            public_modes = permissions_controller.public_modes
        # default to only public, list view when an inline (no controller)
        else:
            public_modes = modes = ('list')

        # process each mode
        view_permissions = []
        for mode in modes:

            # if mode is public, all users have permission
            if mode in public_modes:
                view_permissions.append(mode)
                continue

            # otherwise reject inactive and unverified users
            if not self.user.is_active:
                continue

            # if acting superuser, return True
            if self.has_acting_superuser:
                view_permissions.append(mode)
                continue

            # attempt to get a user permission the normal way
            codename = self.get_url_name(mode)
            if self.user.has_perm(codename):
                view_permissions.append(mode)

        return view_permissions

    def has_permission(self, mode):
        """
        Returns a boolean whether this ViewController has general access to a
        specified mode regardless of per-object permissions.
        """

        return mode in self.permissions
