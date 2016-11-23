from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy as _

from .signals import create_permissions


def autodiscover():
    from django.utils.module_loading import autodiscover_modules
    from .urls import get_backend
    autodiscover_modules('controllers', register_to=get_backend())


class FoundationConfig(AppConfig):
    """The default Foundation AppConfig which does autodiscovery."""

    name = 'foundation'
    verbose_name = _("Foundation")

    def ready(self):
        super(FoundationConfig, self).ready()
        self.module.config.autodiscover()
        from .urls import get_backend
        backend = get_backend()
        if backend.create_permissions:
            post_migrate.connect(
                create_permissions,
                dispatch_uid="django.contrib.auth.management.create_permissions"
            )
