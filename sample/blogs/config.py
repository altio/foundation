from django.apps import AppConfig
# from django.db.models.signals import post_migrate

from foundation.fixtures import create_permissions


def create_fixtures(apps, **kwargs):

    # create permissions and groups for this app
    # create_permissions(apps, app_label='blogs')
    pass


class BlogsConfig(AppConfig):

    name = 'blogs'
    url_namespace = 'blogs'
    url_prefix = 'blogs'
    app_index_class = None  # we are going to park blogs on root

    def ready(self):
        super(BlogsConfig, self).ready()
        """
        if one wanted to create fixtures (esp. add permissions), do that here

        post_migrate.connect(
            create_fixtures,
            dispatch_uid="django.contrib.auth.management.create_permissions"
        )
        """
