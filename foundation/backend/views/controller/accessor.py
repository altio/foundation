# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property

from ..base import AppPermissionsMixin


class ModelPermissionsMixin(AppPermissionsMixin):

    @property
    def user(self):
        """ Shortcut to user on request via auth middleware. """
        return self.view.request.user

    @property
    def auth_object(self):
        """ The top-level object used by the view for providing auth. """
        return self.user

    @property
    def has_acting_superuser(self):
        """ Returns True if view user is superuser and acting as such. """
        return getattr(self.user, 'is_acting_superuser', False)

    @cached_property  # TODO: test this is safe... cloning still works, right?
    def private_queryset(self):
        """ Returns the auth-permitted queryset when not an acting superuser. """

        # if not acting as superuser, apply access controls, filtering down to
        # none if there are no authorized objects
        return (
            super(ModelPermissionsMixin, self).get_queryset()
            if self.has_acting_superuser
            else self.get_auth_queryset(self.auth_object)
        )

    def get_queryset(self):
        """ Returns the private queryset when not an acting superuser. """

        # do not auth constrain default queryset if controller has public modes
        return (
            super(ModelPermissionsMixin, self).get_queryset()
            if self.public_modes
            else self.private_queryset
        )

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

    def get_permissions_model(self):
        return self.model

    def get_permissions(self):
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
        return True  # mode in self.get_permissions()
