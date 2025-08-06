from django.core.cache import cache
from django.http import HttpResponse
import json
import hashlib


class CacheMiddleware:
    """
    Middleware for caching API responses
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only cache GET requests
        if request.method != 'GET':
            return self.get_response(request)

        # Skip caching for admin and non-API endpoints
        if request.path.startswith('/admin') or not request.path.startswith('/api'):
            return self.get_response(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get response from cache
        cached_response = cache.get(cache_key)
        if cached_response:
            response = HttpResponse(
                cached_response['content'],
                content_type=cached_response['content_type'],
                status=cached_response['status_code']
            )
            response['X-Cache'] = 'HIT'
            return response

        # Get response from view
        response = self.get_response(request)

        # Only cache successful responses
        if response.status_code == 200:
            cache_data = {
                'content': response.content.decode('utf-8'),
                'content_type': response.get('Content-Type', 'application/json'),
                'status_code': response.status_code
            }
            
            # Cache for 5 minutes by default
            cache.set(cache_key, cache_data, 300)
            response['X-Cache'] = 'MISS'

        return response

    def _generate_cache_key(self, request):
        """Generate cache key from request"""
        key_data = {
            'path': request.path,
            'query_params': request.GET.dict(),
            'user_id': request.user.id if request.user.is_authenticated else None
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"api_cache:{key_hash}"


class ETagMiddleware:
    """
    Add ETag headers for caching
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only add ETags to GET requests with 200 status
        if request.method == 'GET' and response.status_code == 200:
            if hasattr(response, 'content'):
                etag = hashlib.md5(response.content).hexdigest()
                response['ETag'] = f'"{etag}"'
                
                # Check if client has matching ETag
                client_etag = request.META.get('HTTP_IF_NONE_MATCH')
                if client_etag == f'"{etag}"':
                    return HttpResponse(status=304)

        return response