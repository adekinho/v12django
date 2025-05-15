from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware

class CustomCsrfMiddleware(CsrfViewMiddleware, MiddlewareMixin):
    """
    Custom middleware to handle CSRF verification for browser previews.
    """
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Check if the request is coming from a browser preview or localhost
        if 'HTTP_REFERER' in request.META and ('127.0.0.1:' in request.META['HTTP_REFERER'] or 'localhost:' in request.META['HTTP_REFERER']):
            # Skip CSRF validation for browser preview and localhost requests
            return None
        
        # Otherwise, use the standard CSRF validation
        return super().process_view(request, callback, callback_args, callback_kwargs)
