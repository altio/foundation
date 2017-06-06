from django.conf.urls import include, url
from django.contrib.admin import site as admin_site

from foundation.backend import get_backend


backend = get_backend()

urlpatterns = backend.urls
