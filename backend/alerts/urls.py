from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'alerts'

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r'rules', views.AlertRuleViewSet, basename='alertrule')
router.register(r'records', views.AlertRecordViewSet, basename='alertrecord')

urlpatterns = [
    path('', include(router.urls)),
    path('records/<int:pk>/acknowledge/', views.AlertAcknowledgeView.as_view(), name='alert-acknowledge'),
    path('records/<int:pk>/resolve/', views.AlertResolveView.as_view(), name='alert-resolve'),
    path('statistics/', views.AlertStatisticsView.as_view(), name='alert-statistics'),
]
