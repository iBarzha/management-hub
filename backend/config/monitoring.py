import time
import logging
import traceback
import psutil
from functools import wraps
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Performance monitoring utility
    """
    
    def __init__(self):
        self.metrics = {}
        self.slow_queries = []
        
    def record_metric(self, metric_name, value, tags=None):
        """Record a performance metric"""
        timestamp = timezone.now()
        metric_data = {
            'value': value,
            'timestamp': timestamp,
            'tags': tags or {}
        }
        
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append(metric_data)
        
        # Keep only last 1000 entries per metric
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def get_metrics(self, metric_name=None, since=None):
        """Get recorded metrics"""
        if metric_name:
            metrics = self.metrics.get(metric_name, [])
        else:
            metrics = self.metrics
        
        if since and metric_name:
            metrics = [m for m in metrics if m['timestamp'] > since]
        
        return metrics
    
    def record_slow_query(self, query, duration):
        """Record a slow database query"""
        query_data = {
            'query': str(query)[:500],  # Limit query length
            'duration': duration,
            'timestamp': timezone.now()
        }
        
        self.slow_queries.append(query_data)
        
        # Keep only last 100 slow queries
        if len(self.slow_queries) > 100:
            self.slow_queries = self.slow_queries[-100:]


# Global monitor instance
monitor = PerformanceMonitor()


def performance_tracker(metric_name=None, threshold=1.0):
    """
    Decorator to track function performance
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record metric
                name = metric_name or f"{func.__module__}.{func.__name__}"
                monitor.record_metric(f"function_execution:{name}", execution_time)
                
                # Log slow functions
                if execution_time > threshold:
                    logger.warning(f"Slow function {name}: {execution_time:.2f}s")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Function {func.__name__} failed after {execution_time:.2f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


class DatabaseQueryMonitor:
    """
    Monitor database query performance
    """
    
    def __init__(self, slow_query_threshold=0.5):
        self.slow_query_threshold = slow_query_threshold
        
    def __enter__(self):
        self.queries_before = len(connection.queries)
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        queries_after = len(connection.queries)
        query_count = queries_after - self.queries_before
        
        # Record metrics
        monitor.record_metric('database_queries', query_count)
        monitor.record_metric('database_time', execution_time)
        
        # Check for slow queries
        if execution_time > self.slow_query_threshold:
            recent_queries = connection.queries[self.queries_before:]
            for query in recent_queries:
                query_time = float(query['time'])
                if query_time > self.slow_query_threshold:
                    monitor.record_slow_query(query['sql'], query_time)
        
        # Log performance info
        if query_count > 10 or execution_time > 1.0:
            logger.info(f"Database operation: {query_count} queries in {execution_time:.2f}s")


def get_system_metrics():
    """
    Get system performance metrics
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database connection info
        db_connections = 0
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
                db_connections = cursor.fetchone()[0]
        except Exception:
            pass
        
        # Cache info
        try:
            cache_stats = cache.get('cache_stats', {})
        except Exception:
            cache_stats = {}
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3),
            'database_connections': db_connections,
            'cache_stats': cache_stats,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        return {'error': str(e)}


class MiddlewarePerformanceMonitor:
    """
    Middleware to monitor request performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        start_time = time.time()
        
        # Record request start
        request._monitor_start = start_time
        
        # Get response
        response = self.get_response(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Record metrics
        monitor.record_metric('request_duration', response_time, {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code
        })
        
        # Add performance headers
        response['X-Response-Time'] = f"{response_time:.3f}s"
        
        # Log slow requests
        if response_time > 2.0:
            logger.warning(f"Slow request: {request.method} {request.path} took {response_time:.2f}s")
        
        return response


@require_http_methods(["GET"])
@cache_page(60)  # Cache for 1 minute
def health_check(request):
    """
    Health check endpoint with performance metrics
    """
    try:
        # Basic health checks
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': getattr(settings, 'VERSION', '1.0.0')
        }
        
        # Database health
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                health_data['database'] = 'healthy'
        except Exception as e:
            health_data['database'] = f'error: {str(e)}'
            health_data['status'] = 'unhealthy'
        
        # Cache health
        try:
            cache.set('health_check', 'ok', 10)
            cache_result = cache.get('health_check')
            health_data['cache'] = 'healthy' if cache_result == 'ok' else 'unhealthy'
        except Exception as e:
            health_data['cache'] = f'error: {str(e)}'
            health_data['status'] = 'unhealthy'
        
        # System metrics
        health_data['system'] = get_system_metrics()
        
        # Performance metrics summary
        recent_requests = monitor.get_metrics('request_duration', 
                                             since=timezone.now() - timedelta(minutes=5))
        
        if recent_requests:
            response_times = [m['value'] for m in recent_requests]
            health_data['performance'] = {
                'avg_response_time': sum(response_times) / len(response_times),
                'max_response_time': max(response_times),
                'request_count_5min': len(response_times)
            }
        
        return JsonResponse(health_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
def performance_metrics(request):
    """
    Endpoint to get detailed performance metrics
    """
    try:
        # Get time range from query params
        hours = int(request.GET.get('hours', 1))
        since = timezone.now() - timedelta(hours=hours)
        
        # Collect metrics
        metrics_data = {
            'request_metrics': monitor.get_metrics('request_duration', since=since),
            'database_metrics': monitor.get_metrics('database_time', since=since),
            'function_metrics': {
                name: metrics for name, metrics in monitor.metrics.items()
                if name.startswith('function_execution:')
            },
            'slow_queries': [
                q for q in monitor.slow_queries
                if q['timestamp'] > since
            ],
            'system_metrics': get_system_metrics(),
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(metrics_data)
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def profile_code(func):
    """
    Decorator for detailed code profiling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        import cProfile
        import pstats
        from io import StringIO
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
        finally:
            profiler.disable()
            
            # Generate profile stats
            stats_stream = StringIO()
            stats = pstats.Stats(profiler, stream=stats_stream)
            stats.sort_stats('cumulative').print_stats(20)
            
            # Log profile results
            logger.info(f"Profile for {func.__name__}:\n{stats_stream.getvalue()}")
        
        return result
    
    return wrapper


class APIPerformanceMonitor:
    """
    Monitor API endpoint performance
    """
    
    @staticmethod
    def track_api_call(endpoint, method, response_time, status_code):
        """Track API call performance"""
        cache_key = f"api_performance:{endpoint}:{method}"
        
        # Get existing data
        data = cache.get(cache_key, {
            'call_count': 0,
            'total_time': 0,
            'avg_time': 0,
            'max_time': 0,
            'min_time': float('inf'),
            'error_count': 0
        })
        
        # Update metrics
        data['call_count'] += 1
        data['total_time'] += response_time
        data['avg_time'] = data['total_time'] / data['call_count']
        data['max_time'] = max(data['max_time'], response_time)
        data['min_time'] = min(data['min_time'], response_time)
        
        if status_code >= 400:
            data['error_count'] += 1
        
        # Cache updated data
        cache.set(cache_key, data, 3600)  # Cache for 1 hour
    
    @staticmethod
    def get_api_stats(endpoint=None):
        """Get API performance statistics"""
        if endpoint:
            pattern = f"api_performance:{endpoint}:*"
        else:
            pattern = "api_performance:*"
        
        keys = cache.keys(pattern)
        stats = {}
        
        for key in keys:
            data = cache.get(key)
            if data:
                stats[key] = data
        
        return stats


# Context managers for performance monitoring
class monitor_database_queries:
    """Context manager to monitor database queries"""
    def __enter__(self):
        return DatabaseQueryMonitor().__enter__()
    
    def __exit__(self, *args):
        return DatabaseQueryMonitor().__exit__(*args)


class monitor_cache_operations:
    """Context manager to monitor cache operations"""
    def __init__(self):
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            monitor.record_metric('cache_operation_time', duration)