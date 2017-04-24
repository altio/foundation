from django.http.response import HttpResponseRedirect

from .base import View

class ToggleSuperuser(View):

    def get(self, request, *args, **kwargs):
        """
        Toggles the superuser flag
        """
        if request.user.is_superuser:
            # default will be None which is falsey, inverted to True
            acting_as_superuser = not bool(
                request.session.get('acting_as_superuser')
            )
            request.session['acting_as_superuser'] = acting_as_superuser
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
