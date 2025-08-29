from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import redis
from django.conf import settings


@require_http_methods(["GET"])
def health_check(request):
    try:
        # Test database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Test Redis connection
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()

        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'redis': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)