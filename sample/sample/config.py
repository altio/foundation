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
    create_permissions = True

    class Media:
        css = {
            'all': (
                'pkg/bootstrap/css/bootstrap.min.css',
                'pkg/bootstrap/css/bootstrap-theme.min.css',
                'pkg/fa/css/font-awesome.css',
                'css/home.css',
                'css/overrides.css',
            ),
        }
        js = [
            'js/jquery-1.11.2.min.js',
            'pkg/bootstrap/js/bootstrap.min.js',
        ]

    def each_context(self, request):
        kwargs = super(SiteBackend, self).each_context(request=request)
        if getattr(settings, 'COPYRIGHT_STATEMENT', None):
            kwargs['copyright'] = settings.COPYRIGHT_STATEMENT.format(
                year=timezone.now().year)
        return kwargs


backends.append(SiteBackend())
