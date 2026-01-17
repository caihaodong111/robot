from django.db.models import Count, Q
from django.db.models.functions import TruncHour
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import RiskEvent, RobotComponent, RobotGroup
from .permissions import IsStaffOrReadOnly
from .serializers import RiskEventSerializer, RobotComponentSerializer, RobotGroupSerializer


class RobotGroupViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = RobotGroup.objects.all()
    serializer_class = RobotGroupSerializer

    def list(self, request, *args, **kwargs):
        groups = list(self.get_queryset())
        for group in groups:
            qs = group.components.all()
            group._stats = {
                "total": qs.count(),
                "online": qs.filter(status="online").count(),
                "offline": qs.filter(status="offline").count(),
                "maintenance": qs.filter(status="maintenance").count(),
                "highRisk": qs.filter(level="H").count(),
                "historyHighRisk": qs.exclude(risk_history=[]).count(),
            }
        serializer = self.get_serializer(groups, many=True)
        return Response(serializer.data)


class RobotComponentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = RobotComponent.objects.select_related("group").all()
    serializer_class = RobotComponentSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()

        group_key = self.request.query_params.get("group")
        if group_key:
            qs = qs.filter(group__key=group_key)

        tab = self.request.query_params.get("tab")  # highRisk | all | history
        if tab == "highRisk":
            qs = qs.filter(level="H")
        elif tab == "history":
            qs = qs.exclude(risk_history=[])

        keyword = (self.request.query_params.get("keyword") or "").strip()
        if keyword:
            qs = qs.filter(
                Q(robot_id__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(part_no__icontains=keyword)
                | Q(reference_no__icontains=keyword)
                | Q(type_spec__icontains=keyword)
                | Q(tech__icontains=keyword)
            )

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        risk_filter = self.request.query_params.get("riskLevel")
        if risk_filter:
            qs = qs.filter(risk_level=risk_filter)

        level_filter = self.request.query_params.get("level")
        if level_filter:
            qs = qs.filter(level=level_filter)

        mark_mode = self.request.query_params.get("markMode")
        if mark_mode == "zero":
            qs = qs.filter(mark=0)
        elif mark_mode == "nonzero":
            qs = qs.exclude(mark=0)

        axis_keys_raw = (self.request.query_params.get("axisKeys") or "").strip()
        axis_keys = [k.strip() for k in axis_keys_raw.split(",") if k.strip()] if axis_keys_raw else []
        axis_key = (self.request.query_params.get("axisKey") or "").strip()
        if axis_key and axis_key not in axis_keys:
            axis_keys.append(axis_key)

        axis_ok = self.request.query_params.get("axisOk")
        allowed_axes = {"A1", "A2", "A3", "A4", "A5", "A6", "A7"}
        axis_keys = [k for k in axis_keys if k in allowed_axes]
        if axis_keys and axis_ok is not None:
            axis_ok_bool = str(axis_ok).lower() in {"1", "true", "yes"}
            if axis_ok_bool:
                for k in axis_keys:
                    qs = qs.filter(**{f"checks__{k}__ok": True})
            else:
                axis_q = Q()
                for k in axis_keys:
                    axis_q |= Q(**{f"checks__{k}__ok": False})
                qs = qs.filter(axis_q)

        return qs


class RiskEventViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = RiskEvent.objects.select_related("group").all()
    serializer_class = RiskEventSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        group_key = self.request.query_params.get("group")
        if group_key:
            qs = qs.filter(group__key=group_key)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        severity = self.request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity)

        return qs

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        event = self.get_object()
        event.status = "acknowledged"
        event.notes = request.data.get("notes", "") or event.notes
        event.save(update_fields=["status", "notes", "updated_at"])
        return Response(self.get_serializer(event).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        event = self.get_object()
        event.status = "resolved"
        event.notes = request.data.get("notes", "") or event.notes
        event.save(update_fields=["status", "notes", "updated_at"])
        return Response(self.get_serializer(event).data)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        qs = self.get_queryset()
        severity_counts = qs.values("severity").annotate(count=Count("id"))
        status_counts = qs.values("status").annotate(count=Count("id"))

        severity_stats = {item["severity"]: item["count"] for item in severity_counts}
        total_stats = {item["status"]: item["count"] for item in status_counts}
        recent = qs.order_by("-triggered_at")[:5]

        return Response(
            {
                "severity_stats": severity_stats,
                "total_stats": total_stats,
                "recent_alerts": RiskEventSerializer(recent, many=True).data,
            }
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    now = timezone.now()
    since = now - timezone.timedelta(hours=24)
    high_risk_preview_limit = 12

    groups = list(RobotGroup.objects.all())
    group_payload = []
    for group in groups:
        qs = RobotComponent.objects.filter(group=group)
        high_risk_qs = (
            qs.filter(level="H")
            .order_by("-risk_score", "-updated_at")
            .values("id", "robot_id", "name")[:high_risk_preview_limit]
        )
        high_risk_devices = [
            {"id": item["id"], "robot_id": item["robot_id"], "name": item["name"] or item["robot_id"]}
            for item in high_risk_qs
        ]
        group_payload.append(
            {
                "key": group.key,
                "name": group.name,
                "expected_total": group.expected_total,
                "total": qs.count(),
                "highRisk": qs.filter(level="H").count(),
                "historyHighRisk": qs.exclude(risk_history=[]).count(),
                "marked": qs.exclude(mark=0).count(),
                "highRiskDevices": high_risk_devices,
                "highRiskDevicesPreviewLimit": high_risk_preview_limit,
            }
        )

    total = RobotComponent.objects.count()
    high_risk = RobotComponent.objects.filter(level="H").count()
    history_high_risk = RobotComponent.objects.exclude(risk_history=[]).count()
    marked = RobotComponent.objects.exclude(mark=0).count()

    level_dist = {item["level"]: item["count"] for item in RobotComponent.objects.values("level").annotate(count=Count("id"))}

    axes = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
    axis_bad = {}
    for axis in axes:
        axis_bad[axis] = RobotComponent.objects.filter(**{f"checks__{axis}__ok": False}).count()

    event_qs = RiskEvent.objects.filter(triggered_at__gte=since, triggered_at__lte=now)
    hourly = (
        event_qs.annotate(hour=TruncHour("triggered_at"))
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("hour")
    )
    hourly_series = [{"time": item["hour"].isoformat(), "count": item["count"]} for item in hourly]

    recent_components = RobotComponent.objects.select_related("group").order_by("-updated_at")[:20]
    recent_payload = RobotComponentSerializer(recent_components, many=True).data

    top_high_risk = RobotComponent.objects.select_related("group").filter(level="H").order_by("-updated_at")[:20]
    top_high_risk_payload = RobotComponentSerializer(top_high_risk, many=True).data

    return Response(
        {
            "summary": {
                "total": total,
                "highRisk": high_risk,
                "historyHighRisk": history_high_risk,
                "marked": marked,
            },
            "groupStats": group_payload,
            "levelDistribution": level_dist,
            "axisBad": axis_bad,
            "events24h": hourly_series,
            "recentUpdated": recent_payload,
            "highRiskList": top_high_risk_payload,
            "generatedAt": now.isoformat(),
        }
    )
