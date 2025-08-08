from django.db import models
from django.core.cache import cache
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class LazyQuerySet(models.QuerySet):
    """
    Custom QuerySet with lazy loading capabilities
    """
    
    def with_lazy_loading(self, field_mapping=None):
        """
        Enable lazy loading for specified fields
        field_mapping: dict of field names to lazy loading functions
        """
        self._lazy_field_mapping = field_mapping or {}
        return self
    
    def iterator(self, chunk_size=2000):
        """
        Override iterator to process in smaller chunks for memory efficiency
        """
        for chunk in super().iterator(chunk_size=chunk_size):
            yield chunk


class LazyManager(models.Manager):
    """
    Custom manager with lazy loading capabilities
    """
    
    def get_queryset(self):
        return LazyQuerySet(self.model, using=self._db)
    
    def with_lazy_fields(self, **field_mappings):
        """
        Return queryset with lazy field loading
        """
        return self.get_queryset().with_lazy_loading(field_mappings)


def lazy_property(cache_key_func=None, timeout=300):
    """
    Decorator for lazy loading of model properties
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(self)
            else:
                cache_key = f"{self.__class__.__name__}_{self.pk}_{func.__name__}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute value
            result = func(self)
            
            # Cache the result
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator


def batch_load_related(queryset, related_fields, batch_size=1000):
    """
    Batch load related fields to optimize N+1 queries
    """
    if not related_fields:
        return queryset
    
    # Use prefetch_related for reverse ForeignKey relationships
    # Use select_related for forward ForeignKey relationships
    select_fields = []
    prefetch_fields = []
    
    for field in related_fields:
        if '__' in field or hasattr(queryset.model, field):
            # Check if it's a forward or reverse relationship
            try:
                field_obj = queryset.model._meta.get_field(field.split('__')[0])
                if isinstance(field_obj, (models.ForeignKey, models.OneToOneField)):
                    select_fields.append(field)
                else:
                    prefetch_fields.append(field)
            except models.FieldDoesNotExist:
                prefetch_fields.append(field)
        else:
            prefetch_fields.append(field)
    
    if select_fields:
        queryset = queryset.select_related(*select_fields)
    if prefetch_fields:
        queryset = queryset.prefetch_related(*prefetch_fields)
    
    return queryset


class DeferredLoader:
    """
    Utility for deferred loading of heavy fields
    """
    
    @staticmethod
    def defer_heavy_fields(queryset, heavy_fields=None):
        """
        Defer loading of heavy fields like TextField, ImageField, etc.
        """
        if heavy_fields is None:
            heavy_fields = []
            for field in queryset.model._meta.fields:
                if isinstance(field, (models.TextField, models.ImageField, 
                                     models.FileField, models.BinaryField)):
                    heavy_fields.append(field.name)
        
        return queryset.defer(*heavy_fields)
    
    @staticmethod
    def only_required_fields(queryset, required_fields):
        """
        Only load required fields
        """
        return queryset.only(*required_fields)


def lazy_load_method(timeout=300):
    """
    Decorator for methods that should be lazily loaded and cached
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create cache key from method name and arguments
            cache_key = f"{self.__class__.__name__}_{self.pk}_{func.__name__}"
            if args or kwargs:
                import hashlib
                import json
                args_hash = hashlib.md5(
                    json.dumps([str(arg) for arg in args] + 
                              [f"{k}:{v}" for k, v in sorted(kwargs.items())]).encode()
                ).hexdigest()[:8]
                cache_key += f"_{args_hash}"
            
            # Try cache first
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute method
            result = func(self, *args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator


class AsyncQuerySetMixin:
    """
    Mixin to add async capabilities to QuerySets
    """
    
    def schedule_async_operation(self, operation_name, *args, **kwargs):
        """
        Schedule an async operation on this queryset
        """
        from celery import current_app
        
        # Get primary keys to process
        pks = list(self.values_list('pk', flat=True))
        
        # Schedule the task
        task = current_app.send_task(
            f'async_queryset.{operation_name}',
            args=[self.model._meta.label_lower, pks] + list(args),
            kwargs=kwargs
        )
        
        return task.id


def optimize_queryset_for_api(queryset, fields_to_include=None, 
                              related_fields=None, defer_fields=None):
    """
    Comprehensive queryset optimization for API responses
    """
    # Apply field selection
    if fields_to_include:
        queryset = queryset.only(*fields_to_include)
    
    # Apply deferred loading
    if defer_fields:
        queryset = queryset.defer(*defer_fields)
    
    # Apply related field optimization
    if related_fields:
        queryset = batch_load_related(queryset, related_fields)
    
    # Add distinct to prevent duplicates
    queryset = queryset.distinct()
    
    return queryset


# Example usage in models:
class OptimizedModelMixin(models.Model):
    """
    Mixin to add optimization methods to models
    """
    
    objects = LazyManager()
    
    class Meta:
        abstract = True
    
    @lazy_property(timeout=600)
    def expensive_calculation(self):
        """
        Example of an expensive calculation that should be cached
        """
        # Placeholder for expensive operation
        return sum(range(1000))
    
    @lazy_load_method(timeout=300)
    def get_related_summary(self):
        """
        Example of a method that fetches related data
        """
        # This would be cached after first execution
        return {"count": 0, "summary": "cached data"}