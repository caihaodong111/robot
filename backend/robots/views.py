from datetime import datetime, timedelta
from collections import defaultdict
from django.db import connection
from django.db.models import Count, Q, Avg, Min, Max
from django.db.models.functions import TruncHour
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import RiskEvent, RobotComponent, RobotGroup, RobotAxisData
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def axis_range(request):
    """
    Get available timestamp range for a robot (part_no).
    Query parameters:
    - part_no: Robot part number (e.g., 'AS33_020RB_400')
    """
    part_no = request.query_params.get("part_no", "").upper()
    if not part_no:
        return Response({"error": "part_no is required"}, status=400)

    agg = RobotAxisData.objects.filter(part_no=part_no).aggregate(
        min_ts=Min("timestamp"),
        max_ts=Max("timestamp"),
    )

    if not agg["min_ts"] or not agg["max_ts"]:
        return Response({"error": "No data found", "start_time": None, "end_time": None}, status=404)

    return Response(
        {
            "part_no": part_no,
            "start_time": agg["min_ts"].strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": agg["max_ts"].strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def axis_data(request):
    """
    Get axis time series and aggregated data for a robot
    Query parameters:
    - part_no: Robot part number (e.g., 'AS33_020RB_400')
    - axis: Axis key (A1-A7)
    - start_time: Optional start time (default: 30 days ago)
    - end_time: Optional end time (default: now)
    - program: Optional program/application filter (matches Name_C)
    """
    part_no = request.query_params.get("part_no", "").upper()
    axis = request.query_params.get("axis", "A1")
    program = (request.query_params.get("program") or "").strip()

    if not part_no:
        return Response({"error": "part_no is required"}, status=400)

    # Default time range: last 30 days
    end_time = request.query_params.get("end_time")
    start_time = request.query_params.get("start_time")

    def _quantile_nearest(sorted_values, q: float):
        if not sorted_values:
            return 0
        idx = int(round((len(sorted_values) - 1) * q))
        idx = max(0, min(idx, len(sorted_values) - 1))
        return sorted_values[idx]

    def _get_table_name_candidates(part_no_value: str):
        return [part_no_value, part_no_value.lower(), part_no_value.upper()]

    def _find_existing_table(part_no_value: str):
        try:
            with connection.cursor() as cursor:
                for candidate in _get_table_name_candidates(part_no_value):
                    cursor.execute("SHOW TABLES LIKE %s", [candidate])
                    if cursor.fetchone():
                        return candidate
        except Exception:
            return None
        return None

    def _get_table_columns(table_name_value: str):
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW COLUMNS FROM `{table_name_value}`")
            return [row[0] for row in cursor.fetchall()]

    def _fetch_programs_from_table(table_name_value: str, time_col: str, start_dt_value, end_dt_value):
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT DISTINCT `Name_C` FROM `{table_name_value}` WHERE `{time_col}` BETWEEN %s AND %s AND `Name_C` IS NOT NULL AND `Name_C` != ''",
                [start_dt_value, end_dt_value],
            )
            return sorted([row[0] for row in cursor.fetchall() if row and row[0]])

    def _fetch_rows_from_table(table_name_value: str, time_col: str, cols: list[str], start_dt_value, end_dt_value, program_value: str):
        where = [f"`{time_col}` BETWEEN %s AND %s"]
        params = [start_dt_value, end_dt_value]
        if program_value:
            where.append("`Name_C` = %s")
            params.append(program_value)
        select_cols = ", ".join([f"`{c}`" for c in cols])
        sql = f"SELECT {select_cols} FROM `{table_name_value}` WHERE {' AND '.join(where)} ORDER BY `{time_col}` ASC LIMIT 10000"
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return rows

    def _fetch_recent_rows_from_table(table_name_value: str, time_col: str, cols: list[str], program_value: str, limit: int = 1000):
        where = []
        params = []
        if program_value:
            where.append("`Name_C` = %s")
            params.append(program_value)
        select_cols = ", ".join([f"`{c}`" for c in cols])
        sql = f"SELECT {select_cols} FROM `{table_name_value}`"
        if where:
            sql += f" WHERE {' AND '.join(where)}"
        sql += f" ORDER BY `{time_col}` DESC LIMIT {int(limit)}"
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return rows

    try:
        # Parse datetime if provided
        if end_time:
            end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        else:
            end_dt = datetime.now()

        if start_time:
            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        else:
            start_dt = datetime.now() - timedelta(days=30)

        axis_table_map = {
            "A1": {"curr": "Curr_A1", "max": "MAXCurr_A1", "min": "MinCurr_A1", "temp": "Tem_1", "pos": "AxisP1", "speed": "Speed1", "torque": "Torque1", "fol": "Fol1", "lq": "Curr_A1_LQ", "hq": "Curr_A1_HQ"},
            "A2": {"curr": "Curr_A2", "max": "MAXCurr_A2", "min": "MinCurr_A2", "temp": "Tem_2", "pos": "AxisP2", "speed": "Speed2", "torque": "Torque2", "fol": "Fol2", "lq": "Curr_A2_LQ", "hq": "Curr_A2_HQ"},
            "A3": {"curr": "Curr_A3", "max": "MAXCurr_A3", "min": "MinCurr_A3", "temp": "Tem_3", "pos": "AxisP3", "speed": "Speed3", "torque": "Torque3", "fol": "Fol3", "lq": "Curr_A3_LQ", "hq": "Curr_A3_HQ"},
            "A4": {"curr": "Curr_A4", "max": "MAXCurr_A4", "min": "MinCurr_A4", "temp": "Tem_4", "pos": "AxisP4", "speed": "Speed4", "torque": "Torque4", "fol": "Fol4", "lq": "Curr_A4_LQ", "hq": "Curr_A4_HQ"},
            "A5": {"curr": "Curr_A5", "max": "MAXCurr_A5", "min": "MinCurr_A5", "temp": "Tem_5", "pos": "AxisP5", "speed": "Speed5", "torque": "Torque5", "fol": "Fol5", "lq": "Curr_A5_LQ", "hq": "Curr_A5_HQ"},
            "A6": {"curr": "Curr_A6", "max": "MAXCurr_A6", "min": "MinCurr_A6", "temp": "Tem_6", "pos": "AxisP6", "speed": "Speed6", "torque": "Torque6", "fol": "Fol6", "lq": "Curr_A6_LQ", "hq": "Curr_A6_HQ"},
            "A7": {"curr": "Curr_E1", "max": "MAXCurr_E1", "min": "MinCurr_E1", "temp": "Tem_7", "pos": "AxisP7", "speed": "Speed7", "torque": "Torque7", "fol": "Fol7", "lq": "Curr_E1_LQ", "hq": "Curr_E1_HQ"},
        }
        table_field_map = axis_table_map.get(axis, axis_table_map["A1"])

        # Prefer querying robot-specific raw table if present (supports Name_C program/application)
        table_name = _find_existing_table(part_no)
        if table_name:
            cols = _get_table_columns(table_name)
            cols_set = set(cols)

            time_col = "Timestamp" if "Timestamp" in cols_set else ("timestamp" if "timestamp" in cols_set else None)
            if time_col and "Name_C" in cols_set and "SNR_C" in cols_set:
                required = [time_col, "SNR_C", "P_name", "Name_C"] + [
                    table_field_map["curr"],
                    table_field_map["max"],
                    table_field_map["min"],
                    table_field_map["temp"],
                    table_field_map["pos"],
                    table_field_map["speed"],
                    table_field_map["torque"],
                    table_field_map["fol"],
                ]
                missing = [c for c in required if c not in cols_set]
                if not missing:
                    programs = _fetch_programs_from_table(table_name, time_col, start_dt, end_dt)
                    raw_rows = _fetch_rows_from_table(table_name, time_col, required, start_dt, end_dt, program)

                    if not raw_rows:
                        raw_rows = _fetch_recent_rows_from_table(table_name, time_col, required, program, limit=1000)
                        if not raw_rows:
                            return Response(
                                {
                                    "error": "No data found",
                                    "data": None,
                                    "aggregated": None,
                                    "programs": programs,
                                    "program": program,
                                },
                                status=404,
                            )

                        # recent rows are DESC; reverse to ASC
                        raw_rows = list(reversed(raw_rows))

                    # Build data list
                    data_list = []
                    for idx, row in enumerate(raw_rows, start=1):
                        row_dict = dict(zip(required, row))
                        ts = row_dict.get(time_col)
                        if isinstance(ts, datetime):
                            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            ts_str = str(ts) if ts is not None else ""

                        data_item = {
                            "sort": idx,
                            "Timestamp": ts_str,
                            "SNR_C": row_dict.get("SNR_C"),
                            "P_name": row_dict.get("P_name") or "",
                            "Name_C": row_dict.get("Name_C") or "",
                        }
                        for k in [
                            table_field_map["curr"],
                            table_field_map["max"],
                            table_field_map["min"],
                            table_field_map["temp"],
                            table_field_map["pos"],
                            table_field_map["speed"],
                            table_field_map["torque"],
                            table_field_map["fol"],
                        ]:
                            data_item[k] = row_dict.get(k)
                        data_list.append(data_item)

                    # Aggregate by SNR_C (quantile like Digitaltwin_timefree.py)
                    snr_groups = defaultdict(list)
                    for item in data_list:
                        snr_groups[item["SNR_C"]].append(item)

                    aggregated_list = []
                    for snr in sorted([k for k in snr_groups.keys() if k is not None]):
                        items = snr_groups[snr]
                        last_item = items[-1]

                        curr_key = table_field_map["curr"]
                        curr_values = []
                        for it in items:
                            v = it.get(curr_key)
                            if v is None:
                                continue
                            try:
                                curr_values.append(float(v))
                            except Exception:
                                continue
                        curr_values.sort()
                        lq_value = _quantile_nearest(curr_values, 0.01)
                        hq_value = _quantile_nearest(curr_values, 0.99)

                        aggregated_list.append(
                            {
                                "SNR_C": str(snr),
                                "P_name": last_item.get("P_name", ""),
                                "Name_C": last_item.get("Name_C", ""),
                                table_field_map["lq"]: lq_value,
                                table_field_map["hq"]: hq_value,
                                table_field_map["min"]: last_item.get(table_field_map["min"]),
                                table_field_map["max"]: last_item.get(table_field_map["max"]),
                            }
                        )

                    # Derive time range from returned rows
                    first_ts = data_list[0]["Timestamp"] if data_list else ""
                    last_ts = data_list[-1]["Timestamp"] if data_list else ""

                    return Response(
                        {
                            "table_name": table_name,
                            "axis": axis,
                            "start_time": first_ts,
                            "end_time": last_ts,
                            "data": data_list,
                            "aggregated": aggregated_list,
                            "total_records": len(data_list),
                            "programs": programs,
                            "program": program,
                        }
                    )

        # Fallback: query from RobotAxisData model (does not include Name_C; `program` falls back to p_name)
        base_queryset = RobotAxisData.objects.filter(
            part_no=part_no,
            timestamp__gte=start_dt,
            timestamp__lte=end_dt
        )

        # Program dropdown options should come from DB (range-based, not affected by program filter)
        programs = list(
            base_queryset.exclude(p_name__isnull=True)
            .exclude(p_name="")
            .values_list("p_name", flat=True)
            .distinct()
        )

        # Apply optional program filter for data returned
        queryset = base_queryset
        if program:
            queryset = queryset.filter(p_name=program)

        queryset = queryset.order_by('timestamp')

        data_count = queryset.count()

        # If no data in range, get most recent data
        if data_count == 0:
            fallback_base = RobotAxisData.objects.filter(part_no=part_no)
            programs = list(
                fallback_base.exclude(p_name__isnull=True)
                .exclude(p_name="")
                .values_list("p_name", flat=True)
                .distinct()
            )

            fallback_qs = fallback_base
            if program:
                fallback_qs = fallback_qs.filter(p_name=program)

            queryset = fallback_qs.order_by('-timestamp')[:1000]

            if queryset.count() == 0:
                return Response(
                    {
                        "error": "No data found",
                        "data": None,
                        "aggregated": None,
                        "programs": sorted(programs),
                        "program": program,
                    }
                )

            # Update time range for response
            start_dt = queryset.last().timestamp
            end_dt = queryset.first().timestamp
            queryset = list(queryset)
        else:
            queryset = list(queryset)

        # Field mapping for axis configuration
        axis_field_map = {
            'A1': {'curr': 'curr_a1', 'max': 'max_curr_a1', 'min': 'min_curr_a1', 'temp': 'tem_1', 'pos': 'axisp1', 'lq': 'curr_a1_lq', 'hq': 'curr_a1_hq', 'speed': 'speed1', 'torque': 'torque1', 'fol': 'fol1'},
            'A2': {'curr': 'curr_a2', 'max': 'max_curr_a2', 'min': 'min_curr_a2', 'temp': 'tem_2', 'pos': 'axisp2', 'lq': 'curr_a2_lq', 'hq': 'curr_a2_hq', 'speed': 'speed2', 'torque': 'torque2', 'fol': 'fol2'},
            'A3': {'curr': 'curr_a3', 'max': 'max_curr_a3', 'min': 'min_curr_a3', 'temp': 'tem_3', 'pos': 'axisp3', 'lq': 'curr_a3_lq', 'hq': 'curr_a3_hq', 'speed': 'speed3', 'torque': 'torque3', 'fol': 'fol3'},
            'A4': {'curr': 'curr_a4', 'max': 'max_curr_a4', 'min': 'min_curr_a4', 'temp': 'tem_4', 'pos': 'axisp4', 'lq': 'curr_a4_lq', 'hq': 'curr_a4_hq', 'speed': 'speed4', 'torque': 'torque4', 'fol': 'fol4'},
            'A5': {'curr': 'curr_a5', 'max': 'max_curr_a5', 'min': 'min_curr_a5', 'temp': 'tem_5', 'pos': 'axisp5', 'lq': 'curr_a5_lq', 'hq': 'curr_a5_hq', 'speed': 'speed5', 'torque': 'torque5', 'fol': 'fol5'},
            'A6': {'curr': 'curr_a6', 'max': 'max_curr_a6', 'min': 'min_curr_a6', 'temp': 'tem_6', 'pos': 'axisp6', 'lq': 'curr_a6_lq', 'hq': 'curr_a6_hq', 'speed': 'speed6', 'torque': 'torque6', 'fol': 'fol6'},
            'A7': {'curr': 'curr_e1', 'max': 'max_curr_e1', 'min': 'min_curr_e1', 'temp': 'tem_7', 'pos': 'axisp7', 'lq': 'curr_e1_lq', 'hq': 'curr_e1_hq', 'speed': 'speed7', 'torque': 'torque7', 'fol': 'fol7'},
        }

        field_map = axis_field_map.get(axis, axis_field_map['A1'])

        # Build data list for response
        data_list = []
        sort_idx = 1
        for item in queryset:
            data_item = {
                'sort': sort_idx,
                'Timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'SNR_C': item.snr_c,
                'P_name': item.p_name or '',
                field_map['curr']: getattr(item, field_map['curr']),
                field_map['max']: getattr(item, field_map['max']),
                field_map['min']: getattr(item, field_map['min']),
                field_map['temp']: getattr(item, field_map['temp']),
                field_map['pos']: getattr(item, field_map['pos']),
                field_map['speed']: getattr(item, field_map['speed']),
                field_map['torque']: getattr(item, field_map['torque']),
                field_map['fol']: getattr(item, field_map['fol']),
            }

            # Add all fields for all axes
            for i in range(1, 7):
                data_item[f'Curr_A{i}'] = getattr(item, f'curr_a{i}', None)
                data_item[f'MAXCurr_A{i}'] = getattr(item, f'max_curr_a{i}', None)
                data_item[f'MinCurr_A{i}'] = getattr(item, f'min_curr_a{i}', None)
                data_item[f'Tem_{i}'] = getattr(item, f'tem_{i}', None)
                data_item[f'AxisP{i}'] = getattr(item, f'axisp{i}', None)
                data_item[f'Speed{i}'] = getattr(item, f'speed{i}', None)
                data_item[f'Torque{i}'] = getattr(item, f'torque{i}', None)
                data_item[f'Fol{i}'] = getattr(item, f'fol{i}', None)

            # E1 axis (A7)
            data_item['Curr_E1'] = getattr(item, 'curr_e1', None)
            data_item['MAXCurr_E1'] = getattr(item, 'max_curr_e1', None)
            data_item['MinCurr_E1'] = getattr(item, 'min_curr_e1', None)
            data_item['Tem_7'] = getattr(item, 'tem_7', None)
            data_item['AxisP7'] = getattr(item, 'axisp7', None)
            data_item['Speed7'] = getattr(item, 'speed7', None)
            data_item['Torque7'] = getattr(item, 'torque7', None)
            data_item['Fol7'] = getattr(item, 'fol7', None)

            data_list.append(data_item)
            sort_idx += 1

        # Calculate aggregated data by SNR_C
        snr_groups = defaultdict(list)
        for item in data_list:
            snr_groups[item['SNR_C']].append(item)

        aggregated_list = []
        for snr in sorted(snr_groups.keys()):
            items = snr_groups[snr]
            last_item = items[-1]

            # Calculate quantiles
            curr_values = [item[field_map['curr']] for item in items if item[field_map['curr']] is not None]
            curr_values.sort()

            lq_value = curr_values[0] if curr_values else 0
            hq_value = curr_values[-1] if curr_values else 0

            agg_item = {
                'SNR_C': str(snr),
                'P_name': last_item.get('P_name', ''),
                field_map['lq']: lq_value,
                field_map['hq']: hq_value,
                field_map['min']: last_item.get(field_map['min']),
                field_map['max']: last_item.get(field_map['max']),
            }

            # Add all LQ and HQ fields for all axes
            for i in range(1, 7):
                agg_item[f'Curr_A{i}_LQ'] = lq_value
                agg_item[f'Curr_A{i}_HQ'] = hq_value
                agg_item[f'MinCurr_A{i}'] = last_item.get(f'MinCurr_A{i}')
                agg_item[f'MAXCurr_A{i}'] = last_item.get(f'MAXCurr_A{i}')

            agg_item[f'Curr_E1_LQ'] = lq_value
            agg_item[f'Curr_E1_HQ'] = hq_value
            agg_item['MinCurr_E1'] = last_item.get('MinCurr_E1')
            agg_item['MAXCurr_E1'] = last_item.get('MAXCurr_E1')

            aggregated_list.append(agg_item)

        response_data = {
            'table_name': part_no.lower(),
            'axis': axis,
            'start_time': start_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'data': data_list,
            'aggregated': aggregated_list,
            'total_records': len(data_list),
            'programs': sorted(programs),
            'program': program,
        }

        return Response(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)
