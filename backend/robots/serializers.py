from rest_framework import serializers

from .models import RobotGroup, RobotComponent, RiskEvent, WeeklyResult, HighRiskHistory


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
            "online": obj.components.filter(status="online").count(),
            "offline": obj.components.filter(status="offline").count(),
            "maintenance": obj.components.filter(status="maintenance").count(),
            "highRisk": obj.components.filter(level="H").count(),
            "historyHighRisk": obj.components.exclude(risk_history=[]).count(),
        }


class RobotComponentSerializer(serializers.ModelSerializer):
    group = serializers.CharField(source="group.key", read_only=True)
    partNo = serializers.CharField(source="part_no")
    referenceNo = serializers.CharField(source="reference_no")
    typeSpec = serializers.CharField(source="type_spec")
    number = serializers.IntegerField()
    motorTemp = serializers.IntegerField(source="motor_temp")
    networkLatency = serializers.IntegerField(source="network_latency")
    riskScore = serializers.IntegerField(source="risk_score")
    riskLevel = serializers.CharField(source="risk_level")
    riskHistory = serializers.JSONField(source="risk_history")
    lastSeen = serializers.DateTimeField(source="last_seen")
    isHighRisk = serializers.BooleanField(source="is_high_risk", read_only=True)

    class Meta:
        model = RobotComponent
        fields = (
            "id",
            "group",
            "robot_id",
            "name",
            "partNo",
            "referenceNo",
            "number",
            "typeSpec",
            "tech",
            "mark",
            "remark",
            "checks",
            "level",
            "status",
            "battery",
            "health",
            "motorTemp",
            "networkLatency",
            "riskScore",
            "riskLevel",
            "riskHistory",
            "lastSeen",
            "isHighRisk",
            # 详细数据字段
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
            "a1",
            "a2",
            "a3",
            "a4",
            "a5",
            "a6",
            "a7",
            "p_change",
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
    value = serializers.CharField(source="part_no", help_text="机器人表名")
    label = serializers.CharField(help_text="显示标签")
    robot_id = serializers.CharField(help_text="机器人ID")

    def to_representation(self, instance):
        """自定义输出格式"""
        return {
            "value": instance.part_no,  # BI使用的表名
            "label": f"{instance.robot_id} ({instance.part_no})",
            "robot_id": instance.robot_id,
            "name": instance.name,
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


class WeeklyResultSerializer(serializers.ModelSerializer):
    """周结果数据序列化器"""
    isHighRisk = serializers.BooleanField(source='is_high_risk', read_only=True)

    class Meta:
        model = WeeklyResult
        fields = (
            "id",
            "robot",
            "shop",
            "reference",
            "number",
            "type",
            "tech",
            "mark",
            "remark",
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
            "a1",
            "a2",
            "a3",
            "a4",
            "a5",
            "a6",
            "a7",
            "p_change",
            "level",
            "source_file",
            "week_start",
            "week_end",
            "created_at",
            "updated_at",
            "isHighRisk",
        )


class WeeklyResultListSerializer(serializers.ModelSerializer):
    """周结果数据列表序列化器（精简版）"""
    isHighRisk = serializers.BooleanField(source='is_high_risk', read_only=True)
    avgErrorRate = serializers.SerializerMethodField()

    class Meta:
        model = WeeklyResult
        fields = (
            "id",
            "robot",
            "shop",
            "type",
            "tech",
            "level",
            "remark",
            "source_file",
            "week_start",
            "week_end",
            "updated_at",
            "isHighRisk",
            "avgErrorRate",
        )

    def get_avgErrorRate(self, obj):
        """计算平均错误率"""
        rates = [obj.a1_e_rate, obj.a2_e_rate, obj.a3_e_rate,
                 obj.a4_e_rate, obj.a5_e_rate, obj.a6_e_rate, obj.a7_e_rate]
        valid_rates = [r for r in rates if r is not None]
        if valid_rates:
            return sum(valid_rates) / len(valid_rates)
        return None


class WeeklyResultImportSerializer(serializers.Serializer):
    """周结果数据导入序列化器"""
    folder_path = serializers.CharField(required=False, allow_blank=True, help_text="文件夹路径")
    project = serializers.CharField(required=False, default='reuse', help_text="项目名称")
    file_path = serializers.CharField(required=False, allow_blank=True, help_text="直接指定文件路径")


class WeeklyResultFileSerializer(serializers.Serializer):
    """周结果 CSV 文件列表序列化器"""
    path = serializers.CharField()
    name = serializers.CharField()
    created_time = serializers.CharField()
    week_start = serializers.CharField(allow_null=True)
    week_end = serializers.CharField(allow_null=True)


class HighRiskHistorySerializer(serializers.ModelSerializer):
    """历史高风险机器人序列化器"""
    group = serializers.CharField(source="group_key", read_only=True)
    groupName = serializers.CharField(source="group_name", read_only=True)
    partNo = serializers.CharField(source="part_no")
    referenceNo = serializers.CharField(source="reference_no")
    typeSpec = serializers.CharField(source="type_spec")
    number = serializers.IntegerField()
    motorTemp = serializers.IntegerField(source="motor_temp")
    networkLatency = serializers.IntegerField(source="network_latency")
    riskScore = serializers.IntegerField(source="risk_score")
    riskLevel = serializers.CharField(source="risk_level")
    lastSeen = serializers.DateTimeField(source="last_seen")
    isHighRisk = serializers.BooleanField(source="is_high_risk", read_only=True)
    syncTime = serializers.DateTimeField(source="sync_time")
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = HighRiskHistory
        fields = (
            "id",
            "group",
            "groupName",
            "robot_id",
            "name",
            "partNo",
            "referenceNo",
            "number",
            "typeSpec",
            "tech",
            "mark",
            "remark",
            "checks",
            "level",
            "status",
            "battery",
            "health",
            "motorTemp",
            "networkLatency",
            "riskScore",
            "riskLevel",
            "lastSeen",
            "isHighRisk",
            "record_source",
            "syncTime",
            "createdAt",
        )
