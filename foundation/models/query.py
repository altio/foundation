from django.db.models import query

from .exceptions import AssociativeAttributeError

__all__ = 'QuerySet',


class ModelIterable(query.ModelIterable):
    """
    Iterable that yields a model instance for each row.
    """

    def __iter__(self):
        for obj in super(ModelIterable, self).__iter__():
            obj._controller = self.queryset._controller
            obj._view_controller = self.queryset._view_controller
            yield obj


class AssociativeMixin(object):

    _controller = None
    _view_controller = None

    def __init__(self, *args, **kwargs):
        super(AssociativeMixin, self).__init__(*args, **kwargs)
        self._iterable_class = ModelIterable

    def _clone(self, **kwargs):
        kwargs.update(_controller=self._controller,
                      _view_controller=self._view_controller)
        return super(AssociativeMixin, self)._clone(**kwargs)

    def associate(self, **kwargs):
        view_controller = kwargs.get('view_controller')
        vc_controller = getattr(view_controller, 'controller')
        controller = kwargs.get('controller')
        if view_controller:
            if self._view_controller and self.view_controller != view_controller:
                raise AttributeError('Ambiguous ViewController association.')
            self._view_controller = view_controller
        if vc_controller or controller:
            if any((
                vc_controller and controller and vc_controller != controller,
                self._controller and controller and self._controller != controller,
                self._controller and vc_controller and self._controller != vc_controller
            )):
                raise AttributeError('Ambiguous Controller association.')
            self._controller = vc_controller or controller
        return self

    @property
    def controller(self):
        if not self._controller:
            raise AssociativeAttributeError(
                self.__class__.__name__, 'controller'
            )
        return self._controller

    @property
    def view_controller(self):
        if not self._view_controller:
            raise AssociativeAttributeError(
                self.__class__.__name__, 'view_controller'
            )
        return self._view_controller


class QuerySet(AssociativeMixin, query.QuerySet):
    """ View- and Controller-aware QuerySet """
