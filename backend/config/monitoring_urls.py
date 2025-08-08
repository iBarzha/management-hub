from django.urls import path
from .monitoring import health_check, performance_metrics

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('metrics/', performance_metrics, name='performance_metrics'),
]