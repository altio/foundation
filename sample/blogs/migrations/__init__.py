from django.template.defaultfilters import slugify
from django.utils import timezone
from faker import Faker

from .. import config, models


def generate_initial_data(apps, schema_editor):

    # create permissions for this app
    config.create_fixtures(apps)

    # add service for all users
    User = apps.get_model('auth', 'user')
    for name in ('Joe', 'Sarah', 'Bob', 'Lucy', 'Admin'):
        User.objects.create(
            username=name.lower(),
            first_name=name
        )

    # add service for all users
    Blog = apps.get_model('blogs', 'Blog')
    Post = apps.get_model('blogs', 'Post')

    for user in User.objects.all():
        # TODO: FIX SLUG UNIQUENESS ISSUE
        for b in ('Red', 'Yellow', 'Blue'):
            title = "{}'s {} Blog".format(user.first_name, b)
            slug = slugify(title)
            blog = Blog.objects.create(owner=user, title=title, slug=slug)
            for p in ('First', 'Second', 'Third'):
                title = "{}'s {} {} Post".format(user.first_name, p, b)
                slug = slugify(title)
                Post.objects.create(blog=blog, title=title, slug=slug)
