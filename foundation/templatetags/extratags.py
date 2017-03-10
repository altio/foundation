from django.template.defaulttags import register
from foundation.forms import models


@register.simple_tag(takes_context=True)
def mode_url(context, mode, obj=None, route=None):
    """
    "context" will carry in the view from which this tag was called.
    "mode" will be the named mode for which you are attempting to attain a url.
    "obj" serves multiple roles.  Since this is being called from within the
    context of a view, if the view has a single object in focus, there is no
    need to pass the object.  If you are iterating through a list of objects
    (e.g. formsets on a view, forms in a formset), however, you should pass the
    iteration instance (formset, form) as the object to provide the additional
    context needed to resolve the URL.
    For instance, if you want the "add" URL for a child controller represented
    by a form(set), you would pass that object in.  Or if you wanted the "edit"
    URL for an existing child object (form) you would pass that in.
    Finally, if you are attempting to access a named route (e.g. api),
    you can pass that as a param for lookup.
    NOTE: Controller lookup follows contextual rules.  That is, if it is a
    direct descendant, then if it is a child of any parent in ancestry
    (including backend).
    """

    # derive a view controller from context or supported types
    if obj is None:
        view = context['view']
        if 'form' in context:
            obj = context['form'].original
    elif isinstance(obj, models.BaseModelFormSet):
        view = obj.view
    elif isinstance(obj, models.FormSetModelForm):
        view = obj.view
        obj = obj.original
    elif isinstance(obj, models.ModelForm):
        view = obj.view
        obj = obj.instance
    else:
        raise ValueError('"obj" is unsupported type: {}'.format(type(obj)))

    return view.get_url(mode, obj=obj, route=route)
