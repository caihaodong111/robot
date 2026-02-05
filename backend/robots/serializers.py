from rest_framework import serializers

from .models import RobotGroup, RobotComponent, RiskEvent, RobotHighRiskSnapshot, RefreshLog, RobotReferenceDict


class RobotGroupSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()

    class Meta:
        model = RobotGroup
        fields = ("id", "key", "name", "expected_total", "stats")

    def get_stats(self, obj: RobotGroup):
        stats = getattr(obj, "_stats", None)
        if stats is not None:
            return stats
        return {
            "total": obj.components.count(),
            "highRisk": obj.components.filter(level="H").count(),
        }


class RobotComponentSerializer(serializers.ModelSerializer):
    """机器人组件序列化器 - 严格按照 CSV 字段设计"""
    group = serializers.CharField(source="group.key", read_only=True)
    isHighRisk = serializers.BooleanField(source="is_high_risk", read_only=True)
    referenceNo = serializers.CharField(source="reference", required=False, allow_blank=True)

    class Meta:
        model = RobotComponent
        fields = (
            "id",
            "group",
            "robot",
            "shop",
            "reference",
            "referenceNo",
            "number",
            "type",
            "tech",
            "mark",
            "remark",
            # 错误率和温度
            "error1_c1",
            "tem1_m",
            "tem2_m",
            "tem3_m",
            "tem4_m",
            "tem5_m",
            "tem6_m",
            "tem7_m",
            # A1-A7 错误率
            "a1_e_rate",
            "a2_e_rate",
            "a3_e_rate",
            "a4_e_rate",
            "a5_e_rate",
            "a6_e_rate",
            "a7_e_rate",
            # A1-A7 RMS
            "a1_rms",
            "a2_rms",
            "a3_rms",
            "a4_rms",
            "a5_rms",
            "a6_rms",
            "a7_rms",
            # A1-A7 E值
            "a1_e",
            "a2_e",
            "a3_e",
            "a4_e",
            "a5_e",
            "a6_e",
            "a7_e",
            # Q1-Q7
            "q1",
            "q2",
            "q3",
            "q4",
            "q5",
            "q6",
            "q7",
            # 最大电流
            "curr_a1_max",
            "curr_a2_max",
            "curr_a3_max",
            "curr_a4_max",
            "curr_a5_max",
            "curr_a6_max",
            "curr_a7_max",
            # 最小电流
            "curr_a1_min",
            "curr_a2_min",
            "curr_a3_min",
            "curr_a4_min",
            "curr_a5_min",
            "curr_a6_min",
            "curr_a7_min",
            # A1-A7 电流值
            "a1",
            "a2",
            "a3",
            "a4",
            "a5",
            "a6",
            "a7",
            # 其他
            "p_change",
            "level",
            "isHighRisk",
            # 元数据
            "created_at",
            "updated_at",
        )


class RobotReferenceDictSerializer(serializers.ModelSerializer):
    class Meta:
        model = RobotReferenceDict
        fields = ("id", "robot", "reference", "number", "created_at", "updated_at")


class RefreshLogSerializer(serializers.ModelSerializer):
    """刷新日志序列化器"""
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RefreshLog
        fields = (
            "id",
            "source",
            "source_display",
            "status",
            "status_display",
            "source_file",
            "file_date",
            "records_created",
            "records_updated",
            "records_deleted",
            "total_records",
            "error_message",
            "sync_time",
        )


class RiskEventSerializer(serializers.ModelSerializer):
    group = serializers.CharField(source="group.key", read_only=True)

    class Meta:
        model = RiskEvent
        fields = (
            "id",
            "robot_id",
            "robot_name",
            "group",
            "message",
            "reason",
            "severity",
            "status",
            "risk_score",
            "notes",
            "triggered_at",
        )


class BIRobotSerializer(serializers.Serializer):
    """BI可视化机器人选择器序列化器"""
    value = serializers.CharField(source="robot", help_text="机器人表名")
    label = serializers.CharField(help_text="显示标签")
    robot_id = serializers.CharField(source="robot", help_text="机器人ID")

    def to_representation(self, instance):
        """自定义输出格式"""
        return {
            "value": instance.robot,  # BI使用的表名
            "label": f"{instance.robot}",
            "robot_id": instance.robot,
        }


class GripperCheckSerializer(serializers.Serializer):
    """关键轨迹检查序列化器"""
    start_time = serializers.DateTimeField(help_text="开始时间")
    end_time = serializers.DateTimeField(help_text="结束时间")
    gripper_list = serializers.ListField(
        child=serializers.CharField(),
        help_text="机器人表名列表"
    )
    key_paths = serializers.ListField(
        child=serializers.CharField(required=False, allow_blank=True),
        required=False,
        help_text="关键路径关键字列表，如 ['R1/CO', 'R1/DO']"
    )

    def validate(self, attrs):
        """验证时间范围"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        if start_time and end_time:
            time_span = end_time - start_time

            if time_span.total_seconds() <= 0:
                raise serializers.ValidationError(
                    "结束时间必须大于开始时间"
                )

        return attrs


class GripperCheckResultSerializer(serializers.Serializer):
    """关键轨迹检查结果序列化器"""
    success = serializers.BooleanField()
    count = serializers.IntegerField()
    data = serializers.ListField(child=serializers.DictField(), required=False)
    columns = serializers.ListField(child=serializers.CharField(), required=False)
    error = serializers.CharField(required=False, allow_blank=True)


class RobotHighRiskSnapshotSerializer(serializers.ModelSerializer):
    """高风险机器人快照序列化器 - 与 RobotComponent 字段完全一致"""
    group = serializers.CharField(source="group.key", read_only=True)
    isHighRisk = serializers.BooleanField(source="is_high_risk", read_only=True)

    class Meta:
        model = RobotHighRiskSnapshot
        fields = (
            "id",
            "group",
            "robot",
            "shop",
            "reference",
            "number",
            "type",
            "tech",
            "mark",
            "remark",
            # 错误率和温度
            "error1_c1",
            "tem1_m",
            "tem2_m",
            "tem3_m",
            "tem4_m",
            "tem5_m",
            "tem6_m",
            "tem7_m",
            # A1-A7 错误率
            "a1_e_rate",
            "a2_e_rate",
            "a3_e_rate",
            "a4_e_rate",
            "a5_e_rate",
            "a6_e_rate",
            "a7_e_rate",
            # A1-A7 RMS
            "a1_rms",
            "a2_rms",
            "a3_rms",
            "a4_rms",
            "a5_rms",
            "a6_rms",
            "a7_rms",
            # A1-A7 E值
            "a1_e",
            "a2_e",
            "a3_e",
            "a4_e",
            "a5_e",
            "a6_e",
            "a7_e",
            # Q1-Q7
            "q1",
            "q2",
            "q3",
            "q4",
            "q5",
            "q6",
            "q7",
            # 最大电流
            "curr_a1_max",
            "curr_a2_max",
            "curr_a3_max",
            "curr_a4_max",
            "curr_a5_max",
            "curr_a6_max",
            "curr_a7_max",
            # 最小电流
            "curr_a1_min",
            "curr_a2_min",
            "curr_a3_min",
            "curr_a4_min",
            "curr_a5_min",
            "curr_a6_min",
            "curr_a7_min",
            # A1-A7 状态字符串
            "a1",
            "a2",
            "a3",
            "a4",
            "a5",
            "a6",
            "a7",
            # 其他
            "p_change",
            "level",
            "isHighRisk",
            # 元数据
            "created_at",
            "updated_at",
        )


class RefreshLogSerializer(serializers.ModelSerializer):
    """刷新日志序列化器"""
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RefreshLog
        fields = (
            "id",
            "source",
            "source_display",
            "status",
            "status_display",
            "source_file",
            "file_date",
            "records_created",
            "records_updated",
            "records_deleted",
            "total_records",
            "error_message",
            "sync_time",
        )
