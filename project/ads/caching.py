from functools import wraps
from django.core.cache import cache
from django.db.models import QuerySet
import hashlib
import json
def cache_query(timeout=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f'{func.__module__}.{func.__name__}:{hashlib.md5(json.dump({'args':args, 'kwargs': kwargs}).encode()).hexdigest()}'
            
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data
            
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    
    return decorator

class CachedQuerySet(QuerySet):
    def __init__(self, model = None, query = None, using = None, hints = None):
        super().__init__(model, query, using, hints)
        self._cache_key = None
        
    def _get_cache_key(self):
        if not self._cache_key:
            query_string = str(self.query)
            self._cache_key = f'queryset:{hashlib.md5(query_string.encode()).hexdigest()}'
        
        return self._cache_key
    
    def get_from_cache(self, timeout=300):
        cache_key = self._get_cache_key()
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        result = list(self)
        cache.set(cache_key, result, timeout)
        
        return result