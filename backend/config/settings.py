from pathlib import Path
from decouple import config
from datetime import timedelta
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'channels',
    'drf_yasg',

    # Local apps
    'users.apps.UsersConfig',
    'projects.apps.ProjectsConfig',
    'tasks.apps.TasksConfig',
    'collaboration.apps.CollaborationConfig',
    'integrations.apps.IntegrationsConfig',
    'analytics.apps.AnalyticsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'users.middleware.SecurityHeadersMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'config.middleware.ETagMiddleware',
    'users.middleware.RateLimitMiddleware',
    'users.sql_protection.SQLInjectionProtectionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'users.csrf_protection.SameSiteMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'users.csrf_protection.EnhancedCSRFMiddleware',
    'users.csrf_protection.DoubleSubmitCookieMiddleware',
    'users.csrf_protection.OriginValidationMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'users.middleware.TokenValidationMiddleware',
    'users.middleware.UserActivityMiddleware',
    'config.middleware.CacheMiddleware',
    'config.db_pool.DatabaseConnectionMiddleware',
    'config.monitoring.MiddlewarePerformanceMonitor',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=config('postgresql://postgres:hfGPdRsfgfCGSRDMqDOezXJmYwAFkXWC@postgres.railway.internal:5432/railway'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Cache Configuration
try:
    import redis
    redis_client = redis.from_url(config('REDIS_URL', default='redis://localhost:6379/1'))
    redis_client.ping()
    # Redis is available
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            },
            'KEY_PREFIX': 'management_hub',
            'TIMEOUT': 300,
        }
    }
except (redis.ConnectionError, redis.TimeoutError, ImportError, Exception):
    # Fallback to local memory cache for development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'management_hub_cache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
            }
        }
    }

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    config('FRONTEND_URL', default='http://localhost:3000'),
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = config('DEBUG', default=False, cast=bool)

# CSRF settings for API
CSRF_TRUSTED_ORIGINS = [
    config('FRONTEND_URL', default='http://localhost:3000'),
]

# Exempt API endpoints from CSRF (since we use JWT)
CSRF_EXEMPT_URLS = [
    r'^api/',
    r'^/api/',
]

# Additional CORS security settings
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",  # Allow Vercel deployments
    r"^https://.*\.netlify\.app$",  # Allow Netlify deployments
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = [
    'content-disposition',
    'x-pagination-count',
    'x-pagination-page',
    'x-pagination-per-page',
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session security
SESSION_COOKIE_SECURE = not config('DEBUG', default=False, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not config('DEBUG', default=False, cast=bool)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Additional security headers
if not config('DEBUG', default=False, cast=bool):
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Logging configuration for security monitoring
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# Channels
ASGI_APPLICATION = 'config.asgi.application'

# Try Redis for channels, fallback to in-memory
try:
    import redis
    redis_client = redis.from_url(config('REDIS_URL', default='redis://localhost:6379'))
    redis_client.ping()
    # Redis is available
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(config('REDIS_URL', default='redis://localhost:6379'))],
            },
        },
    }
except (redis.ConnectionError, redis.TimeoutError, ImportError, Exception):
    # Fallback to in-memory channel layer for development
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        },
    }

# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule for automated tasks
CELERY_BEAT_SCHEDULE = {
    'cleanup-websocket-data': {
        'task': 'collaboration.tasks.cleanup_websocket_data',
        'schedule': 300.0,  # Every 5 minutes
    },
    'websocket-health-check': {
        'task': 'collaboration.tasks.websocket_health_check',
        'schedule': 600.0,  # Every 10 minutes
    },
    'generate-websocket-metrics': {
        'task': 'collaboration.tasks.generate_websocket_metrics',
        'schedule': 900.0,  # Every 15 minutes
    },
    'optimize-message-history': {
        'task': 'collaboration.tasks.optimize_message_history',
        'schedule': 3600.0,  # Every hour
    },
    'send-task-deadline-reminders': {
        'task': 'tasks.tasks.send_task_deadline_reminders',
        'schedule': 86400.0,  # Daily
    },
    'cleanup-old-task-data': {
        'task': 'tasks.tasks.cleanup_old_task_data',
        'schedule': 604800.0,  # Weekly
    },
    'cleanup-expired-cache': {
        'task': 'projects.tasks.cleanup_expired_cache',
        'schedule': 7200.0,  # Every 2 hours
    },
}

# Static files configuration for Railway
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# User model
AUTH_USER_MODEL = 'users.User'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Add WhiteNoise for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Add health check URL
from django.http import JsonResponse
def health_check(request):
    return JsonResponse({'status': 'healthy'})

PORT = int(os.environ.get('PORT', 8000))