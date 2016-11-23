from django.db.models import query

__all__ = 'QuerySet',


class ModelIterable(query.ModelIterable):
    """
    Iterable that yields a model instance for each row.
    """

    def __iter__(self):
        queryset = self.queryset
        db = queryset.db
        compiler = queryset.query.get_compiler(using=db)
        # Execute the query. This will also fill compiler.select, klass_info,
        # and annotations.
        results = compiler.execute_sql()
        select, klass_info, annotation_col_map = (compiler.select,
                                                  compiler.klass_info,
                                                  compiler.annotation_col_map)
        if klass_info is None:
            return
        model_cls = klass_info['model']
        select_fields = klass_info['select_fields']
        model_fields_start, model_fields_end = (select_fields[0],
                                                select_fields[-1] + 1)
        init_list = [f[0].target.attname
                     for f in select[model_fields_start:model_fields_end]]
        related_populators = query.get_related_populators(klass_info, select,
                                                          db)
        for row in compiler.results_iter(results):
            obj = model_cls.from_db(db, init_list,
                                    row[model_fields_start:model_fields_end])
            if related_populators:
                for rel_populator in related_populators:
                    rel_populator.populate(row, obj)
            if annotation_col_map:
                for attr_name, col_pos in annotation_col_map.items():
                    setattr(obj, attr_name, row[col_pos])

            # Add the known related objects to the model, if there are any
            if queryset._known_related_objects:
                for field, rel_objs in queryset._known_related_objects.items():
                    # Avoid overwriting objects loaded e.g. by select_related
                    if hasattr(obj, field.get_cache_name()):
                        continue
                    pk = getattr(obj, field.get_attname())
                    try:
                        rel_obj = rel_objs[pk]
                    except KeyError:
                        pass  # may happen in qs1 | qs2 scenarios
                    else:
                        setattr(obj, field.name, rel_obj)

            # attach the appropriate controller to the model
            obj._controller = queryset._controller

            yield obj


class ControllerView(object):

    _controller = None
    _view = None

    def __init__(self, *args, **kwargs):
        super(ControllerView, self).__init__(*args, **kwargs)
        self._iterable_class = ModelIterable

    def _clone(self, **kwargs):
        kwargs.update(_controller=self._controller, _view=self._view)
        return super(ControllerView, self)._clone(**kwargs)

    def attach(self, **kwargs):
        self._view = kwargs.pop('view')
        self._controller = kwargs.pop('controller', self._view.controller)
        return self

    @property
    def controller(self):
        if not self._controller:
            raise AttributeError(
                'This QuerySet does not have a controller.  This probably '
                'means you either attempted to do something from a view that '
                'did not attach itself to the QuerySet, or you tried to '
                'access a model instance method that relies on a view from '
                'outside of a view context.'
            )
        return self._controller

    @property
    def view(self):
        if not self._view:
            raise AttributeError(
                'This QuerySet does not have a view.  This probably means you '
                'either attempted to do something from a view that did not '
                'attach itself to the QuerySet, or you tried to access a '
                'model instance method that relies on a view from outside of '
                'a view context.'
            )
        return self._view


class QuerySet(ControllerView, query.QuerySet):
    """ View- and Controller-aware QuerySet """
