from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'monitoring'

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r'data', views.SensorDataViewSet, basename='sensordata')

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.DataUploadView.as_view(), name='data-upload'),
    path('query/', views.DataQueryView.as_view(), name='data-query'),
    path('export/', views.DataExportView.as_view(), name='data-export'),
    path('realtime/<int:device_id>/', views.RealTimeDataView.as_view(), name='realtime-data'),
    path('statistics/<int:device_id>/', views.DataStatisticsView.as_view(), name='data-statistics'),
]
