import re
import html
import bleach
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class InputSanitizer:
    """Utility class for input sanitization and validation."""
    
    # Allowed HTML tags for rich text content
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'code', 'pre', 'a', 'img'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
        '*': ['class']
    }
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'onfocus\s*=',
        r'onblur\s*=',
        r'onchange\s*=',
        r'onsubmit\s*=',
        r'<iframe.*?>.*?</iframe>',
        r'<object.*?>.*?</object>',
        r'<embed.*?>.*?</embed>',
        r'<form.*?>.*?</form>',
    ]
    
    @classmethod
    def sanitize_html(cls, text):
        """Sanitize HTML content to prevent XSS attacks."""
        if not text:
            return text
            
        # First pass: Remove dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Second pass: Use bleach to clean HTML
        cleaned = bleach.clean(
            text,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True,
            strip_comments=True
        )
        
        return cleaned
    
    @classmethod
    def sanitize_text(cls, text):
        """Sanitize plain text input."""
        if not text:
            return text
            
        # HTML escape to prevent XSS
        text = html.escape(text)
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Limit length to prevent DoS
        if len(text) > 10000:
            text = text[:10000]
            
        return text.strip()
    
    @classmethod
    def validate_email(cls, email):
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(_('Enter a valid email address.'))
        return email.lower().strip()
    
    @classmethod
    def validate_username(cls, username):
        """Validate username format."""
        if not username:
            raise ValidationError(_('Username is required.'))
            
        # Allow only alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError(_('Username can only contain letters, numbers, underscores, and hyphens.'))
            
        if len(username) < 3 or len(username) > 30:
            raise ValidationError(_('Username must be between 3 and 30 characters.'))
            
        return username.strip()
    
    @classmethod
    def validate_url(cls, url):
        """Validate URL format."""
        if not url:
            return url
            
        url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        if not re.match(url_pattern, url):
            raise ValidationError(_('Enter a valid URL.'))
            
        return url.strip()
    
    @classmethod
    def sanitize_filename(cls, filename):
        """Sanitize filename to prevent directory traversal."""
        if not filename:
            return filename
            
        # Remove directory traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
            
        return filename.strip()


class CustomValidationMixin:
    """Mixin for adding custom validation to serializers."""
    
    def validate_text_field(self, value, field_name='field', max_length=1000):
        """Validate and sanitize text fields."""
        if value is None:
            return value
            
        # Sanitize the input
        sanitized = InputSanitizer.sanitize_text(value)
        
        # Check length
        if len(sanitized) > max_length:
            raise serializers.ValidationError(
                f'{field_name} must be less than {max_length} characters.'
            )
            
        return sanitized
    
    def validate_html_field(self, value, field_name='field', max_length=5000):
        """Validate and sanitize HTML fields."""
        if value is None:
            return value
            
        # Sanitize HTML
        sanitized = InputSanitizer.sanitize_html(value)
        
        # Check length
        if len(sanitized) > max_length:
            raise serializers.ValidationError(
                f'{field_name} must be less than {max_length} characters.'
            )
            
        return sanitized
    
    def validate_email_field(self, value):
        """Validate email field."""
        if value is None:
            return value
            
        return InputSanitizer.validate_email(value)
    
    def validate_url_field(self, value):
        """Validate URL field."""
        if value is None:
            return value
            
        return InputSanitizer.validate_url(value)


class SecureFileValidator:
    """Validator for file uploads."""
    
    ALLOWED_EXTENSIONS = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
        'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
        'archive': ['.zip', '.tar', '.gz'],
        'code': ['.py', '.js', '.html', '.css', '.json', '.xml']
    }
    
    DANGEROUS_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.php', '.asp', '.jsp', '.sh', '.ps1', '.msi', '.dll'
    ]
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def validate_file(cls, file):
        """Validate uploaded file."""
        if not file:
            return file
        
        # Check file size first to prevent large file processing
        if file.size > cls.MAX_FILE_SIZE:
            raise ValidationError(f'File size must be less than {cls.MAX_FILE_SIZE // (1024*1024)}MB.')
        
        # Check for minimum file size (prevent empty files)
        if file.size < 1:
            raise ValidationError('Empty files are not allowed.')
        
        # Sanitize filename
        original_name = file.name
        filename = InputSanitizer.sanitize_filename(file.name)
        
        # Validate filename length
        if len(filename) > 255:
            raise ValidationError('Filename is too long.')
        
        # Check for dangerous extensions
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{ext}' in cls.DANGEROUS_EXTENSIONS:
            raise ValidationError('This file type is not allowed.')
        
        # Validate file content with size limit for reading
        cls._validate_file_content_secure(file)
        
        # Update file name if it was sanitized
        if filename != original_name:
            file.name = filename
        
        return file
    
    @classmethod
    def _validate_file_content_secure(cls, file):
        """Secure file content validation with size limits."""
        try:
            # Limit how much we read for security
            max_header_size = min(2048, file.size)
            
            file.seek(0)
            file_header = file.read(max_header_size)
            file.seek(0)
            
            # Check for executable signatures first
            if cls._has_dangerous_signature(file_header):
                raise ValidationError('File contains dangerous content.')
            
            # Try magic library if available
            try:
                import magic
                mime_type = magic.from_buffer(file_header, mime=True)
                cls._validate_mime_type(file.name, mime_type)
            except ImportError:
                # Use fallback validation
                cls._validate_file_content_fallback_secure(file, file_header)
                
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            # Any other error during validation should be treated as suspicious
            raise ValidationError('Unable to validate file content.')
    
    @classmethod
    def _has_dangerous_signature(cls, file_header):
        """Check for dangerous file signatures."""
        dangerous_signatures = [
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
            b'PK\x03\x04',  # ZIP (could contain executables)
            b'\x1f\x8b\x08',  # GZIP
            b'Rar!',  # RAR archive
        ]
        
        for sig in dangerous_signatures:
            if file_header.startswith(sig):
                return True
        return False
    
    @classmethod
    def _validate_mime_type(cls, filename, mime_type):
        """Validate MIME type against filename extension."""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        expected_mimes = cls._get_expected_mime_types(extension)
        
        # Allow common safe MIME types
        safe_mime_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'text/plain', 'application/json', 'text/csv',
            'application/pdf'  # Only if explicitly allowed
        ]
        
        if expected_mimes and mime_type not in expected_mimes:
            raise ValidationError('File content does not match its extension.')
        
        if mime_type not in safe_mime_types:
            raise ValidationError(f'MIME type {mime_type} is not allowed.')
    
    @classmethod
    def _validate_file_content_fallback_secure(cls, file, file_header):
        """Enhanced fallback validation without python-magic library."""
        extension = file.name.lower().split('.')[-1] if '.' in file.name else ''
        
        # Strict whitelist for fallback mode
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'txt', 'csv']
        if extension not in allowed_extensions:
            raise ValidationError('Only image and text files are allowed in fallback mode.')
        
        # Check file signatures for allowed types
        image_signatures = {
            'jpg': [b'\xff\xd8\xff'],
            'jpeg': [b'\xff\xd8\xff'],
            'png': [b'\x89PNG\r\n\x1a\n'],
            'gif': [b'GIF87a', b'GIF89a']
        }
        
        if extension in image_signatures:
            valid_signature = False
            for sig in image_signatures[extension]:
                if file_header.startswith(sig):
                    valid_signature = True
                    break
            
            if not valid_signature:
                raise ValidationError(f'Invalid {extension.upper()} file format.')
    
    @classmethod
    def _validate_file_content(cls, file):
        """Validate file content by checking MIME type."""
        try:
            import magic
            # Read first few bytes to detect file type
            file.seek(0)
            file_header = file.read(1024)
            file.seek(0)
            
            # Use python-magic to detect actual file type
            mime_type = magic.from_buffer(file_header, mime=True)
            
            # Check if MIME type matches extension
            extension = file.name.lower().split('.')[-1] if '.' in file.name else ''
            expected_mimes = cls._get_expected_mime_types(extension)
            
            if expected_mimes and mime_type not in expected_mimes:
                raise ValidationError('File content does not match its extension.')
                
        except ImportError:
            # python-magic not available, use alternative validation
            cls._validate_file_content_fallback(file)
        except Exception:
            # Magic library error, use fallback validation
            cls._validate_file_content_fallback(file)
    
    @classmethod
    def _validate_file_content_fallback(cls, file):
        """Fallback validation without python-magic library."""
        # Read first few bytes to check for dangerous file signatures
        file.seek(0)
        file_header = file.read(20)
        file.seek(0)
        
        # Check for common dangerous file signatures
        dangerous_signatures = [
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
            b'%PDF-',  # PDF (can contain JS)
            b'\x89PNG',  # PNG (allow)
            b'\xff\xd8\xff',  # JPEG (allow)
            b'GIF87a',  # GIF (allow)
            b'GIF89a',  # GIF (allow)
        ]
        
        # Only allow safe file types in fallback mode
        safe_signatures = [
            b'\x89PNG',  # PNG
            b'\xff\xd8\xff',  # JPEG  
            b'GIF87a',  # GIF
            b'GIF89a',  # GIF
        ]
        
        # Check if file starts with executable signatures
        for sig in [b'MZ', b'\x7fELF']:
            if file_header.startswith(sig):
                raise ValidationError('Executable files are not allowed.')
        
        # For non-image files, perform additional checks
        extension = file.name.lower().split('.')[-1] if '.' in file.name else ''
        if extension in ['exe', 'bat', 'cmd', 'scr', 'com', 'pif']:
            raise ValidationError('This file type is not allowed for security reasons.')
    
    @classmethod
    def _get_expected_mime_types(cls, extension):
        """Get expected MIME types for file extension."""
        mime_map = {
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'png': ['image/png'],
            'gif': ['image/gif'],
            'pdf': ['application/pdf'],
            'txt': ['text/plain'],
            'json': ['application/json', 'text/plain'],
            'xml': ['application/xml', 'text/xml'],
        }
        return mime_map.get(extension, [])


class SQLInjectionValidator:
    """Validator to detect potential SQL injection attempts."""
    
    SQL_INJECTION_PATTERNS = [
        r'(\bUNION\b.*\bSELECT\b)',
        r'(\bSELECT\b.*\bFROM\b)',
        r'(\bINSERT\b.*\bINTO\b)',
        r'(\bUPDATE\b.*\bSET\b)',
        r'(\bDELETE\b.*\bFROM\b)',
        r'(\bDROP\b.*\bTABLE\b)',
        r'(\bCREATE\b.*\bTABLE\b)',
        r'(\bALTER\b.*\bTABLE\b)',
        r'(\bEXEC\b|\bEXECUTE\b)',
        r'(\bSP_\w+)',
        r'(--|\#|/\*|\*/)',
        r'(\bOR\b.*=.*\bOR\b)',
        r'(\bAND\b.*=.*\bAND\b)',
        r'(1=1|1=0)',
        r'(\'\s*OR\s*\')',
        r'(\'\s*AND\s*\')',
    ]
    
    @classmethod
    def validate_input(cls, value):
        """Check input for SQL injection patterns."""
        if not value or not isinstance(value, str):
            return value
            
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError('Invalid input detected.')
                
        return value