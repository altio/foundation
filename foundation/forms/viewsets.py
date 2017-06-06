# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from ..backend import ControllerViewSet
from . import views

__all__ = 'PageViewSet', 'EmbedViewSet'


class BaseFormViewSet(ControllerViewSet):

    view_child_class = views.base.FormChild
    view_parent_class = views.base.FormParent

    named_view_classes = (
        ('list', views.ListView),
        ('add', views.AddView),
        ('edit', views.EditView),
        ('delete', views.DeleteView),
        ('display', views.DisplayView),
    )

    def get_urlpatterns(self):
        model_lookup = self.router.controller.model_lookup
        urlpatterns = []

        # reserved modes list, add, and display need special treatment
        if 'list' in self:
            urlpatterns.append(url(r'^$', self['list'], name='list'))
        if 'add' in self:
            urlpatterns.append(url(r'^add$', self['add'], name='add'))

        # attach all single-object manipulation modes
        for mode in set(self) - set(['list', 'add', 'display']):
            urlpatterns.append(url(
                r'^(?P<{lookup}>[-\w]+)/{mode}$'.format(
                    lookup=model_lookup,
                    mode=mode,
                ),
                self[mode],
                name=mode,
            ))

        # defer the display view until after "add" so it is not mistaken as slug
        if 'display' in self:
            urlpatterns.append(url(
                r'^(?P<{lookup}>[-\w]+)$'.format(lookup=model_lookup),
                self['display'],
                name='display',
            ))

        return urlpatterns


class PageMixin(object):

    def get_context_data(self, **kwargs):
        context = super(PageMixin, self).get_context_data(**kwargs)
        context['is_embed'] = False
        return context


class PageViewSet(BaseFormViewSet):

    view_class_mixin = PageMixin


class EmbedMixin(object):

    def get_context_data(self, **kwargs):
        context = super(EmbedMixin, self).get_context_data(**kwargs)
        context['is_embed'] = True
        return context


class EmbedViewSet(BaseFormViewSet):

    view_class_mixin = EmbedMixin
