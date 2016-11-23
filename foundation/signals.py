from django.apps import apps as global_apps
from django.conf import settings
from django.contrib.auth.management import create_permissions as auth_perms
from django.db import DEFAULT_DB_ALIAS, router
from django.utils import translation


from django.urls.resolvers import LocaleRegexURLResolver, RegexURLResolver,\
    RegexURLPattern
from django.core.exceptions import ViewDoesNotExist
from .urls import get_backend


def create_permissions(app_config, verbosity=2, interactive=True, using=DEFAULT_DB_ALIAS, apps=global_apps, **kwargs):

    # run auth's create_permissions since we are re-writing the signal handler
    auth_perms(app_config, verbosity, interactive, using, apps, **kwargs)

    if not app_config.models_module:
        return

    app_label = app_config.label
    try:
        app_config = apps.get_app_config(app_label)
        ContentType = apps.get_model('contenttypes', 'ContentType')
        Permission = apps.get_model('auth', 'Permission')
        Group = apps.get_model('auth', 'Group')
    except LookupError:
        return

    if not router.allow_migrate_model(using, Permission):
        return

    # The ctypes we will review
    ctypes = set()
    for model in app_config.get_models():
        # Force looking up the content types in the current database
        # before creating foreign keys to them.
        ctype = ContentType.objects.db_manager(using).get_for_model(model)
        ctypes.add(ctype)

    # Find all the Permissions that have a content_type for a model we're
    # looking for.  We don't need to check for codenames since we already have
    # a list of the ones we're going to create.
    all_perms = set(Permission.objects.using(using).filter(
        content_type__in=ctypes,
    ).values_list("codename", flat=True))

    def post_process_urlpatterns(urlpatterns, base='', namespace=None):

        patterns, resolvers = {}, {}
        for p in urlpatterns:
            if isinstance(p, RegexURLPattern):
                try:
                    if not p.name:
                        name = p.name
                    elif namespace:
                        name = '{0}:{1}'.format(namespace, p.name)
                    else:
                        name = p.name
                    if name in patterns:
                        raise ValueError('"{}" is duplicate')

                    # we are presuming only CBV... could handle FBV one day
                    view_class = p.callback.view_class if hasattr(p.callback, 'view_class') else None
                    view_model = None
                    if view_class:
                        view_initkwargs = p.callback.view_initkwargs
                        view_controller = p.callback.view_initkwargs.get('controller')
                        view_model = view_controller.model if view_controller else None

                    if view_model:
                        content_type = ContentType.objects.get_for_model(view_model)
                        if content_type not in ctypes:
                            continue
                        view_mode = view_class.mode or view_initkwargs['mode']
                        verbose_name_plural = view_model._meta.verbose_name_plural
                    else:
                        # we cannot add perms on models not in the calling model's app
                        # we will not add perms for non-model views because Perms do not allow
                        # we will always create and refresh groups
                        continue
                        content_type = None
                        name_parts = name.split(':')
                        view_mode = name_parts[-1]
                        verbose_name_plural = '{}'.format(':'.join(name_parts[:-1]))
                    permission_name = 'Can {} {}'.format(view_mode, verbose_name_plural)
                    permission = Permission(codename=name, name=permission_name, content_type=content_type)
                    patterns[name] = (base + p.regex.pattern, p.callback, permission)
                except ViewDoesNotExist:
                    continue
            elif isinstance(p, RegexURLResolver):
                try:
                    url_patterns = p.url_patterns
                except ImportError:
                    continue
                if namespace and p.namespace:
                    _namespace = '{0}:{1}'.format(namespace, p.namespace)
                else:
                    _namespace = (p.namespace or namespace)
                if isinstance(p, LocaleRegexURLResolver):
                    for langauge in settings.LANGUAGES:
                        with translation.override(langauge[0]):
                            if _namespace in resolvers:
                                raise ValueError('"{}" is duplicate')
                            resolvers[_namespace] = post_process_urlpatterns(
                                url_patterns, base + p.regex.pattern,
                                namespace=_namespace)
                else:
                    if _namespace in resolvers:
                        raise ValueError('"{}" is duplicate')
                    resolvers[_namespace] = post_process_urlpatterns(
                        url_patterns, base + p.regex.pattern,
                        namespace=_namespace)

                # bulk create the permissions
                all_patterns = resolvers[_namespace]['patterns']
                new_patterns, new_permissions = [], []
                for name, data in all_patterns.items():
                    if name not in all_perms:
                        new_patterns.append(name)
                        new_permissions.append(data[2])
                        print("Adding permission '%s'" % name)
                Permission.objects.using(using).bulk_create(new_permissions)

                # get-or-create and update the group
                group, created = Group.objects.using(using).get_or_create(
                    name=_namespace)
                if created:
                    print("Adding group '%s'" % _namespace)
                    missing_patterns = new_patterns
                else:
                    missing_patterns = set(new_patterns) - set(
                        group.permissions.values_list('codename', flat=True))
                if missing_patterns:
                    new_group_permissions = Permission.objects.filter(
                        codename__in=missing_patterns)
                    group.permissions.add(*new_group_permissions)
                    for permission in new_group_permissions:
                        print("Adding permission '%s' to group '%s'" % (permission.codename, _namespace))

                    """
                    Can't do nested groups yet so we will rely on controller traversal.
                    group_groups = Group.objects.filter(name__in=resolvers)
                    group.groups.add(*group_groups)
                    """
        return dict(patterns=patterns, resolvers=resolvers)

    post_process_urlpatterns(get_backend().urls)
