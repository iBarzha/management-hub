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
            '/api/auth/login/': 10,  # Login attempts (increased)
            '/api/auth/register/': 5,  # Registration attempts (increased)
            '/api/auth/token/refresh/': 30,  # Token refresh (increased)
            '/api/projects/': 300,  # Projects endpoint (high limit for frequent access)
            '/api/tasks/': 300,  # Tasks endpoint (high limit for frequent access)
            '/api/collaboration/presence/': 600,  # Presence updates (very high limit)
            '/api/auth/profile/': 150,  # Profile endpoint
            '/api/auth/preferences/': 150,  # Preferences endpoint
            'default': 200,  # Default for authenticated users (doubled)
            'anonymous': 50,  # Default for anonymous users (increased)
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
        rate_limit, normalized_path = self.get_rate_limit_and_path(path, request.user if hasattr(request, 'user') else None)
        
        # Check rate limit (use normalized path for cache key)
        cache_key = f"rate_limit_{identifier}_{normalized_path}"
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
    
    def get_rate_limit_and_path(self, path, user):
        """Get rate limit and normalized path for specific path and user."""
        # Check for exact matches first
        if path in self.rate_limits:
            return self.rate_limits[path], path
        
        # Check for partial matches (e.g., /api/projects/ matches /api/projects/1/)
        for rate_path, limit in self.rate_limits.items():
            if rate_path not in ['default', 'anonymous'] and path.startswith(rate_path):
                return limit, rate_path  # Use the rate_path as normalized path
        
        # Default limits based on authentication
        if user and user.is_authenticated:
            return self.rate_limits['default'], 'default'
        else:
            return self.rate_limits['anonymous'], 'anonymous'


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add security headers."""
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Enhanced Content Security Policy
        if request.path.startswith('/api/'):
            # Strict CSP for API endpoints
            csp_policy = (
                "default-src 'none'; "
                "script-src 'none'; "
                "style-src 'none'; "
                "img-src 'none'; "
                "connect-src 'self'; "
                "font-src 'none'; "
                "object-src 'none'; "
                "media-src 'none'; "
                "frame-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'none'; "
                "form-action 'none';"
            )
        else:
            # More permissive CSP for web pages
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "media-src 'self'; "
                "frame-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        
        response['Content-Security-Policy'] = csp_policy
        
        # Additional XSS protection headers
        response['X-Permitted-Cross-Domain-Policies'] = 'none'
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
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