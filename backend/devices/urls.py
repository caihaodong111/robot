from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'devices'

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r'devices', views.DeviceViewSet, basename='device')

urlpatterns = [
    path('', include(router.urls)),
    path('devices/<int:pk>/toggle-status/', views.DeviceToggleStatusView.as_view(), name='device-toggle-status'),
]
