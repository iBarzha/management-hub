from django.middleware.csrf import CsrfViewMiddleware
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
from django.urls import resolve
from rest_framework import status
import logging


class EnhancedCSRFMiddleware(CsrfViewMiddleware):
    """Enhanced CSRF protection middleware with additional security features."""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.logger = logging.getLogger('security')
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        """Process view with enhanced CSRF protection."""
        # Skip CSRF for all API endpoints since we use JWT authentication
        if request.path.startswith('/api/'):
            return None
        
        # Use Django's default CSRF protection for non-API requests
        return super().process_view(request, callback, callback_args, callback_kwargs)
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CSRFTokenView:
    """View to provide CSRF tokens for frontend applications."""
    
    def get(self, request):
        """Get CSRF token for the current session."""
        from django.middleware.csrf import get_token
        token = get_token(request)
        return JsonResponse({'csrfToken': token})


class DoubleSubmitCookieMiddleware(MiddlewareMixin):
    """Double Submit Cookie pattern for additional CSRF protection."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('security')
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process request with double submit cookie validation."""
        # Skip for GET, HEAD, OPTIONS, TRACE
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return None
            
        # Skip for all API endpoints since we use JWT authentication
        if request.path.startswith('/api/'):
            return None
        
        # Check double submit cookie
        csrf_cookie = request.COOKIES.get('csrftoken')
        csrf_header = request.META.get('HTTP_X_CSRFTOKEN')
        
        if csrf_cookie and csrf_header:
            if csrf_cookie != csrf_header:
                self.logger.warning(
                    f"Double submit cookie mismatch for {request.path} "
                    f"from {self._get_client_ip(request)}"
                )
                return JsonResponse({
                    'error': 'CSRF validation failed',
                    'detail': 'Invalid CSRF token.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SameSiteMiddleware(MiddlewareMixin):
    """Middleware to ensure SameSite cookie attributes are properly set."""
    
    def process_response(self, request, response):
        """Set SameSite attributes on cookies."""
        # Set SameSite on all cookies
        for cookie in response.cookies.values():
            if not cookie.get('samesite'):
                cookie['samesite'] = 'Lax'
                
            # Secure flag for production
            if not settings.DEBUG:
                cookie['secure'] = True
                
        return response


class OriginValidationMiddleware(MiddlewareMixin):
    """Middleware to validate request origins for additional CSRF protection."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('security')
        
        # Allowed origins for CSRF-sensitive requests
        self.allowed_origins = [
            settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000',
        ]
        
        # Add CORS allowed origins
        if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
            self.allowed_origins.extend(settings.CORS_ALLOWED_ORIGINS)
            
        super().__init__(get_response)
    
    def process_request(self, request):
        """Validate request origin."""
        # Only check for state-changing methods
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return None
            
        # Skip for all API endpoints since we use JWT authentication
        if request.path.startswith('/api/'):
            return None
        
        # Check Origin header
        origin = request.META.get('HTTP_ORIGIN')
        referer = request.META.get('HTTP_REFERER')
        
        if origin:
            if not self._is_allowed_origin(origin):
                self.logger.warning(
                    f"Invalid origin {origin} for {request.path} "
                    f"from {self._get_client_ip(request)}"
                )
                return JsonResponse({
                    'error': 'Invalid origin',
                    'detail': 'Request origin not allowed.'
                }, status=status.HTTP_403_FORBIDDEN)
        elif referer:
            # Fall back to Referer header if Origin is not present
            if not self._is_allowed_referer(referer):
                self.logger.warning(
                    f"Invalid referer {referer} for {request.path} "
                    f"from {self._get_client_ip(request)}"
                )
                return JsonResponse({
                    'error': 'Invalid referer',
                    'detail': 'Request referer not allowed.'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            # No Origin or Referer header
            self.logger.warning(
                f"Missing origin/referer headers for {request.path} "
                f"from {self._get_client_ip(request)}"
            )
            return JsonResponse({
                'error': 'Missing headers',
                'detail': 'Origin or Referer header required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return None
    
    def _is_allowed_origin(self, origin):
        """Check if origin is allowed."""
        return origin in self.allowed_origins
    
    def _is_allowed_referer(self, referer):
        """Check if referer is from allowed origin."""
        for allowed_origin in self.allowed_origins:
            if referer.startswith(allowed_origin):
                return True
        return False
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Custom decorators for CSRF protection
def csrf_protect_api(view_func):
    """Decorator to enforce CSRF protection on API views."""
    def wrapped_view(request, *args, **kwargs):
        # Check for CSRF token
        csrf_token = request.META.get('HTTP_X_CSRFTOKEN')
        if not csrf_token and request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return JsonResponse({
                'error': 'CSRF token required',
                'detail': 'This endpoint requires CSRF protection.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


def validate_request_integrity(view_func):
    """Decorator to validate request integrity."""
    def wrapped_view(request, *args, **kwargs):
        # Check for suspicious patterns
        if request.method in ('POST', 'PUT', 'PATCH'):
            # Check content length
            content_length = request.META.get('CONTENT_LENGTH')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
                return JsonResponse({
                    'error': 'Request too large',
                    'detail': 'Request payload exceeds maximum size.'
                }, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view