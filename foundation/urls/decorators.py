from .backend import Backend, get_backend
from .controller import Controller

__all__ = 'backend_context', 'register'


def backend_context(fbv, **params):
    """
    Wraps a function-based view (FBV) with the each_context and media from the
    backend.

    @backend_context(auth_views.login)
    class AuthorController(backend.Controller):
        pass

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
