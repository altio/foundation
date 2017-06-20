# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.decorators import available_attrs

from ..utils import redirect_to_url
from .base import Backend, get_backend
from .controllers import Controller

__all__ = 'backend_context', 'register', 'request_passes_test'


def backend_context(fbv, **params):
    """
    Wraps a function-based view (FBV) with the each_context and media from the
    backend.

    @backend_context(backend)
    def login(request, *args, **kwargs):
        return HttpResponse(...)

    A param of `backend` can be passed as the backend, otherwise the default
    backend will be used.
    """

    def wrapper(*args, **kwargs):
        request = args[0] if len(args) else kwargs['request']
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        backend = params.get('backend') or get_backend()
        kwargs['extra_context'].update(backend.each_context(request))
        kwargs['extra_context']['media'] = backend.media
        return fbv(*args, **kwargs)

    return wrapper


def register(*models, **kwargs):
    """
    Registers the given model(s) classes and wrapped Controller class with
    the active backend:

    @register(Author)
    class AuthorController(backend.Controller):
        pass

    A kwarg of `backend` can be passed as the backend, otherwise the default
    backend will be used.
    """

    def _controller_class_wrapper(controller_class):
        if not models:
            raise ValueError('At least one model must be passed to register.')

        site_backend = kwargs.pop('backend', get_backend())

        if not isinstance(site_backend, Backend):
            raise ValueError('backend must subclass Backend')

        if not issubclass(controller_class, Controller):
            raise ValueError('Wrapped class must subclass Controller.')

        site_backend.register(models, controller_class=controller_class)

        return controller_class
    return _controller_class_wrapper


def request_passes_test(test_func, redirect_url=None,
                        redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the request passes the given test,
    redirecting to the redirect url if necessary. The test should be a
    callable that takes the request and returns True if the test passes.
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request):
                return view_func(request, *args, **kwargs)
            return redirect_to_url(request, redirect_url, redirect_field_name)
        return _wrapped_view
    return decorator
