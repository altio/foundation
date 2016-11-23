from foundation.urls import get_backend
from django.conf.urls import include, url
from django.contrib.admin import site as admin_site
from django.contrib.auth import urls as auth_urls

urlpatterns = [
    url(r'^admin/', include(admin_site.urls)),
    url(r'', include(auth_urls)),
]

backend = get_backend()
urlpatterns.extend(backend.urls)
