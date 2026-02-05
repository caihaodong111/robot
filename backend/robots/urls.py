import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    RiskEventViewSet,
    RobotComponentViewSet,
    RobotGroupViewSet,
    GripperCheckViewSet,
    RobotHighRiskSnapshotViewSet,
    bi_view,
    get_last_sync_time,
)
from .error_trend_chart import CHART_OUTPUT_PATH


def serve_chart(request, filename):
    """
    提供错误率趋势图文件服务

    Args:
        filename: 图片文件名 (如 as33_020rb_400_1_trend.png)
    """
    file_path = os.path.join(CHART_OUTPUT_PATH, filename)

    if not os.path.exists(file_path):
        raise Http404(f"图表文件不存在: {filename}")

    return FileResponse(open(file_path, 'rb'), content_type='image/png')

router = DefaultRouter()
router.register(r"groups", RobotGroupViewSet, basename="robot-group")
router.register(r"components", RobotComponentViewSet, basename="robot-component")
router.register(r"risk-events", RiskEventViewSet, basename="risk-event")
router.register(r"gripper-check", GripperCheckViewSet, basename="gripper-check")
router.register(r"high-risk-histories", RobotHighRiskSnapshotViewSet, basename="high-risk-history")

urlpatterns = [
    path("bi/", bi_view, name="robot-bi"),
    path("charts/<path:filename>", serve_chart, name="robot-chart"),
    path("last_sync_time/", get_last_sync_time, name="last-sync-time"),
    path("", include(router.urls)),
]
