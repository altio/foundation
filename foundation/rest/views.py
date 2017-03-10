from django.views import generic  # TODO: REST framework APIView

from ..backend import views
from django.http.response import JsonResponse


class ControllerAPIView(views.ControllerViewMixin, generic.View):
    """ Fake API View to mock out REST integration. """

    def get(self, request, *args, **kwargs):
        return JsonResponse({})

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
