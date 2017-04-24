from django.contrib.auth import middleware


class AuthenticationMiddleware(middleware.AuthenticationMiddleware):

    def process_request(self, request):
        super(AuthenticationMiddleware, self).process_request(request)
        if request.user.is_superuser:
            request.user.acting_as_superuser = bool(
                request.session.get('acting_as_superuser')
            )
