from django.conf.urls import include, url
from django.contrib.admin import site as admin_site
from django.contrib.auth import urls as auth_urls

from foundation.backend import backend_context, get_backend

auth_urlpatterns = []
for auth_urlpattern in auth_urls.urlpatterns:
    auth_urlpattern.callback = backend_context(auth_urlpattern.callback)
    auth_urlpatterns.append(auth_urlpattern)

urlpatterns = [
    url(r'^admin/', include(admin_site.urls)),
    url(r'', include(auth_urls)),
]

backend = get_backend()
urlpatterns.extend(backend.urls)
