from django.db.models import QuerySet, Model
from django.template.defaulttags import register, Node, NodeList, TemplateSyntaxError
from foundation.forms import models


class IfPermissionNode(Node):
    child_nodelists = ('nodelist_true', 'nodelist_false')

    def __init__(self, mode, obj, nodelist_true, nodelist_false):
        self.mode, self.obj = mode, obj
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false

    def __repr__(self):
        return "<IfPermissionNode>"

    def render(self, context):
        mode = self.mode.resolve(context, True)
        obj = self.obj.resolve(context, True) if self.obj else None

        if obj is None:
            view_controller = context['view']
            if 'form' in context:
                obj = context['form'].instance
        elif isinstance(obj, QuerySet):
            view_controller = getattr(obj, 'view_controller', context['view'])
            obj = None
        elif isinstance(obj, Model):
            view_controller = getattr(obj, 'view_controller', context['view'])
        elif isinstance(obj, models.BaseInlineFormSet):
            view_controller = obj.view_controller
            obj = obj.instance
        elif isinstance(obj, models.BaseModelFormSet):
            view_controller = obj.view_controller
            obj = None
        elif isinstance(obj, models.FormSetModelForm):
            view_controller = obj.view_controller
            obj = obj.original
        elif isinstance(obj, models.ModelForm):
            view_controller = obj.view_controller
            obj = obj.instance
        else:
            raise ValueError('"obj" is unsupported type: {}'.format(type(obj)))

        if (obj.has_permission(view_controller, mode) if obj else view_controller.has_permission(mode)):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


@register.tag
def ifpermission(parser, token):
    bits = list(token.split_contents())
    nargs = len(bits)
    if nargs not in (2, 3):
        raise TemplateSyntaxError("%r takes one or two arguments" % bits[0])
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    mode = parser.compile_filter(bits[1])
    obj = parser.compile_filter(bits[2]) if nargs == 3 else None
    return IfPermissionNode(mode, obj, nodelist_true, nodelist_false)


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
        view_controller = context['view']
        if 'form' in context:
            obj = context['form'].instance
    elif isinstance(obj, QuerySet):
        view_controller = getattr(obj, 'view_controller', context['view'])
        obj = None
    elif isinstance(obj, Model):
        view_controller = getattr(obj, 'view_controller', context['view'])
    elif isinstance(obj, models.BaseInlineFormSet):
        view_controller = obj.view_controller
        obj = obj.instance
    elif isinstance(obj, models.BaseModelFormSet):
        view_controller = obj.view_controller
        obj = None
    elif isinstance(obj, models.FormSetModelForm):
        view_controller = obj.view_controller
        obj = obj.original
    elif isinstance(obj, models.ModelForm):
        view_controller = obj.view_controller
        obj = obj.instance
    else:
        raise ValueError('"obj" is unsupported type: {}'.format(type(obj)))

    return view_controller.get_url(mode, obj=obj, route=route)
