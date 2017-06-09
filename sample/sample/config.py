from foundation.backend import Backend, backends
from django.conf import settings
from django.utils import timezone
from django.apps import AppConfig

from .views import SiteIndexView


class SiteConfig(AppConfig):
    name = 'sample'


class SiteBackend(Backend):

    routes = ('ajax', 'api', 'embed')
    site_index_class = SiteIndexView
    auth_url_prefix = ''
    admin_url_prefix = 'admin'
    create_permissions = True

    class Media:
        css = {
            'all': (
            ),
        }
        js = [
        ]

    def each_context(self, request):
        kwargs = super(SiteBackend, self).each_context(request=request)
        if getattr(settings, 'COPYRIGHT_STATEMENT', None):
            kwargs['copyright'] = settings.COPYRIGHT_STATEMENT.format(
                year=timezone.now().year)
        return kwargs


backends.append(SiteBackend())
