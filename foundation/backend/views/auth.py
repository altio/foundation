from django.http.response import HttpResponseRedirect, Http404

from .base import View


class ToggleSuperuser(View):

    def get(self, request, *args, **kwargs):
        """
        Toggles the superuser flag
        """
        referer = request.META.get('HTTP_REFERER')
        if not referer:
            raise Http404()
        if request.user.is_superuser:
            # default will be None which is falsey, inverted to True
            acting_as_superuser = not bool(
                request.session.get('acting_as_superuser')
            )
            request.session['acting_as_superuser'] = acting_as_superuser
        return HttpResponseRedirect(referer)
