from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from .health import health_check

schema_view = get_schema_view(
    openapi.Info(
        title="Project Management API",
        default_version='v1',
        description="API for Project Management Hub",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # API routes
    path('api/auth/', include('users.urls')),
    path('api/', include('projects.urls')),
    path('api/', include('tasks.urls')),
    path('api/collaboration/', include('collaboration.urls')),
    path('api/integrations/', include('integrations.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/monitoring/', include('config.monitoring_urls')),
    path('api/health/', health_check, name='health_check'),
    # Direct routes for frontend compatibility
    path('auth/', include('users.urls')),
    path('collaboration/', include('collaboration.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]