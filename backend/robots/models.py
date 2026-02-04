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
        ("T", "T"),
        ("C", "C"),
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

    # 详细数据字段（从 weeklyresult.csv 导入）
    error1_c1 = models.FloatField(blank=True, null=True, verbose_name="错误率C1")
    tem1_m = models.FloatField(blank=True, null=True, verbose_name="温度M1")
    tem2_m = models.FloatField(blank=True, null=True, verbose_name="温度M2")
    tem3_m = models.FloatField(blank=True, null=True, verbose_name="温度M3")
    tem4_m = models.FloatField(blank=True, null=True, verbose_name="温度M4")
    tem5_m = models.FloatField(blank=True, null=True, verbose_name="温度M5")
    tem6_m = models.FloatField(blank=True, null=True, verbose_name="温度M6")
    tem7_m = models.FloatField(blank=True, null=True, verbose_name="温度M7")

    a1_e_rate = models.FloatField(blank=True, null=True, verbose_name="A1错误率")
    a2_e_rate = models.FloatField(blank=True, null=True, verbose_name="A2错误率")
    a3_e_rate = models.FloatField(blank=True, null=True, verbose_name="A3错误率")
    a4_e_rate = models.FloatField(blank=True, null=True, verbose_name="A4错误率")
    a5_e_rate = models.FloatField(blank=True, null=True, verbose_name="A5错误率")
    a6_e_rate = models.FloatField(blank=True, null=True, verbose_name="A6错误率")
    a7_e_rate = models.FloatField(blank=True, null=True, verbose_name="A7错误率")

    a1_rms = models.FloatField(blank=True, null=True, verbose_name="A1 RMS")
    a2_rms = models.FloatField(blank=True, null=True, verbose_name="A2 RMS")
    a3_rms = models.FloatField(blank=True, null=True, verbose_name="A3 RMS")
    a4_rms = models.FloatField(blank=True, null=True, verbose_name="A4 RMS")
    a5_rms = models.FloatField(blank=True, null=True, verbose_name="A5 RMS")
    a6_rms = models.FloatField(blank=True, null=True, verbose_name="A6 RMS")
    a7_rms = models.FloatField(blank=True, null=True, verbose_name="A7 RMS")

    a1_e = models.FloatField(blank=True, null=True, verbose_name="A1 E值")
    a2_e = models.FloatField(blank=True, null=True, verbose_name="A2 E值")
    a3_e = models.FloatField(blank=True, null=True, verbose_name="A3 E值")
    a4_e = models.FloatField(blank=True, null=True, verbose_name="A4 E值")
    a5_e = models.FloatField(blank=True, null=True, verbose_name="A5 E值")
    a6_e = models.FloatField(blank=True, null=True, verbose_name="A6 E值")
    a7_e = models.FloatField(blank=True, null=True, verbose_name="A7 E值")

    q1 = models.FloatField(blank=True, null=True, verbose_name="Q1")
    q2 = models.FloatField(blank=True, null=True, verbose_name="Q2")
    q3 = models.FloatField(blank=True, null=True, verbose_name="Q3")
    q4 = models.FloatField(blank=True, null=True, verbose_name="Q4")
    q5 = models.FloatField(blank=True, null=True, verbose_name="Q5")
    q6 = models.FloatField(blank=True, null=True, verbose_name="Q6")
    q7 = models.FloatField(blank=True, null=True, verbose_name="Q7")

    curr_a1_max = models.FloatField(blank=True, null=True, verbose_name="A1最大电流")
    curr_a2_max = models.FloatField(blank=True, null=True, verbose_name="A2最大电流")
    curr_a3_max = models.FloatField(blank=True, null=True, verbose_name="A3最大电流")
    curr_a4_max = models.FloatField(blank=True, null=True, verbose_name="A4最大电流")
    curr_a5_max = models.FloatField(blank=True, null=True, verbose_name="A5最大电流")
    curr_a6_max = models.FloatField(blank=True, null=True, verbose_name="A6最大电流")
    curr_a7_max = models.FloatField(blank=True, null=True, verbose_name="A7最大电流")

    curr_a1_min = models.FloatField(blank=True, null=True, verbose_name="A1最小电流")
    curr_a2_min = models.FloatField(blank=True, null=True, verbose_name="A2最小电流")
    curr_a3_min = models.FloatField(blank=True, null=True, verbose_name="A3最小电流")
    curr_a4_min = models.FloatField(blank=True, null=True, verbose_name="A4最小电流")
    curr_a5_min = models.FloatField(blank=True, null=True, verbose_name="A5最小电流")
    curr_a6_min = models.FloatField(blank=True, null=True, verbose_name="A6最小电流")
    curr_a7_min = models.FloatField(blank=True, null=True, verbose_name="A7最小电流")

    a1 = models.FloatField(blank=True, null=True, verbose_name="A1电流")
    a2 = models.FloatField(blank=True, null=True, verbose_name="A2电流")
    a3 = models.FloatField(blank=True, null=True, verbose_name="A3电流")
    a4 = models.FloatField(blank=True, null=True, verbose_name="A4电流")
    a5 = models.FloatField(blank=True, null=True, verbose_name="A5电流")
    a6 = models.FloatField(blank=True, null=True, verbose_name="A6电流")
    a7 = models.FloatField(blank=True, null=True, verbose_name="A7电流")

    p_change = models.FloatField(blank=True, null=True, verbose_name="P变化")

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


class WeeklyResult(models.Model):
    """周结果数据模型 - 从 weeklyresult.csv 导入"""

    LEVEL_CHOICES = [
        ("H", "H"),
        ("M", "M"),
        ("L", "L"),
        ("T", "T"),
        ("C", "C"),
    ]

    # 基本信息
    robot = models.CharField(max_length=64, db_index=True, verbose_name="机器人编号")
    shop = models.CharField(max_length=64, db_index=True, verbose_name="车间")
    reference = models.CharField(max_length=64, blank=True, null=True, verbose_name="参考编号")
    number = models.FloatField(blank=True, null=True, verbose_name="编号")
    type = models.CharField(max_length=128, blank=True, null=True, verbose_name="类型")
    tech = models.CharField(max_length=128, blank=True, null=True, verbose_name="工艺")
    mark = models.IntegerField(default=0, verbose_name="标记")
    remark = models.TextField(blank=True, default="", verbose_name="备注")

    # 错误率和温度
    error1_c1 = models.FloatField(blank=True, null=True, verbose_name="错误率C1")
    tem1_m = models.FloatField(blank=True, null=True, verbose_name="温度M1")
    tem2_m = models.FloatField(blank=True, null=True, verbose_name="温度M2")
    tem3_m = models.FloatField(blank=True, null=True, verbose_name="温度M3")
    tem4_m = models.FloatField(blank=True, null=True, verbose_name="温度M4")
    tem5_m = models.FloatField(blank=True, null=True, verbose_name="温度M5")
    tem6_m = models.FloatField(blank=True, null=True, verbose_name="温度M6")
    tem7_m = models.FloatField(blank=True, null=True, verbose_name="温度M7")

    # A1-A7 错误率
    a1_e_rate = models.FloatField(blank=True, null=True, verbose_name="A1错误率")
    a2_e_rate = models.FloatField(blank=True, null=True, verbose_name="A2错误率")
    a3_e_rate = models.FloatField(blank=True, null=True, verbose_name="A3错误率")
    a4_e_rate = models.FloatField(blank=True, null=True, verbose_name="A4错误率")
    a5_e_rate = models.FloatField(blank=True, null=True, verbose_name="A5错误率")
    a6_e_rate = models.FloatField(blank=True, null=True, verbose_name="A6错误率")
    a7_e_rate = models.FloatField(blank=True, null=True, verbose_name="A7错误率")

    # A1-A7 RMS值
    a1_rms = models.FloatField(blank=True, null=True, verbose_name="A1 RMS")
    a2_rms = models.FloatField(blank=True, null=True, verbose_name="A2 RMS")
    a3_rms = models.FloatField(blank=True, null=True, verbose_name="A3 RMS")
    a4_rms = models.FloatField(blank=True, null=True, verbose_name="A4 RMS")
    a5_rms = models.FloatField(blank=True, null=True, verbose_name="A5 RMS")
    a6_rms = models.FloatField(blank=True, null=True, verbose_name="A6 RMS")
    a7_rms = models.FloatField(blank=True, null=True, verbose_name="A7 RMS")

    # A1-A7 E值
    a1_e = models.FloatField(blank=True, null=True, verbose_name="A1 E值")
    a2_e = models.FloatField(blank=True, null=True, verbose_name="A2 E值")
    a3_e = models.FloatField(blank=True, null=True, verbose_name="A3 E值")
    a4_e = models.FloatField(blank=True, null=True, verbose_name="A4 E值")
    a5_e = models.FloatField(blank=True, null=True, verbose_name="A5 E值")
    a6_e = models.FloatField(blank=True, null=True, verbose_name="A6 E值")
    a7_e = models.FloatField(blank=True, null=True, verbose_name="A7 E值")

    # Q1-Q7值
    q1 = models.FloatField(blank=True, null=True, verbose_name="Q1")
    q2 = models.FloatField(blank=True, null=True, verbose_name="Q2")
    q3 = models.FloatField(blank=True, null=True, verbose_name="Q3")
    q4 = models.FloatField(blank=True, null=True, verbose_name="Q4")
    q5 = models.FloatField(blank=True, null=True, verbose_name="Q5")
    q6 = models.FloatField(blank=True, null=True, verbose_name="Q6")
    q7 = models.FloatField(blank=True, null=True, verbose_name="Q7")

    # 最大电流
    curr_a1_max = models.FloatField(blank=True, null=True, verbose_name="A1最大电流")
    curr_a2_max = models.FloatField(blank=True, null=True, verbose_name="A2最大电流")
    curr_a3_max = models.FloatField(blank=True, null=True, verbose_name="A3最大电流")
    curr_a4_max = models.FloatField(blank=True, null=True, verbose_name="A4最大电流")
    curr_a5_max = models.FloatField(blank=True, null=True, verbose_name="A5最大电流")
    curr_a6_max = models.FloatField(blank=True, null=True, verbose_name="A6最大电流")
    curr_a7_max = models.FloatField(blank=True, null=True, verbose_name="A7最大电流")

    # 最小电流
    curr_a1_min = models.FloatField(blank=True, null=True, verbose_name="A1最小电流")
    curr_a2_min = models.FloatField(blank=True, null=True, verbose_name="A2最小电流")
    curr_a3_min = models.FloatField(blank=True, null=True, verbose_name="A3最小电流")
    curr_a4_min = models.FloatField(blank=True, null=True, verbose_name="A4最小电流")
    curr_a5_min = models.FloatField(blank=True, null=True, verbose_name="A5最小电流")
    curr_a6_min = models.FloatField(blank=True, null=True, verbose_name="A6最小电流")
    curr_a7_min = models.FloatField(blank=True, null=True, verbose_name="A7最小电流")

    # A1-A7 电流值
    a1 = models.FloatField(blank=True, null=True, verbose_name="A1电流")
    a2 = models.FloatField(blank=True, null=True, verbose_name="A2电流")
    a3 = models.FloatField(blank=True, null=True, verbose_name="A3电流")
    a4 = models.FloatField(blank=True, null=True, verbose_name="A4电流")
    a5 = models.FloatField(blank=True, null=True, verbose_name="A5电流")
    a6 = models.FloatField(blank=True, null=True, verbose_name="A6电流")
    a7 = models.FloatField(blank=True, null=True, verbose_name="A7电流")

    # 其他
    p_change = models.FloatField(blank=True, null=True, verbose_name="P变化")
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default="L", verbose_name="等级")

    # 数据来源信息
    source_file = models.CharField(max_length=255, verbose_name="源文件名")
    week_start = models.DateField(blank=True, null=True, verbose_name="周开始日期")
    week_end = models.DateField(blank=True, null=True, verbose_name="周结束日期")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "weekly_results"
        verbose_name = "周结果数据"
        verbose_name_plural = "周结果数据"
        ordering = ["-updated_at", "robot"]
        indexes = [
            models.Index(fields=["robot"]),
            models.Index(fields=["shop"]),
            models.Index(fields=["level"]),
            models.Index(fields=["source_file"]),
            models.Index(fields=["week_start", "week_end"]),
        ]

    def __str__(self):
        return f"{self.robot} ({self.shop}) - {self.week_start}"

    @property
    def is_high_risk(self) -> bool:
        return self.level == "H"


class RobotHighRiskSnapshot(models.Model):
    """
    高风险机器人数据快照表

    用于存储 level=H 的机器人数据快照，防止数据同步时被覆盖。
    当同步数据时，如果某个机器人在此表中有快照，则使用快照数据而不是新的导入数据。
    """

    STATUS_CHOICES = [
        ("online", "在线"),
        ("offline", "离线"),
        ("maintenance", "维护中"),
    ]

    LEVEL_CHOICES = [
        ("H", "H"),
        ("M", "M"),
        ("L", "L"),
        ("T", "T"),
        ("C", "C"),
    ]

    # 关联到原机器人组件（可选，用于追溯）
    component = models.ForeignKey(
        RobotComponent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="high_risk_snapshots",
        verbose_name="关联组件"
    )

    # 唯一标识（通过 part_no 关联到具体机器人）
    part_no = models.CharField(max_length=64, db_index=True, unique=True, verbose_name="部件编号")

    # 车间信息（冗余存储，确保快照独立完整）
    group_key = models.CharField(max_length=32, verbose_name="车间Key")
    group_name = models.CharField(max_length=64, verbose_name="车间名称")

    # 机器人基本信息
    robot_id = models.CharField(max_length=64, db_index=True, verbose_name="机器人ID")
    name = models.CharField(max_length=128, blank=True, default="", verbose_name="名称")
    reference_no = models.CharField(max_length=64, verbose_name="参考编号")
    number = models.IntegerField(default=0, verbose_name="Number")
    type_spec = models.CharField(max_length=128, verbose_name="类型")
    tech = models.CharField(max_length=128, verbose_name="工艺")
    mark = models.IntegerField(default=0, verbose_name="标记")
    remark = models.TextField(blank=True, default="", verbose_name="备注")

    # A1-A7 检查项
    checks = models.JSONField(default=dict, verbose_name="A1-A7检查项")
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default="H", verbose_name="等级")

    # 状态信息
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="online", verbose_name="状态")
    battery = models.PositiveSmallIntegerField(default=100, verbose_name="电量")
    health = models.PositiveSmallIntegerField(default=100, verbose_name="健康度")
    motor_temp = models.PositiveSmallIntegerField(default=60, verbose_name="电机温度")
    network_latency = models.PositiveSmallIntegerField(default=30, verbose_name="网络时延")
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="最近上报")

    # 风险信息
    risk_score = models.PositiveSmallIntegerField(default=0, verbose_name="风险分数")
    risk_level = models.CharField(max_length=16, choices=RobotComponent.RISK_LEVEL_CHOICES, default="high", verbose_name="风险等级")
    risk_history = models.JSONField(default=list, verbose_name="历史风险记录")

    # 快照元数据
    snapshot_reason = models.CharField(max_length=255, default="", verbose_name="快照原因")
    snapshot_source = models.CharField(max_length=64, default="manual", verbose_name="快照来源")  # manual/auto_sync/api
    is_active = models.BooleanField(default=True, verbose_name="是否生效")  # 可手动关闭快照保护

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "_robot_high_risk_snapshots"
        verbose_name = "高风险机器人快照"
        verbose_name_plural = "高风险机器人快照"
        ordering = ["-updated_at", "-created_at"]
        indexes = [
            models.Index(fields=["part_no"]),
            models.Index(fields=["robot_id"]),
            models.Index(fields=["group_key"]),
            models.Index(fields=["level"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.part_no} - {self.group_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def is_protected(self) -> bool:
        """此快照是否受保护（生效中）"""
        return self.is_active

    def restore_to_component(self, component=None):
        """
        将快照数据恢复到 RobotComponent

        Args:
            component: 目标组件，如果为 None 则通过 part_no 查找

        Returns:
            更新后的 RobotComponent 实例
        """
        from robots.models import RobotGroup

        if component is None:
            component = RobotComponent.objects.filter(part_no=self.part_no).first()

        if not component:
            # 创建新的组件记录
            group = RobotGroup.objects.filter(key=self.group_key).first()
            if not group:
                group = RobotGroup.objects.create(key=self.group_key, name=self.group_name)

            component = RobotComponent.objects.create(
                group=group,
                part_no=self.part_no
            )

        # 更新组件数据
        component.robot_id = self.robot_id
        component.name = self.name
        component.reference_no = self.reference_no
        component.number = self.number
        component.type_spec = self.type_spec
        component.tech = self.tech
        component.mark = self.mark
        component.remark = self.remark
        component.checks = self.checks
        component.level = self.level
        component.status = self.status
        component.battery = self.battery
        component.health = self.health
        component.motor_temp = self.motor_temp
        component.network_latency = self.network_latency
        component.last_seen = self.last_seen
        component.risk_score = self.risk_score
        component.risk_level = self.risk_level
        component.risk_history = self.risk_history

        component.save()

        # 更新关联
        self.component = component
        self.save(update_fields=["component"])

        return component


class SystemConfig(models.Model):
    """
    系统配置模型
    用于存储全局的系统配置信息，如最后同步时间等
    """
    key = models.CharField(max_length=64, unique=True, verbose_name="配置键")
    value = models.TextField(verbose_name="配置值")
    description = models.CharField(max_length=255, blank=True, default="", verbose_name="描述")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "system_configs"
        verbose_name = "系统配置"
        verbose_name_plural = "系统配置"
        ordering = ["key"]

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get(cls, key, default=None):
        """获取配置值"""
        try:
            config = cls.objects.get(key=key)
            return config.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, description=""):
        """设置配置值"""
        config, created = cls.objects.get_or_create(
            key=key,
            defaults={"value": value, "description": description}
        )
        if not created:
            config.value = value
            if description:
                config.description = description
            config.save()
        return config


class HighRiskHistory(models.Model):
    """
    历史高风险机器人记录表

    存储所有曾经 level=H 的机器人数据快照。
    每次数据同步时，如果发现新的 level=H 机器人，则追加到此表。
    已有的记录不会被更新或删除，数据只会越来越多。
    """

    STATUS_CHOICES = [
        ("online", "在线"),
        ("offline", "离线"),
        ("maintenance", "维护中"),
    ]

    LEVEL_CHOICES = [
        ("H", "H"),
        ("M", "M"),
        ("L", "L"),
        ("T", "T"),
        ("C", "C"),
    ]

    # 关联到原机器人组件（可选，用于追溯）
    component = models.ForeignKey(
        RobotComponent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="high_risk_histories",
        verbose_name="关联组件"
    )

    # 唯一标识（通过 part_no 关联到具体机器人）
    part_no = models.CharField(max_length=64, db_index=True, verbose_name="部件编号")

    # 车间信息
    group_key = models.CharField(max_length=32, verbose_name="车间Key")
    group_name = models.CharField(max_length=64, verbose_name="车间名称")

    # 机器人基本信息
    robot_id = models.CharField(max_length=64, db_index=True, verbose_name="机器人ID")
    name = models.CharField(max_length=128, blank=True, default="", verbose_name="名称")
    reference_no = models.CharField(max_length=64, verbose_name="参考编号")
    number = models.IntegerField(default=0, verbose_name="Number")
    type_spec = models.CharField(max_length=128, verbose_name="类型")
    tech = models.CharField(max_length=128, verbose_name="工艺")
    mark = models.IntegerField(default=0, verbose_name="标记")
    remark = models.TextField(blank=True, default="", verbose_name="备注")

    # A1-A7 检查项
    checks = models.JSONField(default=dict, verbose_name="A1-A7检查项")
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default="H", verbose_name="等级")

    # 状态信息
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="online", verbose_name="状态")
    battery = models.PositiveSmallIntegerField(default=100, verbose_name="电量")
    health = models.PositiveSmallIntegerField(default=100, verbose_name="健康度")
    motor_temp = models.PositiveSmallIntegerField(default=60, verbose_name="电机温度")
    network_latency = models.PositiveSmallIntegerField(default=30, verbose_name="网络时延")
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="最近上报")

    # 风险信息
    risk_score = models.PositiveSmallIntegerField(default=0, verbose_name="风险分数")
    risk_level = models.CharField(max_length=16, choices=RobotComponent.RISK_LEVEL_CHOICES, default="high", verbose_name="风险等级")

    # 记录元数据
    record_source = models.CharField(max_length=64, default="sync", verbose_name="记录来源")  # sync/manual/api
    sync_time = models.DateTimeField(auto_now_add=True, verbose_name="同步时间")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "high_risk_histories"
        verbose_name = "历史高风险机器人"
        verbose_name_plural = "历史高风险机器人"
        ordering = ["-created_at", "-sync_time"]
        indexes = [
            models.Index(fields=["part_no"]),
            models.Index(fields=["robot_id"]),
            models.Index(fields=["group_key"]),
            models.Index(fields=["level"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-sync_time"]),
        ]

    def __str__(self):
        return f"{self.part_no} - {self.group_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def is_high_risk(self) -> bool:
        return self.level == "H"
