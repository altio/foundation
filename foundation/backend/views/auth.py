from django.http.response import HttpResponseRedirect

from .base import View

class ToggleSuperuser(View):

    def get(self, request, *args, **kwargs):
        """
        Toggles the superuser flag
        """
        if request.user.is_superuser:
            request.session['act_as_superuser'] = not bool(request.session.get('act_as_superuser'))
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
