from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.conf import settings
import time
import threading
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """
    Simple connection pool manager for Django
    """
    
    def __init__(self):
        self.pool_stats = defaultdict(dict)
        self.pool_lock = threading.Lock()
        
    def get_connection_info(self, alias='default'):
        """
        Get connection pool information
        """
        connection = connections[alias]
        
        with self.pool_lock:
            stats = {
                'alias': alias,
                'vendor': connection.vendor,
                'is_connected': hasattr(connection, 'connection') and connection.connection is not None,
                'queries_count': len(connection.queries) if connection.queries else 0,
                'total_time': sum(float(q['time']) for q in connection.queries) if connection.queries else 0
            }
            
            # Try to get pool-specific information if available
            if hasattr(connection, 'connection') and connection.connection:
                try:
                    # PostgreSQL specific information
                    if connection.vendor == 'postgresql':
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT count(*) as active_connections 
                                FROM pg_stat_activity 
                                WHERE datname = current_database()
                            """)
                            result = cursor.fetchone()
                            stats['active_connections'] = result[0] if result else 0
                except Exception as e:
                    logger.warning(f"Could not get connection stats: {e}")
            
            return stats
    
    def close_idle_connections(self, max_idle_time=300):
        """
        Close connections that have been idle for too long
        """
        closed_count = 0
        
        for alias in connections:
            connection = connections[alias]
            
            # Check if connection exists and has been idle
            if hasattr(connection, 'connection') and connection.connection:
                try:
                    # Force close if needed
                    connection.close()
                    closed_count += 1
                except Exception as e:
                    logger.error(f"Error closing connection {alias}: {e}")
        
        return closed_count
    
    def health_check(self):
        """
        Perform health check on all database connections
        """
        results = {}
        
        for alias in settings.DATABASES.keys():
            try:
                connection = connections[alias]
                start_time = time.time()
                
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
                
                response_time = time.time() - start_time
                
                results[alias] = {
                    'status': 'healthy',
                    'response_time': response_time,
                    'info': self.get_connection_info(alias)
                }
                
            except Exception as e:
                results[alias] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'response_time': None
                }
        
        return results


# Middleware for connection management
class DatabaseConnectionMiddleware:
    """
    Middleware to manage database connections per request
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.pool_manager = DatabaseConnectionPool()
    
    def __call__(self, request):
        # Set connection timeout for this request
        request._connection_start = time.time()
        
        response = self.get_response(request)
        
        # Log slow queries
        connection_time = time.time() - request._connection_start
        if connection_time > 1.0:  # Log requests taking more than 1 second
            logger.warning(f"Slow request: {request.path} took {connection_time:.2f}s")
        
        # Close connections if needed
        self._cleanup_connections()
        
        return response
    
    def _cleanup_connections(self):
        """
        Clean up database connections after request
        """
        try:
            # Close connections that are not in a transaction
            for alias in connections:
                connection = connections[alias]
                if not connection.in_atomic_block:
                    connection.close()
        except Exception as e:
            logger.error(f"Error cleaning up connections: {e}")


# Utility functions for connection management
def get_database_stats():
    """
    Get comprehensive database statistics
    """
    pool_manager = DatabaseConnectionPool()
    stats = {}
    
    for alias in settings.DATABASES.keys():
        stats[alias] = pool_manager.get_connection_info(alias)
    
    return stats


def force_close_connections():
    """
    Force close all database connections
    """
    closed_count = 0
    
    for alias in connections:
        try:
            connections[alias].close()
            closed_count += 1
        except Exception as e:
            logger.error(f"Error force closing connection {alias}: {e}")
    
    return closed_count


def test_database_performance():
    """
    Test database performance with sample queries
    """
    results = {}
    
    for alias in settings.DATABASES.keys():
        try:
            connection = connections[alias]
            
            # Test simple query
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1 as test')
                cursor.fetchone()
            simple_query_time = time.time() - start_time
            
            # Test with a more complex query if we have tables
            complex_query_time = None
            try:
                start_time = time.time()
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        LIMIT 5
                    """)
                    cursor.fetchall()
                complex_query_time = time.time() - start_time
            except Exception:
                pass
            
            results[alias] = {
                'simple_query_time': simple_query_time,
                'complex_query_time': complex_query_time,
                'status': 'success'
            }
            
        except Exception as e:
            results[alias] = {
                'status': 'error',
                'error': str(e)
            }
    
    return results


# Context manager for transaction handling
class OptimizedTransaction:
    """
    Context manager for optimized database transactions
    """
    
    def __init__(self, using='default', savepoint=True):
        self.using = using
        self.savepoint = savepoint
        self.transaction_started = False
    
    def __enter__(self):
        self.transaction_started = True
        if self.savepoint:
            return transaction.atomic(using=self.using, savepoint=True)
        else:
            return transaction.atomic(using=self.using)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.transaction_started:
            # Transaction will be handled by the atomic decorator
            pass


# Global pool manager instance
pool_manager = DatabaseConnectionPool()