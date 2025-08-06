from functools import wraps
from django.core.cache import cache
from django.conf import settings
import hashlib
import json


def cache_key_generator(prefix, *args, **kwargs):
    """
    Generate a cache key based on function arguments
    """
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return f"{prefix}:{key_hash}"


def cache_result(timeout=300, key_prefix='default'):
    """
    Decorator to cache function results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_key_generator(f"{key_prefix}:{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidate all cache keys matching a pattern
    """
    cache.delete_many(cache.keys(f"*{pattern}*"))


def get_user_cache_key(user_id, resource_type, resource_id=None):
    """
    Generate standardized cache keys for user-related data
    """
    if resource_id:
        return f"user:{user_id}:{resource_type}:{resource_id}"
    return f"user:{user_id}:{resource_type}"


class CacheManager:
    """
    Centralized cache management for the application
    """
    
    @staticmethod
    def get_projects_cache_key(user_id):
        return f"projects:user:{user_id}"
    
    @staticmethod
    def get_tasks_cache_key(user_id, project_id=None):
        if project_id:
            return f"tasks:user:{user_id}:project:{project_id}"
        return f"tasks:user:{user_id}"
    
    @staticmethod
    def get_team_cache_key(user_id):
        return f"teams:user:{user_id}"
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries for a user"""
        patterns = [
            f"user:{user_id}:*",
            f"projects:user:{user_id}*",
            f"tasks:user:{user_id}*",
            f"teams:user:{user_id}*"
        ]
        
        for pattern in patterns:
            keys = cache.keys(pattern)
            if keys:
                cache.delete_many(keys)
    
    @staticmethod
    def invalidate_project_cache(project_id):
        """Invalidate cache entries related to a project"""
        patterns = [
            f"*:project:{project_id}*",
            f"tasks:*:project:{project_id}*"
        ]
        
        for pattern in patterns:
            keys = cache.keys(pattern)
            if keys:
                cache.delete_many(keys)