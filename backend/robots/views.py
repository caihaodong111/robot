from datetime import datetime, timedelta
from django.shortcuts import render
from django.db.models import Count, Q
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import RiskEvent, RobotComponent, RobotGroup
from .serializers import (
    RiskEventSerializer,
    RobotComponentSerializer,
    RobotGroupSerializer,
    BIRobotSerializer,
    GripperCheckSerializer,
)
from .gripper_service import check_gripper_from_config
from .error_trend_chart import generate_trend_chart, chart_exists, CHART_OUTPUT_PATH


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RobotGroupViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = RobotGroup.objects.all()
    serializer_class = RobotGroupSerializer

    def list(self, request, *args, **kwargs):
        groups = list(self.get_queryset())

        # 获取时间范围参数（用于统计特定时间段内的风险事件）
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        for group in groups:
            qs = group.components.all()

            # 如果提供了时间范围，过滤在该时间范围内有高风险事件的机器人
            if start_date and end_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    # 延长结束日期到当天结束
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)

                    # 统计在指定时间范围内有高风险的机器人
                    # 这里假设RiskEvent有triggered_at字段
                    from django.db.models import Exists, OuterRef
                    high_risk_in_period = qs.filter(
                        level='H',
                        riskevent__triggered_at__range=(start_dt, end_dt)
                    ).distinct().count()

                    # 统计历史高风险（在时间范围内的）
                    history_in_period = qs.filter(
                        riskevent__triggered_at__range=(start_dt, end_dt)
                    ).exclude(risk_history=[]).distinct().count()

                    group._stats = {
                        "total": qs.count(),
                        "online": qs.filter(status="online").count(),
                        "offline": qs.filter(status="offline").count(),
                        "maintenance": qs.filter(status="maintenance").count(),
                        "highRisk": high_risk_in_period,
                        "historyHighRisk": history_in_period,
                        "timeRange": f"{start_date} ~ {end_date}"
                    }
                except ValueError:
                    # 日期格式错误，使用默认统计
                    group._stats = {
                        "total": qs.count(),
                        "online": qs.filter(status="online").count(),
                        "offline": qs.filter(status="offline").count(),
                        "maintenance": qs.filter(status="maintenance").count(),
                        "highRisk": qs.filter(level="H").count(),
                        "historyHighRisk": qs.exclude(risk_history=[]).count(),
                    }
            else:
                # 默认统计（不限制时间范围）
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
    pagination_class = StandardResultsSetPagination

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

    @action(detail=False, methods=["get"])
    def bi_robots(self, request):
        """获取BI可视化机器人选择列表"""
        # 获取车间过滤
        group_key = request.query_params.get("group")
        qs = self.get_queryset()

        if group_key:
            qs = qs.filter(group__key=group_key)

        # 获取搜索关键词
        keyword = (request.query_params.get("keyword") or "").strip()
        if keyword:
            qs = qs.filter(
                Q(robot_id__icontains=keyword)
                | Q(name__icontains=keyword)
                | Q(part_no__icontains=keyword)
            )

        # 按robot_id去重并排序，同时包含group_key
        robots = qs.values("robot_id", "part_no", "name", "group__key").distinct().order_by("robot_id")

        # 手动构建返回数据
        results = []
        for r in robots:
            results.append({
                "value": r["part_no"],  # BI使用的表名
                "label": f"{r['robot_id']} ({r['part_no']})",
                "robot_id": r["robot_id"],
                "name": r.get("name", ""),
                "group_key": r.get("group__key", ""),
            })

        return Response({"results": results})

    @action(detail=False, methods=["get"])
    def time_range(self, request):
        """
        获取机器人数据的实际时间范围（从数据库表获取）

        参数:
            robot: 机器人部件编号（表名），必填

        返回:
            {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        """
        from .bokeh_charts import get_table_time_range, get_db_engine
        from sqlalchemy import create_engine

        table_name = request.query_params.get("robot")
        if not table_name:
            return Response(
                {"error": "缺少参数 robot，请提供机器人部件编号"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 获取数据库连接配置
            db_config = get_db_engine()
            engine_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            engine = create_engine(engine_url)

            # 获取时间范围
            start_time, end_time = get_table_time_range(table_name, engine)

            # 格式化为 YYYY-MM-DD
            start_date = start_time.strftime("%Y-%m-%d")
            end_date = end_time.strftime("%Y-%m-%d")

            return Response({
                "start_date": start_date,
                "end_date": end_date
            })
        except Exception as e:
            return Response(
                {"error": f"获取时间范围失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"])
    def error_trend_chart(self, request, pk=None):
        """
        获取机器人关节错误率趋势图

        参数:
            axis: 关节编号 (1-7)，必填
            regenerate: 是否重新生成图表 (0/1)，默认为0

        返回:
            {
                "success": true,
                "chart_url": "/media/error_charts/robot_1_trend.png",
                "axis": 1
            }
        """
        robot = self.get_object()
        axis_num = request.query_params.get("axis")
        regenerate = request.query_params.get("regenerate", "0") == "1"

        # 参数验证
        if not axis_num:
            return Response(
                {"success": False, "error": "缺少参数 axis，请提供关节编号 (1-7)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            axis_num = int(axis_num)
            if axis_num < 1 or axis_num > 7:
                raise ValueError("关节编号必须在 1-7 之间")
        except ValueError as e:
            return Response(
                {"success": False, "error": f"参数 axis 无效: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 检查是否需要重新生成
        chart_path = None
        if regenerate or not chart_exists(robot.part_no, axis_num):
            try:
                chart_path = generate_trend_chart(robot.part_no, axis_num)
            except FileNotFoundError as e:
                return Response(
                    {"success": False, "error": f"CSV 数据文件不存在: {str(e)}"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {"success": False, "error": f"生成图表失败: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # 图表已存在，直接返回路径
            chart_path = f"{CHART_OUTPUT_PATH}/{robot.part_no}_{axis_num}_trend.png"

        # 构建返回数据
        # 如果路径是绝对路径，转换为相对路径供前端使用
        # 这里假设你需要通过 Django 的 static 或 media 服务来提供图片
        # 实际部署时可能需要配置 nginx 或 Django staticfiles
        chart_filename = f"{robot.part_no}_{axis_num}_trend.png"
        chart_url = f"/api/robots/charts/{chart_filename}"

        return Response({
            "success": True,
            "chart_url": chart_url,
            "chart_path": chart_path,
            "axis": axis_num,
            "robot_part_no": robot.part_no
        })


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


@xframe_options_exempt
def bi_view(request):
    """
    BI可视化页面 - 使用Bokeh components静态嵌入
    支持程序、轴、时间范围选择
    支持embed参数：embed=1时返回纯净模板用于iframe嵌入
    """
    from .bokeh_charts import create_bi_charts
    import logging

    logger = logging.getLogger(__name__)

    # 从查询参数获取参数
    # 优先使用robot参数（来自MonitoringView的跳转），其次使用table参数
    table_name = request.GET.get('robot', request.GET.get('table', 'as33_020rb_400'))
    # 检测是否为嵌入模式
    embed_mode = request.GET.get('embed', '0') == '1'
    # 注意：create_bi_charts 现在会自动获取数据库实际时间范围
    # URL 参数用于控件联动，但实际数据范围由数据库决定
    program = request.GET.get('program', None)
    axis = request.GET.get('axis', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    logger.info(f"BI页面请求: table={table_name}, program={program}, axis={axis}, start={start_date}, end={end_date}, embed={embed_mode}")

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

    # 根据embed参数选择模板
    template_name = 'bi_embed.html' if embed_mode else 'bi.html'
    return render(request, template_name, context)


class GripperCheckViewSet(viewsets.GenericViewSet):
    """
    关键轨迹检查API ViewSet
    提供执行关键轨迹检查和获取机器人列表的接口
    """

    def get_queryset(self):
        return RobotComponent.objects.all()

    @action(detail=False, methods=['post'])
    def execute(self, request):
        """
        执行关键轨迹检查

        请求体:
        {
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-08T00:00:00",
            "gripper_list": ["as33_020rb_400", "as33_020rb_401"],
            "key_paths": ["R1/CO", "R1/DO", "R1/CN", "R1/DN"]
        }

        返回:
        {
            "success": true,
            "count": 100,
            "data": [...],
            "columns": [...]
        }
        """
        serializer = GripperCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid request data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 执行检查
            result = check_gripper_from_config(serializer.validated_data)
            return Response(result)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def robot_tables(self, request):
        """
        获取可用的机器人表名列表（从RobotComponent获取part_no）
        支持按车间(group_key)筛选和关键词(keyword)搜索

        参数:
            group: 车间key（可选）
            keyword: 搜索关键词（可选，支持part_no、robot_id、name模糊搜索）

        返回:
        {
            "results": [
                {"value": "as33_020rb_400", "label": "as33_020rb_400", "robot_id": "RB001", "group_key": "plant_a"},
                ...
            ]
        }
        """
        # 获取车间筛选参数
        group_key = request.query_params.get('group')
        keyword = request.query_params.get('keyword', '').strip()

        # 构建查询
        qs = RobotComponent.objects.values('part_no', 'robot_id', 'group__key', 'name').distinct()

        if group_key:
            qs = qs.filter(group__key=group_key)

        # 支持关键词搜索
        if keyword:
            qs = qs.filter(
                Q(part_no__icontains=keyword)
                | Q(robot_id__icontains=keyword)
                | Q(name__icontains=keyword)
            )

        tables = qs.order_by('part_no')

        results = []
        for t in tables:
            results.append({
                'value': t['part_no'],
                'label': t['part_no'],
                'robot_id': t.get('robot_id', ''),
                'group_key': t.get('group__key', ''),
            })

        return Response({'results': results})

    @action(detail=False, methods=['get'])
    def config_template(self, request):
        """
        获取配置模板，帮助前端了解如何构建请求

        返回:
        {
            "key_paths_example": ["R1/CO", "R1/DO", "R1/CN", "R1/DN"],
            "default_time_range_hours": 168
        }
        """
        return Response({
            'key_paths_example': ['R1/CO', 'R1/DO', 'R1/CN', 'R1/DN'],
            'default_time_range_hours': 168,  # 7天
            'description': '关键轨迹检查用于检测机器人抓放点动作的电流异常'
        })
