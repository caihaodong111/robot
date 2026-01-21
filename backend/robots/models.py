from django.db import models


class RobotGroup(models.Model):
    key = models.CharField(max_length=32, unique=True, verbose_name="组Key")
    name = models.CharField(max_length=64, verbose_name="组名称")
    expected_total = models.PositiveIntegerField(default=0, verbose_name="预期数量")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "robot_groups"
        verbose_name = "机器人组"
        verbose_name_plural = "机器人组"
        ordering = ["key"]

    def __str__(self):
        return f"{self.name} ({self.key})"


class RobotComponent(models.Model):
    STATUS_CHOICES = [
        ("online", "在线"),
        ("offline", "离线"),
        ("maintenance", "维护中"),
    ]

    RISK_LEVEL_CHOICES = [
        ("critical", "严重"),
        ("high", "高"),
        ("medium", "中"),
        ("low", "低"),
    ]

    LEVEL_CHOICES = [
        ("H", "H"),
        ("M", "M"),
        ("L", "L"),
    ]

    group = models.ForeignKey(RobotGroup, on_delete=models.PROTECT, related_name="components", verbose_name="组")

    robot_id = models.CharField(max_length=64, db_index=True, verbose_name="机器人ID")
    name = models.CharField(max_length=128, blank=True, default="", verbose_name="名称")

    part_no = models.CharField(max_length=64, db_index=True, verbose_name="部件编号")
    reference_no = models.CharField(max_length=64, db_index=True, verbose_name="参考编号")
    number = models.IntegerField(default=0, verbose_name="Number")
    type_spec = models.CharField(max_length=128, verbose_name="类型")
    tech = models.CharField(max_length=128, verbose_name="工艺")
    mark = models.IntegerField(default=0, verbose_name="标记")
    remark = models.TextField(blank=True, default="", verbose_name="备注")

    checks = models.JSONField(default=dict, verbose_name="A1-A7检查项")
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default="L", verbose_name="等级")

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="online", verbose_name="状态")
    battery = models.PositiveSmallIntegerField(default=100, verbose_name="电量")
    health = models.PositiveSmallIntegerField(default=100, verbose_name="健康度")
    motor_temp = models.PositiveSmallIntegerField(default=60, verbose_name="电机温度")
    network_latency = models.PositiveSmallIntegerField(default=30, verbose_name="网络时延")
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="最近上报")

    risk_score = models.PositiveSmallIntegerField(default=0, verbose_name="风险分数")
    risk_level = models.CharField(max_length=16, choices=RISK_LEVEL_CHOICES, default="low", verbose_name="风险等级")
    risk_history = models.JSONField(default=list, verbose_name="历史风险记录")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "robot_components"
        verbose_name = "机器人部件"
        verbose_name_plural = "机器人部件"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["robot_id"]),
            models.Index(fields=["part_no"]),
            models.Index(fields=["reference_no"]),
            models.Index(fields=["risk_level"]),
            models.Index(fields=["level"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.part_no} ({self.robot_id})"

    @property
    def is_high_risk(self) -> bool:
        return self.level == "H"


class RiskEvent(models.Model):
    SEVERITY_CHOICES = [
        ("critical", "严重"),
        ("high", "高"),
        ("medium", "中"),
        ("low", "低"),
    ]

    STATUS_CHOICES = [
        ("pending", "待处理"),
        ("acknowledged", "已确认"),
        ("resolved", "已解决"),
    ]

    component = models.ForeignKey(
        RobotComponent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_events",
        verbose_name="关联部件",
    )
    group = models.ForeignKey(RobotGroup, on_delete=models.PROTECT, related_name="risk_events", verbose_name="组")

    robot_id = models.CharField(max_length=64, db_index=True, verbose_name="机器人ID")
    robot_name = models.CharField(max_length=128, blank=True, default="", verbose_name="机器人名称")

    message = models.CharField(max_length=255, verbose_name="事件信息")
    reason = models.CharField(max_length=128, blank=True, default="", verbose_name="原因")
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="low", verbose_name="严重程度")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="状态")
    risk_score = models.PositiveSmallIntegerField(default=0, verbose_name="风险分数")
    notes = models.TextField(blank=True, default="", verbose_name="备注")
    triggered_at = models.DateTimeField(verbose_name="触发时间")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "risk_events"
        verbose_name = "风险事件"
        verbose_name_plural = "风险事件"
        ordering = ["-triggered_at", "-id"]
        indexes = [
            models.Index(fields=["robot_id"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["status"]),
            models.Index(fields=["triggered_at"]),
        ]

    def __str__(self):
        return f"{self.robot_id} {self.message}"


class RobotAxisData(models.Model):
    """Robot axis time series data"""
    part_no = models.CharField(max_length=64, db_index=True, verbose_name="部件编号")
    timestamp = models.DateTimeField(db_index=True, verbose_name="时间戳")
    snr_c = models.IntegerField(db_index=True, verbose_name="SNR_C")
    p_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="程序名称")
    ref = models.CharField(max_length=64, blank=True, null=True, verbose_name="参考编号")
    robot_stop = models.BooleanField(default=False, verbose_name="机器人停止")

    # A1-A6 Axis data
    curr_a1 = models.FloatField(null=True, blank=True, verbose_name="A1电流")
    curr_a2 = models.FloatField(null=True, blank=True, verbose_name="A2电流")
    curr_a3 = models.FloatField(null=True, blank=True, verbose_name="A3电流")
    curr_a4 = models.FloatField(null=True, blank=True, verbose_name="A4电流")
    curr_a5 = models.FloatField(null=True, blank=True, verbose_name="A5电流")
    curr_a6 = models.FloatField(null=True, blank=True, verbose_name="A6电流")
    curr_e1 = models.FloatField(null=True, blank=True, verbose_name="E1电流")

    max_curr_a1 = models.FloatField(null=True, blank=True, verbose_name="A1最大电流")
    max_curr_a2 = models.FloatField(null=True, blank=True, verbose_name="A2最大电流")
    max_curr_a3 = models.FloatField(null=True, blank=True, verbose_name="A3最大电流")
    max_curr_a4 = models.FloatField(null=True, blank=True, verbose_name="A4最大电流")
    max_curr_a5 = models.FloatField(null=True, blank=True, verbose_name="A5最大电流")
    max_curr_a6 = models.FloatField(null=True, blank=True, verbose_name="A6最大电流")
    max_curr_e1 = models.FloatField(null=True, blank=True, verbose_name="E1最大电流")

    min_curr_a1 = models.FloatField(null=True, blank=True, verbose_name="A1最小电流")
    min_curr_a2 = models.FloatField(null=True, blank=True, verbose_name="A2最小电流")
    min_curr_a3 = models.FloatField(null=True, blank=True, verbose_name="A3最小电流")
    min_curr_a4 = models.FloatField(null=True, blank=True, verbose_name="A4最小电流")
    min_curr_a5 = models.FloatField(null=True, blank=True, verbose_name="A5最小电流")
    min_curr_a6 = models.FloatField(null=True, blank=True, verbose_name="A6最小电流")
    min_curr_e1 = models.FloatField(null=True, blank=True, verbose_name="E1最小电流")

    # Temperature
    tem_1 = models.IntegerField(null=True, blank=True, verbose_name="A1温度")
    tem_2 = models.IntegerField(null=True, blank=True, verbose_name="A2温度")
    tem_3 = models.IntegerField(null=True, blank=True, verbose_name="A3温度")
    tem_4 = models.IntegerField(null=True, blank=True, verbose_name="A4温度")
    tem_5 = models.IntegerField(null=True, blank=True, verbose_name="A5温度")
    tem_6 = models.IntegerField(null=True, blank=True, verbose_name="A6温度")
    tem_7 = models.IntegerField(null=True, blank=True, verbose_name="E1温度")

    # Position
    axisp1 = models.FloatField(null=True, blank=True, verbose_name="A1位置")
    axisp2 = models.FloatField(null=True, blank=True, verbose_name="A2位置")
    axisp3 = models.FloatField(null=True, blank=True, verbose_name="A3位置")
    axisp4 = models.FloatField(null=True, blank=True, verbose_name="A4位置")
    axisp5 = models.FloatField(null=True, blank=True, verbose_name="A5位置")
    axisp6 = models.FloatField(null=True, blank=True, verbose_name="A6位置")
    axisp7 = models.FloatField(null=True, blank=True, verbose_name="E1位置")

    # Speed
    speed1 = models.FloatField(null=True, blank=True, verbose_name="A1速度")
    speed2 = models.FloatField(null=True, blank=True, verbose_name="A2速度")
    speed3 = models.FloatField(null=True, blank=True, verbose_name="A3速度")
    speed4 = models.FloatField(null=True, blank=True, verbose_name="A4速度")
    speed5 = models.FloatField(null=True, blank=True, verbose_name="A5速度")
    speed6 = models.FloatField(null=True, blank=True, verbose_name="A6速度")
    speed7 = models.FloatField(null=True, blank=True, verbose_name="E7速度")

    # Torque
    torque1 = models.FloatField(null=True, blank=True, verbose_name="A1扭矩")
    torque2 = models.FloatField(null=True, blank=True, verbose_name="A2扭矩")
    torque3 = models.FloatField(null=True, blank=True, verbose_name="A3扭矩")
    torque4 = models.FloatField(null=True, blank=True, verbose_name="A4扭矩")
    torque5 = models.FloatField(null=True, blank=True, verbose_name="A5扭矩")
    torque6 = models.FloatField(null=True, blank=True, verbose_name="A6扭矩")
    torque7 = models.FloatField(null=True, blank=True, verbose_name="E7扭矩")

    # Following error
    fol1 = models.FloatField(null=True, blank=True, verbose_name="A1跟随误差")
    fol2 = models.FloatField(null=True, blank=True, verbose_name="A2跟随误差")
    fol3 = models.FloatField(null=True, blank=True, verbose_name="A3跟随误差")
    fol4 = models.FloatField(null=True, blank=True, verbose_name="A4跟随误差")
    fol5 = models.FloatField(null=True, blank=True, verbose_name="A5跟随误差")
    fol6 = models.FloatField(null=True, blank=True, verbose_name="A6跟随误差")
    fol7 = models.FloatField(null=True, blank=True, verbose_name="E7跟随误差")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "robot_axis_data"
        verbose_name = "机器人轴数据"
        verbose_name_plural = "机器人轴数据"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["part_no", "timestamp"]),
            models.Index(fields=["part_no", "snr_c"]),
        ]

    def __str__(self):
        return f"{self.part_no} - {self.timestamp}"
