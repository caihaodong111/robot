from datetime import datetime, timedelta
from django.shortcuts import render
from django.db.models import Count, Q
from rest_framework import mixins, viewsets
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


def bi_view(request):
    """
    BI可视化页面 - 使用Bokeh components静态嵌入
    支持程序、轴、时间范围选择
    """
    from .bokeh_charts import create_bi_charts
    import logging

    logger = logging.getLogger(__name__)

    # 从查询参数获取参数
    table_name = request.GET.get('table', 'as33_020rb_400')
    # 注意：create_bi_charts 现在会自动获取数据库实际时间范围
    # URL 参数用于控件联动，但实际数据范围由数据库决定
    program = request.GET.get('program', None)
    axis = request.GET.get('axis', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    logger.info(f"BI页面请求: table={table_name}, program={program}, axis={axis}, start={start_date}, end={end_date}")

    # 生成Bokeh图表（函数内部会获取数据库实际时间范围）
    # 传递轴和程序参数，只生成需要的图表
    script, div, chart_info = create_bi_charts(
        table_name,
        axis=axis,
        program=program,
        start_date=start_date,
        end_date=end_date,
    )

    if script is None:
        # 数据获取失败或无数据
        logger.error("图表生成失败: 返回None")
        return render(request, 'bi_error.html', {
            'table_name': table_name,
            'error': '无法获取数据，请检查数据库连接或表名是否正确'
        })

    logger.info(f"图表生成成功: script长度={len(script)}, div长度={len(div)}")

    context = {
        'table_name': table_name,
        'bokeh_script': script,
        'bokeh_div': div,
        'chart_info': chart_info,
        # 传递控件值到模板，用于设置默认选择
        'selected_program': program,
        'selected_axis': axis,
        'selected_start_date': start_date,
        'selected_end_date': end_date,
    }
    return render(request, 'bi.html', context)
