from rest_framework import serializers

from .models import RobotGroup, RobotComponent, RiskEvent


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
