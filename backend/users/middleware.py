import time
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware to prevent API abuse."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rate limit configurations (requests per minute)
        self.rate_limits = {
            '/api/auth/login/': 5,  # Login attempts
            '/api/auth/register/': 3,  # Registration attempts
            '/api/auth/token/refresh/': 10,  # Token refresh
            'default': 100,  # Default for authenticated users
            'anonymous': 20,  # Default for anonymous users
        }
        
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip rate limiting for superusers
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
            return None
            
        # Get client identifier
        client_ip = self.get_client_ip(request)
        user_id = None
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = request.user.id
            identifier = f"user_{user_id}"
        else:
            identifier = f"ip_{client_ip}"
        
        # Determine rate limit for this endpoint
        path = request.path
        rate_limit = self.get_rate_limit(path, request.user if hasattr(request, 'user') else None)
        
        # Check rate limit
        cache_key = f"rate_limit_{identifier}_{path}"
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= rate_limit:
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'detail': f'Maximum {rate_limit} requests per minute allowed.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, 60)  # 60 seconds TTL
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_rate_limit(self, path, user):
        """Get rate limit for specific path and user."""
        # Specific endpoint limits
        if path in self.rate_limits:
            return self.rate_limits[path]
        
        # Default limits based on authentication
        if user and user.is_authenticated:
            return self.rate_limits['default']
        else:
            return self.rate_limits['anonymous']


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add security headers."""
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy for API responses
        if request.path.startswith('/api/'):
            response['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none';"
        
        return response


class UserActivityMiddleware(MiddlewareMixin):
    """Middleware to track user activity for security monitoring."""
    
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Update last seen timestamp
            cache_key = f"user_activity_{request.user.id}"
            cache.set(cache_key, time.time(), 300)  # 5 minutes cache
            
            # Track suspicious activity patterns
            self.track_security_events(request)
    
    def track_security_events(self, request):
        """Track potential security events."""
        user_id = request.user.id
        client_ip = self.get_client_ip(request)
        
        # Track login attempts from different IPs
        if request.path == '/api/auth/login/' and request.method == 'POST':
            cache_key = f"login_ips_{user_id}"
            recent_ips = cache.get(cache_key, set())
            
            if isinstance(recent_ips, set):
                recent_ips.add(client_ip)
            else:
                recent_ips = {client_ip}
                
            cache.set(cache_key, recent_ips, 3600)  # 1 hour
            
            # Alert if user is logging in from many different IPs
            if len(recent_ips) > 3:
                self.log_security_event(user_id, 'multiple_ip_login', {
                    'ip_count': len(recent_ips),
                    'current_ip': client_ip
                })
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def log_security_event(self, user_id, event_type, data):
        """Log security events for monitoring."""
        import logging
        logger = logging.getLogger('security')
        logger.warning(f"Security event: {event_type} for user {user_id}: {data}")


class TokenValidationMiddleware(MiddlewareMixin):
    """Enhanced JWT token validation middleware."""
    
    def process_request(self, request):
        # Skip for non-API endpoints
        if not request.path.startswith('/api/'):
            return None
            
        # Skip for public endpoints
        public_endpoints = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/token/refresh/',
            '/api/docs/',
            '/api/swagger/',
        ]
        
        if any(request.path.startswith(endpoint) for endpoint in public_endpoints):
            return None
            
        # Check for JWT token in Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            # Check if token is blacklisted
            if self.is_token_blacklisted(token):
                return JsonResponse({
                    'error': 'Token has been revoked',
                    'detail': 'Please login again to get a new token.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return None
    
    def is_token_blacklisted(self, token):
        """Check if JWT token is blacklisted."""
        # This would integrate with django-rest-framework-simplejwt's blacklist
        # For now, we'll use a simple cache-based approach
        blacklist_key = f"blacklisted_token_{hash(token)}"
        return cache.get(blacklist_key, False)