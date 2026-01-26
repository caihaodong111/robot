from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    RiskEventViewSet,
    RobotComponentViewSet,
    RobotGroupViewSet,
    GripperCheckViewSet,
    bi_view,
)

router = DefaultRouter()
router.register(r"groups", RobotGroupViewSet, basename="robot-group")
router.register(r"components", RobotComponentViewSet, basename="robot-component")
router.register(r"risk-events", RiskEventViewSet, basename="risk-event")
router.register(r"gripper-check", GripperCheckViewSet, basename="gripper-check")

urlpatterns = [
    path("bi/", bi_view, name="robot-bi"),
    path("", include(router.urls)),
]
