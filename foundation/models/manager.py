from django.db.models import manager
from .query import QuerySet


__all__ = 'Manager',


class Manager(manager.Manager.from_queryset(QuerySet)):
    use_for_related_fields = True
    use_in_migrations = True
