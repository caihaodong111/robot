from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RiskEventViewSet, RobotComponentViewSet, RobotGroupViewSet, dashboard, axis_data, axis_range

router = DefaultRouter()
router.register(r"groups", RobotGroupViewSet, basename="robot-group")
router.register(r"components", RobotComponentViewSet, basename="robot-component")
router.register(r"risk-events", RiskEventViewSet, basename="risk-event")

urlpatterns = [
    path("dashboard/", dashboard, name="robots-dashboard"),
    path("axis-data/", axis_data, name="axis-data"),
    path("axis-range/", axis_range, name="axis-range"),
    path("", include(router.urls)),
]
