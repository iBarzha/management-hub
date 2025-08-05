import logging
import re
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """Middleware to detect and prevent SQL injection attempts."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('security')
        
        # SQL injection patterns to detect
        self.sql_patterns = [
            # Union-based attacks
            r'(\bUNION\b.*\bSELECT\b)',
            r'(\bUNION\b.*\bALL\b.*\bSELECT\b)',
            
            # Boolean-based blind attacks
            r'(\bOR\b.*1\s*=\s*1)',
            r'(\bAND\b.*1\s*=\s*1)',
            r'(\bOR\b.*1\s*=\s*0)',
            r'(\bAND\b.*1\s*=\s*0)',
            r'(\'\s*OR\s*\'1\'\s*=\s*\'1)',
            r'(\'\s*AND\s*\'1\'\s*=\s*\'1)',
            
            # Time-based blind attacks
            r'(\bSLEEP\s*\()',
            r'(\bWAITFOR\b.*\bDELAY\b)',
            r'(\bBENCHMARK\s*\()',
            r'(\bPG_SLEEP\s*\()',
            
            # Error-based attacks
            r'(\bCONVERT\s*\([^)]*,.*\bINT\b)',
            r'(\bCAST\s*\([^)]*\s+AS\s+\bINT\b)',
            r'(\bEXTRACTVALUE\s*\()',
            r'(\bUPDATEXML\s*\()',
            
            # Stacked queries
            r'(;\s*SELECT\b)',
            r'(;\s*INSERT\b)',
            r'(;\s*UPDATE\b)',
            r'(;\s*DELETE\b)',
            r'(;\s*DROP\b)',
            r'(;\s*CREATE\b)',
            r'(;\s*ALTER\b)',
            
            # System functions
            r'(\bLOAD_FILE\s*\()',
            r'(\bINTO\s+OUTFILE\b)',
            r'(\bINTO\s+DUMPFILE\b)',
            r'(\bxp_cmdshell\b)',
            r'(\bsp_executesql\b)',
            
            # Comments for evasion
            r'(/\*.*\*/)',
            r'(--[^\r\n]*)',
            r'(#[^\r\n]*)',
            
            # Database-specific functions
            r'(\bSYSTEM_USER\s*\(\))',
            r'(\bUSER\s*\(\))',
            r'(\bDATABASE\s*\(\))',
            r'(\bVERSION\s*\(\))',
            r'(\b@@VERSION\b)',
            r'(\b@@SPID\b)',
            
            # String manipulation for evasion
            r'(\bCHAR\s*\([0-9,\s]+\))',
            r'(\bCONCAT\s*\()',
            r'(\bSUBSTRING\s*\()',
            
            # Advanced evasion techniques
            r'(\bIF\s*\([^)]*,.*,.*\))',
            r'(\bCASE\s+WHEN\b)',
            r'(\bEXISTS\s*\(\s*SELECT\b)',
        ]
        
        # Compile patterns for better performance
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL) 
            for pattern in self.sql_patterns
        ]
        
        super().__init__(get_response)
    
    def process_request(self, request):
        """Check request for SQL injection attempts."""
        # Skip static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None
            
        # Check query parameters
        if self._check_sql_injection(request.GET):
            return self._block_request(request, 'query parameters')
            
        # Check POST data
        if hasattr(request, 'POST') and self._check_sql_injection(request.POST):
            return self._block_request(request, 'POST data')
            
        # Check JSON body for API requests
        if request.content_type == 'application/json':
            try:
                import json
                if hasattr(request, 'body') and request.body:
                    json_data = json.loads(request.body.decode('utf-8'))
                    if self._check_json_for_sql_injection(json_data):
                        return self._block_request(request, 'JSON body')
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
                
        return None
    
    def _check_sql_injection(self, data_dict):
        """Check dictionary data for SQL injection patterns."""
        for key, values in data_dict.items():
            # Handle both single values and lists
            if not isinstance(values, list):
                values = [values]
                
            for value in values:
                if isinstance(value, str) and self._contains_sql_injection(value):
                    return True
        return False
    
    def _check_json_for_sql_injection(self, data):
        """Recursively check JSON data for SQL injection patterns."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and self._contains_sql_injection(value):
                    return True
                elif isinstance(value, (dict, list)):
                    if self._check_json_for_sql_injection(value):
                        return True
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str) and self._contains_sql_injection(item):
                    return True
                elif isinstance(item, (dict, list)):
                    if self._check_json_for_sql_injection(item):
                        return True
        elif isinstance(data, str):
            return self._contains_sql_injection(data)
            
        return False
    
    def _contains_sql_injection(self, value):
        """Check if a string contains SQL injection patterns."""
        if not value or len(value) > 10000:  # Skip very long strings
            return False
            
        # Check against compiled patterns
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                return True
                
        return False
    
    def _block_request(self, request, source):
        """Block request and log security event."""
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        self.logger.warning(
            f"SQL injection attempt blocked from {client_ip} "
            f"(user: {user_id}) in {source} on path: {request.path}"
        )
        
        return JsonResponse({
            'error': 'Invalid request detected',
            'detail': 'Your request contains potentially malicious content.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DatabaseQueryMonitor:
    """Monitor database queries for suspicious patterns."""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.suspicious_patterns = [
            r'SELECT.*FROM.*information_schema',
            r'SELECT.*FROM.*mysql\.user',
            r'SELECT.*FROM.*pg_user',
            r'UNION.*SELECT.*NULL',
            r'ORDER BY.*[0-9]+',
            r'GROUP BY.*[0-9]+',
            r'HAVING.*[0-9]+.*=.*[0-9]+',
        ]
        
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.suspicious_patterns
        ]
    
    def check_query(self, sql, params=None):
        """Check if a SQL query is suspicious."""
        if not sql:
            return False
            
        # Check for suspicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(sql):
                self.logger.warning(f"Suspicious SQL query detected: {sql[:200]}...")
                return True
                
        # Check for unusual parameter patterns
        if params:
            for param in params:
                if isinstance(param, str) and len(param) > 1000:
                    self.logger.warning(f"Unusually long SQL parameter: {len(param)} characters")
                    return True
                    
        return False


# Database connection wrapper for additional monitoring
class SecureDatabaseWrapper:
    """Wrapper for database connections to add security monitoring."""
    
    def __init__(self, connection):
        self.connection = connection
        self.monitor = DatabaseQueryMonitor()
    
    def execute(self, sql, params=None):
        """Execute SQL with security monitoring."""
        # Monitor the query
        self.monitor.check_query(sql, params)
        
        # Execute the original query
        return self.connection.execute(sql, params)
    
    def executemany(self, sql, param_list):
        """Execute many SQL statements with monitoring."""
        # Monitor the query
        self.monitor.check_query(sql, param_list[0] if param_list else None)
        
        # Execute the original query
        return self.connection.executemany(sql, param_list)


# Custom database backend for additional security
def get_secure_database_wrapper():
    """Get a secure database wrapper."""
    from django.db import connection
    return SecureDatabaseWrapper(connection)