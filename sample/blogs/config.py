from django.apps import AppConfig
# from django.db.models.signals import post_migrate

from foundation.fixtures import create_permissions


def create_fixtures(apps, **kwargs):

    # create permissions and groups for this app
    # create_permissions(apps, app_label='blogs')
    pass


class BlogsConfig(AppConfig):

    # this flag determines whether to expose the public views
    is_public = True

    name = 'blogs'
    url_namespace = 'blogs'
    url_prefix = 'blogs'

    def ready(self):
        super(BlogsConfig, self).ready()
        """
        if one wanted to create fixtures (esp. add permissions), do that here

        post_migrate.connect(
            create_fixtures,
            dispatch_uid="django.contrib.auth.management.create_permissions"
        )
        """
