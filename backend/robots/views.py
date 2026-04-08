from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
import pandas as pd
import numpy as np
from celery.result import AsyncResult
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, StreamingHttpResponse, FileResponse
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import RiskEvent, RobotComponent, RobotGroup, RobotHighRiskSnapshot, RobotReferenceDict
from .serializers import (
    RiskEventSerializer,
    RobotComponentSerializer,
    RobotComponentListSerializer,
    RobotGroupSerializer,
    BIRobotSerializer,
    GripperCheckSerializer,
    RobotHighRiskSnapshotSerializer,
    RobotHighRiskSnapshotListSerializer,
    RobotReferenceDictSerializer,
    RefreshLogSerializer,
)
from .gripper_check_state import (
    get_gripper_check_latest,
    get_gripper_check_status,
    set_gripper_check_status,
    request_gripper_check_cancel,
)
from .error_trend_chart import generate_trend_chart, chart_exists
from .tasks import gripper_check_csv_task, gripper_check_task
import json
import time
import uuid

from .bi_jobs import BiCancelledError, bi_job_registry

logger = logging.getLogger(__name__)

DISCONNECTED_FIELDS = [
    "error1_c1",
    "tem1_m",
    "tem2_m",
    "tem3_m",
    "tem4_m",
    "tem5_m",
    "tem6_m",
    "tem7_m",
    "a1_e_rate",
    "a2_e_rate",
    "a3_e_rate",
    "a4_e_rate",
    "a5_e_rate",
    "a6_e_rate",
    "a7_e_rate",
    "a1_rms",
    "a2_rms",
    "a3_rms",
    "a4_rms",
    "a5_rms",
    "a6_rms",
    "a7_rms",
    "a1_e",
    "a2_e",
    "a3_e",
    "a4_e",
    "a5_e",
    "a6_e",
    "a7_e",
    "q1",
    "q2",
    "q3",
    "q4",
    "q5",
    "q6",
    "q7",
    "curr_a1_max",
    "curr_a2_max",
    "curr_a3_max",
    "curr_a4_max",
    "curr_a5_max",
    "curr_a6_max",
    "curr_a7_max",
    "curr_a1_min",
    "curr_a2_min",
    "curr_a3_min",
    "curr_a4_min",
    "curr_a5_min",
    "curr_a6_min",
    "curr_a7_min",
]


def build_disconnected_q(prefix=""):
    query = Q()
    for field in DISCONNECTED_FIELDS:
        query &= Q(**{f"{prefix}{field}__isnull": True})
    return query


def get_sort_fields(model):
    fields = set()
    for field in model._meta.get_fields():
        if getattr(field, "attname", None) and not field.many_to_many and not field.one_to_many:
            fields.add(field.name)
    return fields


COMPONENT_SORT_FIELDS = get_sort_fields(RobotComponent)
SNAPSHOT_SORT_FIELDS = get_sort_fields(RobotHighRiskSnapshot)


def apply_ordering(qs, sort_by, sort_order, allowed_fields):
    if not sort_by:
        return qs
    sort_by = sort_by.strip()
    if sort_by not in allowed_fields:
        return qs
    order_prefix = "-" if sort_order == "desc" else ""
    return qs.order_by(f"{order_prefix}{sort_by}")


def parse_axis_ok(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "ok", "normal", "good"}:
        return True
    if text in {"0", "false", "no", "bad", "high", "abnormal"}:
        return False
    return None


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RobotGroupViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = RobotGroup.objects.all()
    serializer_class = RobotGroupSerializer

    # 排除的车间 key 列表
    EXCLUDED_GROUP_KEYS = ['', '(空)', '未分配']

    def get_queryset(self):
        """过滤掉排除的车间，避免加载所有组件"""
        return super().get_queryset().exclude(
            key__in=self.EXCLUDED_GROUP_KEYS
        )

    def list(self, request, *args, **kwargs):
        # 获取时间范围参数（用于统计特定时间段内的风险事件）
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # 使用 annotate 预先计算统计数据，避免 N+1 查询
        disconnected_q = build_disconnected_q("components__")

        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)

                # 预先计算每个组的统计数据
                groups = self.get_queryset().annotate(
                    total_count=Count('components'),
                    high_risk_count=Count(
                        'components',
                        filter=Q(components__level='H') & Q(components__riskevent__triggered_at__range=(start_dt, end_dt))
                    ),
                    disconnected_count=Count('components', filter=disconnected_q),
                ).distinct()

                for group in groups:
                    group._stats = {
                        "total": group.total_count,
                        "highRisk": group.high_risk_count,
                        "disconnected": group.disconnected_count,
                        "timeRange": f"{start_date} ~ {end_date}"
                    }
            except ValueError:
                # 日期格式错误，使用默认统计
                groups = self.get_queryset().annotate(
                    total_count=Count('components'),
                    high_risk_count=Count('components', filter=Q(components__level='H')),
                    disconnected_count=Count('components', filter=disconnected_q),
                )

                for group in groups:
                    group._stats = {
                        "total": group.total_count,
                        "highRisk": group.high_risk_count,
                        "disconnected": group.disconnected_count,
                    }
        else:
            # 默认统计（不限制时间范围）
            groups = self.get_queryset().annotate(
                total_count=Count('components'),
                high_risk_count=Count('components', filter=Q(components__level='H')),
                disconnected_count=Count('components', filter=disconnected_q),
            )

            for group in groups:
                group._stats = {
                    "total": group.total_count,
                    "highRisk": group.high_risk_count,
                    "disconnected": group.disconnected_count,
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
    
    def get_serializer_class(self):
        if self.action == "list":
            tab = (self.request.query_params.get("tab") or "").strip()
            if tab != "all":
                return RobotComponentListSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        qs = super().get_queryset()

        group_key = self.request.query_params.get("group")
        if group_key:
            qs = qs.filter(group__key=group_key)

        tab = self.request.query_params.get("tab")  # highRisk | all | history
        if tab == "highRisk":
            qs = qs.filter(level="H")
        elif tab == "history":
            # history 标签页不使用 robot_components 表，由单独的 API 处理
            qs = qs.none()  # 返回空查询集，前端应该请求 /api/robots/high-risk-histories/

        keyword = (self.request.query_params.get("keyword") or "").strip()
        if keyword:
            qs = qs.filter(
                Q(robot__icontains=keyword)
                | Q(shop__icontains=keyword)
                | Q(reference__icontains=keyword)
                | Q(type__icontains=keyword)
                | Q(tech__icontains=keyword)
                | Q(remark__icontains=keyword)
            )

        level_filter = self.request.query_params.get("level")
        if level_filter:
            # 支持多个 level 值（逗号分隔）
            levels = [l.strip() for l in level_filter.split(',') if l.strip()]
            if len(levels) == 1:
                qs = qs.filter(level=levels[0])
            else:
                qs = qs.filter(level__in=levels)

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
            axis_ok_bool = parse_axis_ok(axis_ok)
            if axis_ok_bool is True:
                # 轴状态为 ok（排除 high，允许空值代表正常）
                for k in axis_keys:
                    field = k.lower()
                    qs = qs.exclude(**{f"{field}__iexact": "high"})
            elif axis_ok_bool is False:
                # 轴状态为 high（所有所选轴都为 high）
                for k in axis_keys:
                    qs = qs.filter(**{f"{k.lower()}__iexact": "high"})

        sort_by = (self.request.query_params.get("sort_by") or "").strip()
        sort_order = (self.request.query_params.get("sort_order") or "").lower()
        if sort_order not in {"asc", "desc"}:
            sort_order = "asc"
        qs = apply_ordering(qs, sort_by, sort_order, COMPONENT_SORT_FIELDS)

        return qs

    def perform_update(self, serializer):
        instance = self.get_object()
        reference = serializer.validated_data.get("reference")
        number_provided = "number" in serializer.validated_data
        number = serializer.validated_data.get("number")

        if reference:
            mapped_number = RobotReferenceDict.objects.filter(
                robot=instance.robot,
                reference=reference,
            ).values_list("number", flat=True).first()
            if mapped_number is not None:
                serializer.save(number=mapped_number)
                return

        if number_provided:
            serializer.save(number=number)
        else:
            serializer.save()

    def update(self, request, *args, **kwargs):
        """添加调试日志来查看请求详情"""
        logger.info(f"PATCH request data: {request.data}")
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"PATCH success for id {kwargs.get('pk')}")

            # 同步更新到CSV配置文件
            try:
                instance = self.get_object()
                from .robot_config_sync import sync_robot_component_to_csv
                sync_success = sync_robot_component_to_csv(instance)
                if sync_success:
                    logger.info(f"CSV同步成功: robot={instance.robot}")
            except Exception as csv_error:
                logger.error(f"CSV同步失败: {csv_error}")
                # CSV同步失败不影响主流程，只记录日志

            return response
        except Exception as e:
            logger.error(f"PATCH error for id {kwargs.get('pk')}: {type(e).__name__}: {e}")
            raise

    @action(detail=False, methods=["get"])
    def bi_robots(self, request):
        """
        获取 BI 可视化机器人（表名）信息

        当前行为（PROGRAM CYCLE SYNC 专用）：
        - 只查询 SG 数据库（SG_DB_*）。
        - 只支持精确匹配（不做模糊匹配），大小写不敏感。
        - 找不到则返回 404 错误。
        """
        import re

        def _get_sg_db_url():
            sg_name = os.getenv("SG_DB_NAME")
            sg_user = os.getenv("SG_DB_USER")
            sg_password = os.getenv("SG_DB_PASSWORD")
            sg_host = os.getenv("SG_DB_HOST")
            sg_port = os.getenv("SG_DB_PORT") or "3306"

            missing = [key for key, value in [
                ("SG_DB_NAME", sg_name),
                ("SG_DB_USER", sg_user),
                ("SG_DB_PASSWORD", sg_password),
                ("SG_DB_HOST", sg_host),
            ] if not value]
            if missing:
                raise ValueError(f"Missing SG DB env vars: {', '.join(missing)}")

            return f"mysql+pymysql://{sg_user}:{sg_password}@{sg_host}:{sg_port}/{sg_name}"

        def _find_sg_table_exact(table_name: str):
            from sqlalchemy import create_engine, text
            name = (table_name or "").strip()
            if not name:
                return None

            engine = create_engine(_get_sg_db_url())
            with engine.connect() as conn:
                # 使用 information_schema 避免全库 SHOW TABLES；精确匹配（大小写不敏感）
                sg_db_name = os.getenv("SG_DB_NAME")
                row = conn.execute(
                    text(
                        "SELECT table_name "
                        "FROM information_schema.tables "
                        "WHERE table_schema = :schema "
                        "AND LOWER(table_name) = LOWER(:name) "
                        "LIMIT 1"
                    ),
                    {"schema": sg_db_name, "name": name},
                ).fetchone()
            return row[0] if row and row[0] else None

        keyword = (request.query_params.get("keyword") or "").strip()
        if not keyword:
            return Response({"results": []})

        if not re.match(r"^[0-9a-zA-Z_-]+$", keyword):
            return Response({"detail": "非法的机器人/表名参数"}, status=400)

        try:
            sg_schema = os.getenv("SG_DB_NAME") or ""
            table = _find_sg_table_exact(keyword)
        except Exception as e:
            logger.warning("SG DB table lookup unavailable: %s", e)
            return Response({"detail": "SG 数据库不可用或连接失败"}, status=503)

        if not table:
            schema_hint = f"（schema={sg_schema}）" if sg_schema else ""
            return Response({"detail": f"SG 数据库中未找到表: {keyword}{schema_hint}"}, status=404)

        if not re.search(r"rb[_-]?\d+", str(table), flags=re.IGNORECASE):
            return Response({"detail": f"表名不符合机器人命名规则: {table}"}, status=404)

        return Response(
            {
                "results": [
                    {
                        "value": str(table).strip(),
                        "label": str(table).strip(),
                        "robot_id": str(table).strip(),
                    }
                ]
            }
        )

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
        from .bokeh_charts import get_table_time_bounds, get_db_engine
        from sqlalchemy import create_engine

        table_name = request.query_params.get("robot")
        if not table_name:
            return Response(
                {"error": "缺少参数 robot，请提供机器人部件编号"},
                status=status.HTTP_400_BAD_REQUEST
            )
        table_name = str(table_name).strip()

        try:
            # 获取数据库连接配置
            db_config = get_db_engine()
            engine_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            engine = create_engine(engine_url)

            # 获取真实时间边界（MIN/MAX）
            start_time, end_time = get_table_time_bounds(table_name, engine)

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
                "chart_data": "base64_encoded_image_data",
                "axis": 1
            }
        """
        robot = self.get_object()
        axis_num = request.query_params.get("axis")

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

        # 生成图表（每次都重新生成，因为不保存到磁盘了）
        try:
            chart_base64 = generate_trend_chart(robot.robot, axis_num)
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

        # 返回 base64 编码的图片数据
        return Response({
            "success": True,
            "chart_data": chart_base64,
            "axis": axis_num,
            "robot": robot.robot
        })

    @action(detail=False, methods=["post"])
    def import_csv(self, request):
        """
        导入 weeklyresult.csv 文件到 robot_components 表

        请求体:
        {
            "folder_path": "/Users/caihd/Desktop/sg",  // 可选，未提供则使用数据库配置
            "project": "reuse",  // 可选
            "file_path": "/path/to/specific/file.csv"  // 可选，直接指定文件
        }

        返回:
        {
            "success": true,
            "file": "文件路径",
            "source_file": "文件名",
            "records_created": 100,
            "records_updated": 10,
            "total_records": 110,
            "shop_stats": {"MRA1": {"created": 50, "updated": 5}}
        }
        """
        from .weekly_result_service import import_robot_components_csv
        from rest_framework import serializers

        class ImportCSVSerializer(serializers.Serializer):
            folder_path = serializers.CharField(required=False, allow_blank=True)
            project = serializers.CharField(required=False, default='reuse')
            file_path = serializers.CharField(required=False, allow_blank=True)
            use_mysql_load_data = serializers.BooleanField(required=False)

        serializer = ImportCSVSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid request data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            result = import_robot_components_csv(
                file_path=data.get('file_path'),
                folder_path=data.get('folder_path') or None,
                project=data.get('project') or None,
                use_mysql_load_data=data.get('use_mysql_load_data'),
            )
            return Response(result)
        except FileNotFoundError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def import_csv_async(self, request):
        """
        异步导入 weeklyresult.csv 文件到 robot_components 表
        """
        from rest_framework import serializers
        from .tasks import import_robot_components_csv_task

        class ImportCSVAsyncSerializer(serializers.Serializer):
            folder_path = serializers.CharField(required=False, allow_blank=True)
            project = serializers.CharField(required=False, default='reuse')
            file_path = serializers.CharField(required=False, allow_blank=True)
            use_mysql_load_data = serializers.BooleanField(required=False)

        serializer = ImportCSVAsyncSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid request data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        task = import_robot_components_csv_task.delay(
            file_path=data.get('file_path'),
            folder_path=data.get('folder_path') or None,
            project=data.get('project') or None,
            use_mysql_load_data=data.get('use_mysql_load_data'),
        )
        return Response({
            'success': True,
            'task_id': task.id,
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["get"])
    def import_csv_status(self, request):
        """
        查询异步 CSV 导入任务状态
        """
        from celery.result import AsyncResult

        task_id = (request.query_params.get("task_id") or "").strip()
        if not task_id:
            return Response(
                {"success": False, "error": "缺少参数 task_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = AsyncResult(task_id)
        payload = {
            "success": True,
            "task_id": task_id,
            "state": result.state,
        }
        if result.successful():
            payload["result"] = result.result
        elif result.failed():
            payload["error"] = str(result.result)

        return Response(payload)

    @action(detail=False, methods=["get"])
    def stats_summary(self, request):
        """
        获取机器人统计数据摘要

        返回:
            {
                "total": 156,
                "high_risk": 14,
                "disconnected": 8
            }
        """
        qs = self.get_queryset()
        total = qs.count()
        high_risk = qs.filter(level='H').count()
        disconnected = qs.filter(build_disconnected_q()).count()

        return Response({
            'total': total,
            'high_risk': high_risk,
            'disconnected': disconnected,
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
@require_GET
def bi_cancel_view(request):
    job_id = (request.GET.get("job_id") or "").strip()
    cancelled = bi_job_registry.cancel(job_id)
    return JsonResponse({"ok": True, "job_id": job_id, "cancelled": cancelled})


@xframe_options_exempt
def bi_view(request):
    """
    BI可视化页面 - 使用Bokeh components静态嵌入
    支持程序、轴、时间范围选择
    支持embed参数：embed=1时返回纯净模板用于iframe嵌入
    """
    from .bokeh_charts import create_bi_charts
    from bokeh.resources import CDN, INLINE
    import logging

    logger = logging.getLogger(__name__)

    # 从查询参数获取参数
    # 优先使用robot参数（来自MonitoringView的跳转），其次使用table参数
    import re

    table_name = request.GET.get('robot', request.GET.get('table', 'as33_020rb_400'))
    table_name = (table_name or '').strip()
    if not re.match(r'^[0-9a-zA-Z_-]+$', table_name):
        return render(request, 'bi_error.html', {
            'table_name': table_name,
            'error': '非法的表名参数'
        })

    raw_job_id = (request.GET.get("job_id") or "").strip()
    job_id = ""
    if raw_job_id and re.match(r"^[0-9a-zA-Z_-]{1,128}$", raw_job_id):
        job_id = raw_job_id
    elif raw_job_id:
        job_id = uuid.uuid4().hex

    if job_id:
        bi_job_registry.register(job_id)

    def cancel_check():
        if job_id and bi_job_registry.is_cancelled(job_id):
            raise BiCancelledError()
    # 检测是否为嵌入模式
    embed_mode = request.GET.get('embed', '0') == '1'
    # 注意：create_bi_charts 现在会自动获取数据库实际时间范围
    # URL 参数用于控件联动，但实际数据范围由数据库决定
    program = request.GET.get('program', None)
    axis = request.GET.get('axis', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    logger.info(f"BI页面请求: table={table_name}, program={program}, axis={axis}, start={start_date}, end={end_date}, embed={embed_mode}")

    # 优先走 Bokeh Server（Digitaltwin_timefree.py 思路）：常驻进程 + 内存交互更新
    # 开关：BI_BOKEH_SERVER_URL 存在时默认启用；render=static 可强制回退静态 components。
    import os
    from django.conf import settings

    bokeh_server_url = (
        (os.getenv("BI_BOKEH_SERVER_URL") or "").strip()
        or (getattr(settings, "BI_BOKEH_SERVER_URL", "") or "").strip()
    )
    if not bokeh_server_url:
        # 自动推导：与当前请求相同 host，不同端口（默认 5008）
        # 优先使用原始请求头中的 Host（处理代理情况）
        request_host = (request.get_host() or "").split(":", 1)[0].strip()

        # 如果是通过代理（如 127.0.0.1），尝试从 X-Forwarded-Host 获取真实主机
        if request_host in ("127.0.0.1", "localhost"):
            forwarded_host = request.META.get("HTTP_X_FORWARDED_HOST") or request.META.get("HTTP_X_REAL_IP")
            if forwarded_host:
                request_host = forwarded_host.split(":", 1)[0].strip()

        bi_bokeh_port = int(getattr(settings, "BI_BOKEH_SERVER_PORT", 5008))
        scheme = "https" if request.is_secure() else "http"
        if request_host:
            bokeh_server_url = f"{scheme}://{request_host}:{bi_bokeh_port}/"

    force_static = request.GET.get("render", "").strip().lower() == "static"
    use_bokeh_server = bool(getattr(settings, "BI_BOKEH_USE_SERVER", True)) and bool(bokeh_server_url) and not force_static

    try:
        if use_bokeh_server:
            from bokeh.embed import server_document

            cancel_check()
            arguments = {
                "table": table_name,
                "program": program or "",
                "axis": axis or "",
                "start_date": start_date or "",
                "end_date": end_date or "",
            }
            server_script = server_document(bokeh_server_url, arguments=arguments)
            return render(
                request,
                "bi_server_embed.html",
                {
                    "table_name": table_name,
                    "bokeh_server_script": server_script,
                },
            )

    # 静态嵌入（旧逻辑）：每次请求重建并 components 序列化
        script, div, chart_info, energy_modal_html, energy_script = create_bi_charts(
            table_name,
            axis=axis,
            program=program,
            start_date=start_date,
            end_date=end_date,
            cancel_check=cancel_check,
        )

        if script is None:
            logger.error("图表生成失败: 返回None")
            return render(
                request,
                "bi_error.html",
                {
                    "table_name": table_name,
                    "error": "无法获取数据，请检查数据库连接或表名是否正确",
                },
            )

        logger.info(f"图表生成成功: script长度={len(script)}, div长度={len(div)}")

        # NOTE: iframe嵌入场景经常处于内网/受限网络环境，CDN 资源可能无法加载，导致前端“空白但无报错”。
        bokeh_resources = (INLINE if embed_mode else CDN).render()

        context = {
            "table_name": table_name,
            "bokeh_resources": bokeh_resources,
            "bokeh_script": script,
            "bokeh_div": div,
            "chart_info": chart_info,
            "energy_modal_html": energy_modal_html,
            "energy_script": energy_script,
            "selected_program": program,
            "selected_axis": axis,
            "selected_start_date": start_date,
            "selected_end_date": end_date,
        }

        template_name = "bi_embed.html" if embed_mode else "bi.html"
        return render(request, template_name, context)
    except BiCancelledError:
        logger.info("BI 图生成已取消: table=%s job_id=%s", table_name, job_id)
        return render(
            request,
            "bi_error.html",
            {
                "table_name": table_name,
                "error": "已取消生成",
            },
        )
    finally:
        if job_id:
            bi_job_registry.unregister(job_id)


@xframe_options_exempt
def bi_program_data_view(request):
    """
    PROGRAM CYCLE SYNC: program_name 切换时无刷新更新数据。
    返回指定 program 的 ColumnDataSource 数据（source / agg）。
    """
    from .bokeh_charts import get_bi_program_payload
    import re

    table_name = request.GET.get("robot", request.GET.get("table", ""))
    table_name = (table_name or "").strip()
    if not re.match(r"^[0-9a-zA-Z_-]+$", table_name):
        return JsonResponse({"ok": False, "error": "非法的表名参数"}, status=400)

    program = request.GET.get("program", None)
    start_date = request.GET.get("start_date", None)
    end_date = request.GET.get("end_date", None)

    payload = get_bi_program_payload(
        table_name=table_name,
        program=program,
        start_date=start_date,
        end_date=end_date,
    )
    status_code = 200 if payload.get("ok") else 400
    return JsonResponse(payload, status=status_code)


@xframe_options_exempt
def bi_programs_view(request):
    """
    返回指定 robot/table 在时间范围内的 program(Name_C) 列表。
    为避免首屏阻塞，BI 页面会延迟调用此接口填充下拉选项。
    """
    from .bokeh_charts import get_db_engine, get_real_table_name, _normalize_date_bounds, _format_datetime
    from sqlalchemy import create_engine, text
    import logging
    import re
    import pandas as pd

    logger = logging.getLogger(__name__)

    table_name = request.GET.get("robot", request.GET.get("table", ""))
    table_name = (table_name or "").strip()
    if not re.match(r"^[0-9a-zA-Z_-]+$", table_name):
        return JsonResponse({"ok": False, "error": "非法的表名参数"}, status=400)

    start_date = request.GET.get("start_date", None)
    end_date = request.GET.get("end_date", None)
    requested_start, requested_end = _normalize_date_bounds(start_date, end_date)
    if not requested_start or not requested_end:
        return JsonResponse({"ok": False, "error": "缺少 start_date/end_date"}, status=400)
    if requested_start > requested_end:
        requested_start, requested_end = requested_end, requested_start

    db_config = get_db_engine()
    try:
        engine = create_engine(
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
    except Exception as e:
        logger.warning("数据库连接失败: %s", e)
        return JsonResponse({"ok": False, "error": "数据库连接失败"}, status=500)

    real_table = get_real_table_name(table_name, engine)
    time_column = "Timestamp"

    try:
        programs_sql = (
            f"SELECT DISTINCT `Name_C` AS Name_C "
            f"FROM `{real_table}` "
            f"WHERE `{time_column}` BETWEEN :start_time AND :end_time "
            f"AND `Name_C` IS NOT NULL AND `Name_C` <> ''"
        )
        df = pd.read_sql(
            text(programs_sql),
            engine,
            params={
                "start_time": _format_datetime(requested_start),
                "end_time": _format_datetime(requested_end),
            },
        )
        programs = []
        if not df.empty and "Name_C" in df.columns:
            programs = [str(v) for v in df["Name_C"].dropna().tolist() if str(v)]
            programs.sort()
        return JsonResponse({"ok": True, "programs": programs})
    except Exception as e:
        logger.warning("获取 program 列表失败: %s", e)
        return JsonResponse({"ok": False, "error": "获取 program 列表失败"}, status=500)


class GripperCheckViewSet(viewsets.GenericViewSet):
    """
    关键轨迹检查API ViewSet
    提供执行关键轨迹检查和获取机器人列表的接口
    """

    def get_queryset(self):
        return RobotComponent.objects.all()

    def _get_gripper_export_dir(self):
        return Path(getattr(settings, "BASE_DIR", ".")) / "exports" / "gripper_check"

    def _parse_multi_query_param(self, request, name):
        values = []
        for raw in request.query_params.getlist(name):
            if raw is None:
                continue
            values.extend(str(raw).split(","))
        return [value.strip() for value in values if value and value.strip()]

    def _resolve_export_csv_path(self, filename):
        safe_name = Path((filename or "").strip()).name
        if not safe_name or safe_name in {".", ".."}:
            return None
        path = self._get_gripper_export_dir() / safe_name
        try:
            path.resolve().relative_to(self._get_gripper_export_dir().resolve())
        except Exception:
            return None
        return path

    def _read_csv_page_response(self, path, page, page_size, sort_col, order, keyword):
        try:
            try:
                df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
            except pd.errors.EmptyDataError:
                logger.warning("read csv page got empty csv path=%s", path)
                return Response(
                    {
                        "success": True,
                        "count": 0,
                        "page": page,
                        "page_size": page_size,
                        "columns": [],
                        "data": [],
                    }
                )
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(path, encoding="gbk", low_memory=False)
                except pd.errors.EmptyDataError:
                    logger.warning("read csv page got empty csv path=%s", path)
                    return Response(
                        {
                            "success": True,
                            "count": 0,
                            "page": page,
                            "page_size": page_size,
                            "columns": [],
                            "data": [],
                        }
                    )

            if df.empty:
                return Response(
                    {
                        "success": True,
                        "count": 0,
                        "page": page,
                        "page_size": page_size,
                        "columns": df.columns.tolist(),
                        "data": [],
                    }
                )

            if keyword:
                candidate_cols = [c for c in ["robot", "Name_C", "SNR_C", "SUB", "P_name"] if c in df.columns]
                if candidate_cols:
                    mask = False
                    for col in candidate_cols:
                        mask = mask | df[col].astype(str).str.contains(keyword, case=False, na=False)
                    df = df[mask]

            if sort_col and sort_col in df.columns:
                asc = order != "desc"
                series = df[sort_col]
                numeric = pd.to_numeric(series, errors="coerce")
                if numeric.notna().any():
                    df = df.assign(_sort_key=numeric).sort_values("_sort_key", ascending=asc, kind="mergesort")
                    df = df.drop(columns=["_sort_key"])
                else:
                    df = df.sort_values(sort_col, ascending=asc, kind="mergesort")

            total = int(df.shape[0])
            start = (page - 1) * page_size
            end = start + page_size
            page_df = df.iloc[start:end].copy()
            page_df = page_df.replace([np.nan, np.inf, -np.inf], None)

            return Response(
                {
                    "success": True,
                    "count": total,
                    "page": page,
                    "page_size": page_size,
                    "columns": df.columns.tolist(),
                    "data": page_df.to_dict("records"),
                }
            )
        except Exception as exc:
            logger.exception("read csv page failed path=%s", path)
            return Response({"success": False, "error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _queue_gripper_check_task(self, config_data, task_func):
        task_id = uuid.uuid4().hex
        set_gripper_check_status("queued", task_id=task_id)
        try:
            task_func.apply_async(args=[config_data], task_id=task_id)
        except Exception as exc:
            logger.exception("Failed to enqueue gripper check task %s", task_id)
            set_gripper_check_status("failed", error=str(exc), task_id=task_id)
            return Response(
                {"success": False, "error": "enqueue-failed", "details": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"success": True, "queued": True, "task_id": task_id, "status": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=['post'])
    def execute(self, request):
        """
        执行关键轨迹检查（后台线程执行）

        请求体:
        {
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-08T00:00:00",
            "gripper_list": ["as33_020rb_400", "as33_020rb_401"],
            "key_paths": ["R1/CO", "R1/DO", "R1/CN", "R1/DN"]
        }

        返回:
        {
            "queued": true,
            "task_id": "xxx",
            "status": "running"
        }
        """
        serializer = GripperCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Invalid request data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        config_data = dict(serializer.validated_data)
        return self._queue_gripper_check_task(config_data, gripper_check_task)

    @action(detail=False, methods=["post"], url_path="execute_csv")
    def execute_csv(self, request):
        """
        执行关键轨迹检查并导出 CSV（异步）

        说明：
        - 大数据量（>1h）不适合长连接等待；此接口立即返回 task_id
        - 前端通过 /status 轮询，完成后调用 /download_csv 下载文件
        """
        serializer = GripperCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": "Invalid request data",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        config_data = dict(serializer.validated_data)
        return self._queue_gripper_check_task(config_data, gripper_check_csv_task)

    @action(detail=False, methods=["post"])
    def cancel(self, request):
        task_id = (request.data.get("task_id") or "").strip()
        if not task_id:
            return Response({"success": False, "error": "missing-task-id"}, status=status.HTTP_400_BAD_REQUEST)

        task_status = get_gripper_check_status(task_id=task_id)
        if not task_status:
            return Response({"success": False, "error": "task-not-found"}, status=status.HTTP_404_NOT_FOUND)

        status_value = (task_status.get("status") or "").lower()
        if status_value in {"idle", "failed", "cancelled"}:
            return Response(
                {"success": False, "error": "task-not-active", **task_status},
                status=status.HTTP_409_CONFLICT,
            )

        request_gripper_check_cancel(task_id)
        AsyncResult(task_id).revoke(terminate=False)
        if status_value == "queued":
            set_gripper_check_status("cancelled", task_id=task_id)
            return Response({"success": True, "task_id": task_id, "status": "cancelled"})

        set_gripper_check_status("cancelling", task_id=task_id)
        return Response({"success": True, "task_id": task_id, "status": "cancelling"})

    @action(detail=False, methods=["get"], url_path="download_csv")
    def download_csv(self, request):
        """
        下载最近一次 CSV（或指定 task_id 的 CSV）
        """
        task_id = (request.query_params.get("task_id") or "").strip()
        if not task_id:
            return Response({"success": False, "error": "missing-task-id"}, status=status.HTTP_400_BAD_REQUEST)

        latest = get_gripper_check_latest(task_id=task_id) or {}

        if not latest or not latest.get("success"):
            return Response({"success": False, "error": "no-ready-csv"}, status=status.HTTP_404_NOT_FOUND)

        server_path = (latest.get("server_path") or "").strip()
        filename = (latest.get("filename") or "trajectory_report.csv").strip()
        if not server_path:
            return Response({"success": False, "error": "missing-server-path"}, status=status.HTTP_404_NOT_FOUND)

        path = Path(server_path)
        if not path.exists():
            return Response({"success": False, "error": "file-not-found"}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(path.open("rb"), as_attachment=True, filename=filename, content_type="text/csv")
        response["X-Server-File-Path"] = str(path)
        return response

    @action(detail=False, methods=["get"], url_path="download_csv_file")
    def download_csv_file(self, request):
        filename = (request.query_params.get("filename") or "").strip()
        if not filename:
            return Response({"success": False, "error": "missing-filename"}, status=status.HTTP_400_BAD_REQUEST)

        path = self._resolve_export_csv_path(filename)
        if not path:
            return Response({"success": False, "error": "invalid-filename"}, status=status.HTTP_400_BAD_REQUEST)
        if not path.exists():
            return Response({"success": False, "error": "file-not-found"}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(path.open("rb"), as_attachment=True, filename=path.name, content_type="text/csv")
        response["X-Server-File-Path"] = str(path)
        return response

    @action(detail=False, methods=["get"], url_path="csv_rows")
    def csv_rows(self, request):
        """
        从已生成的 CSV 中按需读取行（简单版：每次请求都 read_csv -> filter -> sort -> paginate）

        Query params:
            task_id: 必填
            page: 1-based，默认 1
            page_size: 默认 15
            sort: 列名（可选）
            order: asc/desc（默认 asc）
            keyword: 关键字（可选），在常用文本列做 contains 匹配
        """
        task_id = (request.query_params.get("task_id") or "").strip()
        if not task_id:
            return Response({"success": False, "error": "missing-task-id"}, status=status.HTTP_400_BAD_REQUEST)

        current_status = get_gripper_check_status(task_id=task_id) or {}
        if not current_status:
            return Response({"success": False, "error": "task-not-found"}, status=status.HTTP_404_NOT_FOUND)
        if (current_status.get("status") or "").lower() != "idle":
            return Response({"success": False, "error": "not-ready", **current_status}, status=status.HTTP_409_CONFLICT)

        latest = get_gripper_check_latest(task_id=task_id) or {}
        if not latest.get("success"):
            return Response({"success": False, "error": latest.get("error") or "no-latest"}, status=status.HTTP_404_NOT_FOUND)

        server_path = (latest.get("server_path") or "").strip()
        if not server_path:
            return Response({"success": False, "error": "missing-server-path"}, status=status.HTTP_404_NOT_FOUND)
        path = Path(server_path)
        if not path.exists():
            return Response({"success": False, "error": "file-not-found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            page = int(request.query_params.get("page", 1))
        except Exception:
            page = 1
        try:
            page_size = int(request.query_params.get("page_size", 15))
        except Exception:
            page_size = 15
        page = max(page, 1)
        page_size = min(max(page_size, 1), 500)

        sort_col = (request.query_params.get("sort") or "").strip()
        order = (request.query_params.get("order") or "asc").strip().lower()
        keyword = (request.query_params.get("keyword") or "").strip()

        return self._read_csv_page_response(path, page, page_size, sort_col, order, keyword)

    @action(detail=False, methods=["get"], url_path="csv_file_rows")
    def csv_file_rows(self, request):
        filename = (request.query_params.get("filename") or "").strip()
        if not filename:
            return Response({"success": False, "error": "missing-filename"}, status=status.HTTP_400_BAD_REQUEST)

        path = self._resolve_export_csv_path(filename)
        if not path:
            return Response({"success": False, "error": "invalid-filename"}, status=status.HTTP_400_BAD_REQUEST)
        if not path.exists():
            return Response({"success": False, "error": "file-not-found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            page = int(request.query_params.get("page", 1))
        except Exception:
            page = 1
        try:
            page_size = int(request.query_params.get("page_size", 15))
        except Exception:
            page_size = 15
        page = max(page, 1)
        page_size = min(max(page_size, 1), 500)
        sort_col = (request.query_params.get("sort") or "").strip()
        order = (request.query_params.get("order") or "asc").strip().lower()
        keyword = (request.query_params.get("keyword") or "").strip()

        return self._read_csv_page_response(path, page, page_size, sort_col, order, keyword)

    @action(detail=False, methods=["get"], url_path="csv_files")
    def csv_files(self, request):
        export_dir = self._get_gripper_export_dir()
        export_dir.mkdir(parents=True, exist_ok=True)

        files = []
        for path in sorted(export_dir.glob("*.csv"), key=lambda item: item.stat().st_mtime, reverse=True):
            stat_result = path.stat()
            files.append(
                {
                    "filename": path.name,
                    "server_path": str(path),
                    "size": int(stat_result.st_size),
                    "updated_at": datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.get_current_timezone()).isoformat(),
                }
            )

        return Response(
            {
                "success": True,
                "export_dir": str(export_dir),
                "files": files,
            }
        )

    @action(detail=False, methods=['get'])
    def status(self, request):
        task_id = (request.query_params.get("task_id") or "").strip()
        payload = get_gripper_check_status(task_id=task_id)
        if not payload:
            if task_id:
                return Response({"success": False, "error": "task-not-found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"status": "idle"})
        return Response(payload)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        task_id = (request.query_params.get("task_id") or "").strip()
        payload = get_gripper_check_latest(task_id=task_id)
        if not payload:
            return Response({"success": False, "error": "no-latest-result"}, status=status.HTTP_404_NOT_FOUND)
        return Response(payload)

    @action(detail=False, methods=['get'])
    def robot_tables(self, request):
        """
        获取可用的机器人表名列表（从RobotComponent获取robot）
        支持按车间(group_key)、type、tech 筛选和关键词(keyword)搜索

        参数:
            group: 车间key（可选）
            keyword: 搜索关键词（可选，支持robot、shop、tech等模糊搜索）

        返回:
        {
            "results": [
                {"value": "as33_020rb_400", "label": "as33_020rb_400", "shop": "MRA1", "group_key": "MRA1"},
                ...
            ]
        }
        """
        # 获取车间筛选参数
        group_key = request.query_params.get('group')
        keyword = request.query_params.get('keyword', '').strip()
        selected_types = self._parse_multi_query_param(request, "types")
        selected_techs = self._parse_multi_query_param(request, "techs")

        # 构建查询 - 使用 robot 字段而不是 part_no
        qs = RobotComponent.objects.values('robot', 'shop', 'group__key', 'type', 'tech').distinct()

        if group_key:
            qs = qs.filter(group__key=group_key)
        if selected_types:
            qs = qs.filter(type__in=selected_types)
        if selected_techs:
            qs = qs.filter(tech__in=selected_techs)

        # 支持关键词搜索
        if keyword:
            qs = qs.filter(
                Q(robot__icontains=keyword)
                | Q(shop__icontains=keyword)
                | Q(type__icontains=keyword)
                | Q(tech__icontains=keyword)
            )

        tables = qs.order_by('robot')

        results = []
        for t in tables:
            results.append({
                'value': t['robot'],
                'label': t['robot'],
                'robot_id': t['robot'],  # 兼容前端，使用 robot 作为 robot_id
                'shop': t.get('shop', ''),
                'group_key': t.get('group__key', ''),
                'type': t.get('type', '') or '',
                'tech': t.get('tech', '') or '',
            })

        return Response({'results': results})

    @action(detail=False, methods=["get"], url_path="filter_options")
    def filter_options(self, request):
        group_key = (request.query_params.get("group") or "").strip()
        qs = RobotComponent.objects.all()
        if group_key:
            qs = qs.filter(group__key=group_key)

        types = [
            value for value in qs.exclude(type__isnull=True).exclude(type__exact="").values_list("type", flat=True).distinct().order_by("type")
        ]
        techs = [
            value for value in qs.exclude(tech__isnull=True).exclude(tech__exact="").values_list("tech", flat=True).distinct().order_by("tech")
        ]

        return Response(
            {
                "success": True,
                "types": types,
                "techs": techs,
            }
        )

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


@require_GET
@xframe_options_exempt
def gripper_check_events(request):
    """
    Server-Sent Events: 推送关键轨迹检查状态与最终结果
    """
    import json as json_module

    task_id = (request.GET.get("task_id") or "").strip()
    if not task_id:
        return JsonResponse({"success": False, "error": "missing-task-id"}, status=400)

    def stream_generator():
        try:
            # 立即发送初始状态
            status_payload = get_gripper_check_status(task_id=task_id) or {"status": "queued", "task_id": task_id}
            yield f"event: status\ndata: {json_module.dumps(status_payload, ensure_ascii=False)}\n\n"

            last_status = status_payload.get("status", "idle").lower()

            last_ping = 0.0
            while True:
                try:
                    current_status = get_gripper_check_status(task_id=task_id) or {"status": "queued", "task_id": task_id}
                    current_value = current_status.get("status", "idle").lower()

                    # 心跳：避免代理/浏览器因长时间无数据而断开连接
                    now = time.time()
                    if now - last_ping >= 15:
                        yield ": ping\n\n"
                        last_ping = now

                    # 发送状态更新
                    if current_value != last_status:
                        yield f"event: status\ndata: {json_module.dumps(current_status, ensure_ascii=False)}\n\n"
                        last_status = current_value

                    # 检查是否完成
                    if current_value in ("idle", "failed", "cancelled"):
                        if current_value == "idle":
                            latest = get_gripper_check_latest(task_id=task_id)
                            if latest:
                                yield f"event: result\ndata: {json_module.dumps(latest, ensure_ascii=False)}\n\n"
                        break

                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Error in SSE loop: {e}")
                    yield f"event: error\ndata: {json_module.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                    break

        except Exception as e:
            logger.exception(f"Error in gripper_check_events: {e}")
            yield f"event: error\ndata: {json_module.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    response = StreamingHttpResponse(stream_generator(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


class RobotHighRiskSnapshotViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """历史高风险机器人 ViewSet - 读取 _robot_high_risk_snapshots 表"""
    queryset = RobotHighRiskSnapshot.objects.all()
    serializer_class = RobotHighRiskSnapshotSerializer
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "list":
            return RobotHighRiskSnapshotListSerializer
        return super().get_serializer_class()

    # 排除的车间 key 列表（与前端保持一致）
    EXCLUDED_GROUP_KEYS = ['', '(空)', '未分配']

    def get_queryset(self):
        """获取查询集，支持过滤"""
        qs = super().get_queryset()

        # 过滤排除的车间
        qs = qs.exclude(group__key__in=self.EXCLUDED_GROUP_KEYS)

        # 按车间筛选
        group = self.request.query_params.get('group')
        if group:
            qs = qs.filter(group__key=group)

        # 按等级筛选
        level = self.request.query_params.get('level')
        if level:
            # 支持多个 level 值（逗号分隔）
            levels = [l.strip() for l in level.split(',') if l.strip()]
            if len(levels) == 1:
                qs = qs.filter(level=levels[0])
            else:
                qs = qs.filter(level__in=levels)

        # 搜索关键词
        keyword = (self.request.query_params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(
                Q(robot__icontains=keyword)
                | Q(shop__icontains=keyword)
                | Q(reference__icontains=keyword)
                | Q(type__icontains=keyword)
                | Q(tech__icontains=keyword)
                | Q(remark__icontains=keyword)
            )

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
            axis_ok_bool = parse_axis_ok(axis_ok)
            if axis_ok_bool is True:
                # 轴状态为 ok（排除 high，允许空值代表正常）
                for k in axis_keys:
                    field = k.lower()
                    qs = qs.exclude(**{f"{field}__iexact": "high"})
            elif axis_ok_bool is False:
                # 轴状态为 high（所有所选轴都为 high）
                for k in axis_keys:
                    qs = qs.filter(**{f"{k.lower()}__iexact": "high"})

        sort_by = (self.request.query_params.get("sort_by") or "").strip()
        sort_order = (self.request.query_params.get("sort_order") or "").lower()
        if sort_order not in {"asc", "desc"}:
            sort_order = "asc"
        qs = apply_ordering(qs, sort_by, sort_order, SNAPSHOT_SORT_FIELDS)

        return qs


class RobotReferenceDictViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """机器人 reference 字典 - 从本地 CSV 刷新"""
    queryset = RobotReferenceDict.objects.all()
    serializer_class = RobotReferenceDictSerializer
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        robot = (self.request.query_params.get("robot") or "").strip()
        if robot:
            qs = qs.filter(robot=robot)
        return qs.order_by("reference")

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["post"])
    def refresh(self, request):
        from .tasks import refresh_reference_dict_task

        task = refresh_reference_dict_task.delay()
        return Response(
            {"task_id": task.id, "status": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["get"], url_path="refresh-status")
    def refresh_status(self, request):
        task_id = (request.query_params.get("task_id") or "").strip()
        if not task_id:
            return Response(
                {"error": "缺少参数 task_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = AsyncResult(task_id)
        payload = {"task_id": task_id, "status": result.status.lower()}
        if result.successful():
            payload["result"] = result.result
        elif result.failed():
            payload["error"] = str(result.result)
        return Response(payload)

    @action(detail=False, methods=["get"])
    def resolve(self, request):
        robot = (request.query_params.get("robot") or "").strip()
        reference = (request.query_params.get("reference") or "").strip()

        if not robot or not reference:
            return Response(
                {"error": "缺少参数 robot/reference"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        number = RobotReferenceDict.objects.filter(
            robot=robot,
            reference=reference,
        ).values_list("number", flat=True).first()

        if number is None:
            return Response(
                {"error": "未找到匹配的 number"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"robot": robot, "reference": reference, "number": number})


# API 端点：获取最后同步时间
@api_view(['GET'])
def get_last_sync_time(request):
    """
    获取最后同步时间（从 refresh_logs 表读取最新的记录）
    """
    from .models import RefreshLog

    # 获取最新的成功同步记录
    latest_log = RefreshLog.objects.filter(
        status="success"
    ).order_by('-sync_time').first()

    if latest_log:
        last_sync_time = latest_log.sync_time.isoformat()
        source = latest_log.get_source_display()
        source_file = latest_log.source_file
        records_created = latest_log.records_created
        records_updated = latest_log.records_updated
        records_deleted = latest_log.records_deleted
        total_records = latest_log.total_records
    else:
        last_sync_time = None
        source = None
        source_file = None
        records_created = 0
        records_updated = 0
        records_deleted = 0
        total_records = 0

    return Response({
        'last_sync_time': last_sync_time,
        'source': source,
        'source_file': source_file,
        'records_created': records_created,
        'records_updated': records_updated,
        'records_deleted': records_deleted,
        'total_records': total_records,
    })


@api_view(['GET'])
def get_refresh_logs(request):
    """获取刷新日志列表（按时间倒序）"""
    from .models import RefreshLog

    raw_limit = (request.query_params.get('limit') or '').strip()
    try:
        limit = int(raw_limit) if raw_limit else 12
    except ValueError:
        limit = 12

    limit = max(1, min(limit, 50))
    logs = RefreshLog.objects.all().order_by('-sync_time')[:limit]
    serializer = RefreshLogSerializer(logs, many=True)
    return Response({'logs': serializer.data})


def _tail_lines(file_path, max_lines=200, chunk_size=65536):
    if not os.path.exists(file_path):
        return []

    with open(file_path, "rb") as handle:
        handle.seek(0, os.SEEK_END)
        file_size = handle.tell()
        offset = min(file_size, chunk_size)
        handle.seek(-offset, os.SEEK_END)
        data = handle.read(offset)

    try:
        text = data.decode("utf-8", errors="ignore")
    except UnicodeDecodeError:
        text = data.decode("latin1", errors="ignore")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-max_lines:]


@api_view(['GET'])
def get_bi_logs(request):
    """获取BI加载相关的后端日志文本"""
    raw_limit = (request.query_params.get('limit') or '').strip()
    try:
        limit = int(raw_limit) if raw_limit else 8
    except ValueError:
        limit = 8

    limit = max(1, min(limit, 20))
    log_path = os.path.join(settings.BASE_DIR, "logs", "django.log")
    lines = _tail_lines(log_path)

    keywords = (
        "bokeh_charts",
        "请求时间范围",
        "主数据: db fetch",
        "加载数据条数",
        "能量数据: db fetch",
        "能量数据条数",
        "可用程序列表",
        "图表生成成功",
    )
    filtered = [line for line in lines if any(keyword in line for keyword in keywords)]
    return Response({"lines": filtered[-limit:]})


# API 端点：获取关键路径告警数据
@api_view(['GET'])
def get_keypath_warnings(request):
    """
    获取关键路径告警数据（从 keypath 数据库的 keypath_warn 表）

    查询参数:
        robot: 机器人名称（可选，按robot字段筛选）
        limit: 返回记录数限制（可选，默认10）

    返回:
        {
            "recent_alerts": [
                {
                    "id": 1,
                    "robot": "VB25_130RB_100",
                    "name_c": "/R1/tool_1_couple.SRC",
                    "p_name": "XL_BHF_NP005",
                    "time": "2026-02-06T10:12:39",
                    "triggered_at": "2026-02-06T10:12:39"
                },
                ...
            ]
        }
    """
    import os
    from pymysql import Connect
    from datetime import datetime

    robot = request.query_params.get('robot', '').strip()
    limit = int(request.query_params.get('limit', 10))

    try:
        # 连接到 keypath 数据库
        connection = Connect(
            host=os.getenv('KEY_DB_HOST', '20.212.53.247'),
            port=int(os.getenv('KEY_DB_PORT', 3306)),
            user=os.getenv('KEY_DB_USER', 'key'),
            password=os.getenv('KEY_DB_PASSWORD', '123456'),
            database=os.getenv('KEY_DB_NAME', 'keypath_warn'),
            charset='utf8mb4'
        )

        with connection.cursor() as cursor:
            # 构建查询（注意：表没有id字段，需要用其他方式生成）
            if robot:
                sql = """
                    SELECT robot, Name_C, P_name, time
                    FROM keypath_warn
                    WHERE robot = %s
                    ORDER BY time DESC
                    LIMIT %s
                """
                cursor.execute(sql, (robot, limit))
            else:
                sql = """
                    SELECT robot, Name_C, P_name, time
                    FROM keypath_warn
                    ORDER BY time DESC
                    LIMIT %s
                """
                cursor.execute(sql, (limit,))

            results = cursor.fetchall()

            # 转换为前端期望的格式
            recent_alerts = []
            for idx, row in enumerate(results, 1):
                # 处理时间格式
                time_val = row[3]
                if isinstance(time_val, datetime):
                    triggered_at = time_val.isoformat()
                else:
                    triggered_at = str(time_val) if time_val else None

                # 按照用户要求格式显示：robot在程序Name_C中的P_name轨迹点扭矩持续升高
                robot = row[0] or ''
                name_c = row[1] or ''
                p_name = row[2] or '未指定轨迹点'

                # 如果P_name为空，显示不同的消息
                if row[2] and row[2].strip():
                    message = f"{robot}在程序{name_c}中的{p_name}轨迹点扭矩持续升高"
                else:
                    message = f"{robot}在程序{name_c}中检测到扭矩持续升高"

                recent_alerts.append({
                    'id': idx,  # 使用索引作为id
                    'robot': robot,
                    'name_c': name_c,
                    'p_name': p_name,
                    'time': triggered_at,
                    'triggered_at': triggered_at,
                    'robot_name': robot,  # 兼容前端显示
                    'message': message
                })

        return Response({
            'recent_alerts': recent_alerts
        })

    except Exception as e:
        logger.error(f"获取关键路径告警失败: {e}")
        return Response({
            'recent_alerts': []
        })
