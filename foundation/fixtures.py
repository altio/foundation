from . import signals


def create_permissions(apps, app_label=None, **kwargs):
    """
    Helper method not used by backend but useful to other apps for writing
    fixture generators as part of initial migrations.  This will force creation
    of permissions and groups resulting from view hierarchy early in the process
    so downstream collections can be accurately rendered.  Of course if you
    change view that will impact permissions/groups post facto, so you will need
    to deal with that.

    app_label only comes into play when we are spoofing an AppConfig
    """

    # most likely called from a migration where app_config will not be set
    if 'app_config' not in kwargs:
        # get the migration's AppConfig
        fake_app_config = apps.get_app_config(app_label)
        # make it truthy to pass signal's condition
        fake_app_config.models_module = True
        kwargs['app_config'] = fake_app_config
    signals.create_permissions(apps=apps, **kwargs)
