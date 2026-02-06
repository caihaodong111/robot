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
    """
    机器人组件模型
    严格按照 CSV 字段设计，用于从 weeklyresult.csv 导入数据
    """

    LEVEL_CHOICES = [
        ("H", "H"),
        ("M", "M"),
        ("L", "L"),
        ("T", "T"),
        ("C", "C"),
    ]

    RISK_LEVEL_CHOICES = [
        ("critical", "严重"),
        ("high", "高"),
        ("medium", "中"),
        ("low", "低"),
    ]

    # 外键
    group = models.ForeignKey(RobotGroup, on_delete=models.RESTRICT, related_name="components", verbose_name="组")

    # CSV 字段（严格按照顺序）
    robot = models.CharField(max_length=64, db_index=True, verbose_name="robot")
    shop = models.CharField(max_length=64, null=True, blank=True, verbose_name="shop")
    reference = models.CharField(max_length=64, null=True, blank=True, verbose_name="reference")
    number = models.FloatField(null=True, blank=True, verbose_name="number")
    type = models.CharField(max_length=128, null=True, blank=True, verbose_name="type")
    tech = models.CharField(max_length=128, null=True, blank=True, verbose_name="tech")
    mark = models.IntegerField(default=0, verbose_name="mark")
    remark = models.TextField(blank=True, default="", verbose_name="remark")

    error1_c1 = models.FloatField(null=True, blank=True, verbose_name="error1_c1")
    tem1_m = models.FloatField(null=True, blank=True, verbose_name="tem1_m")
    tem2_m = models.FloatField(null=True, blank=True, verbose_name="tem2_m")
    tem3_m = models.FloatField(null=True, blank=True, verbose_name="tem3_m")
    tem4_m = models.FloatField(null=True, blank=True, verbose_name="tem4_m")
    tem5_m = models.FloatField(null=True, blank=True, verbose_name="tem5_m")
    tem6_m = models.FloatField(null=True, blank=True, verbose_name="tem6_m")
    tem7_m = models.FloatField(null=True, blank=True, verbose_name="tem7_m")

    a1_e_rate = models.FloatField(null=True, blank=True, verbose_name="A1_e_rate")
    a2_e_rate = models.FloatField(null=True, blank=True, verbose_name="A2_e_rate")
    a3_e_rate = models.FloatField(null=True, blank=True, verbose_name="A3_e_rate")
    a4_e_rate = models.FloatField(null=True, blank=True, verbose_name="A4_e_rate")
    a5_e_rate = models.FloatField(null=True, blank=True, verbose_name="A5_e_rate")
    a6_e_rate = models.FloatField(null=True, blank=True, verbose_name="A6_e_rate")
    a7_e_rate = models.FloatField(null=True, blank=True, verbose_name="A7_e_rate")

    a1_rms = models.FloatField(null=True, blank=True, verbose_name="A1_Rms")
    a2_rms = models.FloatField(null=True, blank=True, verbose_name="A2_Rms")
    a3_rms = models.FloatField(null=True, blank=True, verbose_name="A3_Rms")
    a4_rms = models.FloatField(null=True, blank=True, verbose_name="A4_Rms")
    a5_rms = models.FloatField(null=True, blank=True, verbose_name="A5_Rms")
    a6_rms = models.FloatField(null=True, blank=True, verbose_name="A6_Rms")
    a7_rms = models.FloatField(null=True, blank=True, verbose_name="A7_Rms")

    a1_e = models.FloatField(null=True, blank=True, verbose_name="A1_E")
    a2_e = models.FloatField(null=True, blank=True, verbose_name="A2_E")
    a3_e = models.FloatField(null=True, blank=True, verbose_name="A3_E")
    a4_e = models.FloatField(null=True, blank=True, verbose_name="A4_E")
    a5_e = models.FloatField(null=True, blank=True, verbose_name="A5_E")
    a6_e = models.FloatField(null=True, blank=True, verbose_name="A6_E")
    a7_e = models.FloatField(null=True, blank=True, verbose_name="A7_E")

    q1 = models.FloatField(null=True, blank=True, verbose_name="Q1")
    q2 = models.FloatField(null=True, blank=True, verbose_name="Q2")
    q3 = models.FloatField(null=True, blank=True, verbose_name="Q3")
    q4 = models.FloatField(null=True, blank=True, verbose_name="Q4")
    q5 = models.FloatField(null=True, blank=True, verbose_name="Q5")
    q6 = models.FloatField(null=True, blank=True, verbose_name="Q6")
    q7 = models.FloatField(null=True, blank=True, verbose_name="Q7")

    curr_a1_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A1_max")
    curr_a2_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A2_max")
    curr_a3_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A3_max")
    curr_a4_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A4_max")
    curr_a5_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A5_max")
    curr_a6_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A6_max")
    curr_a7_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A7_max")

    curr_a1_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A1_min")
    curr_a2_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A2_min")
    curr_a3_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A3_min")
    curr_a4_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A4_min")
    curr_a5_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A5_min")
    curr_a6_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A6_min")
    curr_a7_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A7_min")

    a1 = models.CharField(max_length=16, null=True, blank=True, db_column='A1', verbose_name="A1")
    a2 = models.CharField(max_length=16, null=True, blank=True, db_column='A2', verbose_name="A2")
    a3 = models.CharField(max_length=16, null=True, blank=True, db_column='A3', verbose_name="A3")
    a4 = models.CharField(max_length=16, null=True, blank=True, db_column='A4', verbose_name="A4")
    a5 = models.CharField(max_length=16, null=True, blank=True, db_column='A5', verbose_name="A5")
    a6 = models.CharField(max_length=16, null=True, blank=True, db_column='A6', verbose_name="A6")
    a7 = models.CharField(max_length=16, null=True, blank=True, db_column='A7', verbose_name="A7")

    p_change = models.FloatField(null=True, blank=True, verbose_name="P_Change")
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default="L", verbose_name="level")

    # 元数据字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "robot_components"
        verbose_name = "机器人组件"
        verbose_name_plural = "机器人组件"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["robot"]),
            models.Index(fields=["shop"]),
            models.Index(fields=["level"]),
            models.Index(fields=["group"]),
        ]

    def __str__(self):
        return f"{self.robot} ({self.shop})"

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


class RobotHighRiskSnapshot(models.Model):
    """
    高风险机器人数据快照表

    用于存储 level=H 的机器人数据快照。
    每次同步时，robot_components 表中的 level=H 数据会被追加到此表，不会删除历史数据。
    此表结构与 robot_components 完全相同。
    """

    LEVEL_CHOICES = [
        ("H", "H"),
        ("M", "M"),
        ("L", "L"),
        ("T", "T"),
        ("C", "C"),
    ]

    # 外键
    group = models.ForeignKey(RobotGroup, on_delete=models.RESTRICT, related_name="high_risk_snapshots", verbose_name="组")

    # CSV 字段（严格按照顺序，与 RobotComponent 完全相同）
    robot = models.CharField(max_length=64, db_index=True, verbose_name="robot")
    shop = models.CharField(max_length=64, null=True, blank=True, verbose_name="shop")
    reference = models.CharField(max_length=64, null=True, blank=True, verbose_name="reference")
    number = models.FloatField(null=True, blank=True, verbose_name="number")
    type = models.CharField(max_length=128, null=True, blank=True, verbose_name="type")
    tech = models.CharField(max_length=128, null=True, blank=True, verbose_name="tech")
    mark = models.IntegerField(default=0, verbose_name="mark")
    remark = models.TextField(blank=True, default="", verbose_name="remark")

    error1_c1 = models.FloatField(null=True, blank=True, verbose_name="error1_c1")
    tem1_m = models.FloatField(null=True, blank=True, verbose_name="tem1_m")
    tem2_m = models.FloatField(null=True, blank=True, verbose_name="tem2_m")
    tem3_m = models.FloatField(null=True, blank=True, verbose_name="tem3_m")
    tem4_m = models.FloatField(null=True, blank=True, verbose_name="tem4_m")
    tem5_m = models.FloatField(null=True, blank=True, verbose_name="tem5_m")
    tem6_m = models.FloatField(null=True, blank=True, verbose_name="tem6_m")
    tem7_m = models.FloatField(null=True, blank=True, verbose_name="tem7_m")

    a1_e_rate = models.FloatField(null=True, blank=True, verbose_name="A1_e_rate")
    a2_e_rate = models.FloatField(null=True, blank=True, verbose_name="A2_e_rate")
    a3_e_rate = models.FloatField(null=True, blank=True, verbose_name="A3_e_rate")
    a4_e_rate = models.FloatField(null=True, blank=True, verbose_name="A4_e_rate")
    a5_e_rate = models.FloatField(null=True, blank=True, verbose_name="A5_e_rate")
    a6_e_rate = models.FloatField(null=True, blank=True, verbose_name="A6_e_rate")
    a7_e_rate = models.FloatField(null=True, blank=True, verbose_name="A7_e_rate")

    a1_rms = models.FloatField(null=True, blank=True, verbose_name="A1_Rms")
    a2_rms = models.FloatField(null=True, blank=True, verbose_name="A2_Rms")
    a3_rms = models.FloatField(null=True, blank=True, verbose_name="A3_Rms")
    a4_rms = models.FloatField(null=True, blank=True, verbose_name="A4_Rms")
    a5_rms = models.FloatField(null=True, blank=True, verbose_name="A5_Rms")
    a6_rms = models.FloatField(null=True, blank=True, verbose_name="A6_Rms")
    a7_rms = models.FloatField(null=True, blank=True, verbose_name="A7_Rms")

    a1_e = models.FloatField(null=True, blank=True, verbose_name="A1_E")
    a2_e = models.FloatField(null=True, blank=True, verbose_name="A2_E")
    a3_e = models.FloatField(null=True, blank=True, verbose_name="A3_E")
    a4_e = models.FloatField(null=True, blank=True, verbose_name="A4_E")
    a5_e = models.FloatField(null=True, blank=True, verbose_name="A5_E")
    a6_e = models.FloatField(null=True, blank=True, verbose_name="A6_E")
    a7_e = models.FloatField(null=True, blank=True, verbose_name="A7_E")

    q1 = models.FloatField(null=True, blank=True, verbose_name="Q1")
    q2 = models.FloatField(null=True, blank=True, verbose_name="Q2")
    q3 = models.FloatField(null=True, blank=True, verbose_name="Q3")
    q4 = models.FloatField(null=True, blank=True, verbose_name="Q4")
    q5 = models.FloatField(null=True, blank=True, verbose_name="Q5")
    q6 = models.FloatField(null=True, blank=True, verbose_name="Q6")
    q7 = models.FloatField(null=True, blank=True, verbose_name="Q7")

    curr_a1_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A1_max")
    curr_a2_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A2_max")
    curr_a3_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A3_max")
    curr_a4_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A4_max")
    curr_a5_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A5_max")
    curr_a6_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A6_max")
    curr_a7_max = models.FloatField(null=True, blank=True, verbose_name="Curr_A7_max")

    curr_a1_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A1_min")
    curr_a2_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A2_min")
    curr_a3_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A3_min")
    curr_a4_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A4_min")
    curr_a5_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A5_min")
    curr_a6_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A6_min")
    curr_a7_min = models.FloatField(null=True, blank=True, verbose_name="Curr_A7_min")

    a1 = models.CharField(max_length=16, null=True, blank=True, db_column='A1', verbose_name="A1")
    a2 = models.CharField(max_length=16, null=True, blank=True, db_column='A2', verbose_name="A2")
    a3 = models.CharField(max_length=16, null=True, blank=True, db_column='A3', verbose_name="A3")
    a4 = models.CharField(max_length=16, null=True, blank=True, db_column='A4', verbose_name="A4")
    a5 = models.CharField(max_length=16, null=True, blank=True, db_column='A5', verbose_name="A5")
    a6 = models.CharField(max_length=16, null=True, blank=True, db_column='A6', verbose_name="A6")
    a7 = models.CharField(max_length=16, null=True, blank=True, db_column='A7', verbose_name="A7")

    p_change = models.FloatField(null=True, blank=True, verbose_name="P_Change")
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default="H", verbose_name="level")

    # 元数据字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "_robot_high_risk_snapshots"
        verbose_name = "高风险机器人快照"
        verbose_name_plural = "高风险机器人快照"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["robot"]),
            models.Index(fields=["shop"]),
            models.Index(fields=["level"]),
            models.Index(fields=["group"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.robot} ({self.shop}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_high_risk(self) -> bool:
        return self.level == "H"


class RobotReferenceDict(models.Model):
    """Reference dictionary for robot -> reference -> number mapping."""

    robot = models.CharField(max_length=64, db_index=True, verbose_name="robot")
    reference = models.CharField(max_length=128, db_index=True, verbose_name="reference")
    number = models.FloatField(null=True, blank=True, verbose_name="number")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "robot_reference_dict"
        verbose_name = "机器人参考字典"
        verbose_name_plural = "机器人参考字典"
        unique_together = ("robot", "reference")
        indexes = [
            models.Index(fields=["robot", "reference"]),
        ]

    def __str__(self):
        return f"{self.robot} - {self.reference}"


class RefreshLog(models.Model):
    """
    数据刷新日志表
    记录每次数据同步的详细信息
    """
    SOURCE_CHOICES = [
        ("manual", "手动同步"),
        ("auto", "自动同步"),
    ]

    STATUS_CHOICES = [
        ("success", "成功"),
        ("failed", "失败"),
    ]

    # 数据来源
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default="manual", verbose_name="数据来源")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="success", verbose_name="状态")

    # 文件信息
    source_file = models.CharField(max_length=255, blank=True, default="", verbose_name="源文件名")
    file_date = models.DateField(null=True, blank=True, verbose_name="文件日期")

    # 统计信息
    records_created = models.PositiveIntegerField(default=0, verbose_name="新增记录数")
    records_updated = models.PositiveIntegerField(default=0, verbose_name="更新记录数")
    records_deleted = models.PositiveIntegerField(default=0, verbose_name="删除记录数")
    total_records = models.PositiveIntegerField(default=0, verbose_name="总记录数")

    # 错误信息
    error_message = models.TextField(blank=True, default="", verbose_name="错误信息")

    # 同步时间
    sync_time = models.DateTimeField(auto_now_add=True, verbose_name="同步时间")

    class Meta:
        db_table = "refresh_logs"
        verbose_name = "刷新日志"
        verbose_name_plural = "刷新日志"
        ordering = ["-sync_time"]
        indexes = [
            models.Index(fields=["-sync_time"]),
            models.Index(fields=["source"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.get_source_display()} - {self.sync_time.strftime('%Y-%m-%d %H:%M:%S')}"


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


class EditAuthUser(models.Model):
    """
    编辑认证用户模型
    用于存储机器人组件编辑功能的认证账号密码
    """
    username = models.CharField(max_length=64, unique=True, verbose_name="用户名")
    # 使用 Django 的 make_password 生成的哈希密码存储
    password_hash = models.CharField(max_length=128, verbose_name="密码哈希")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name="最后登录时间")

    class Meta:
        db_table = "edit_auth_users"
        verbose_name = "编辑认证用户"
        verbose_name_plural = "编辑认证用户"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        """设置密码（哈希存储）"""
        from django.contrib.auth.hashers import make_password
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """验证密码"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password_hash)

    @classmethod
    def get_active_user(cls, username):
        """获取活跃用户"""
        try:
            return cls.objects.get(username=username, is_active=True)
        except cls.DoesNotExist:
            return None

    @classmethod
    def verify_credentials(cls, username, password):
        """验证凭据"""
        user = cls.get_active_user(username)
        if user and user.check_password(password):
            # 更新最后登录时间
            from django.utils import timezone
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])
            return user
        return None


class EditSessionVersion(models.Model):
    """
    编辑会话版本控制

    用于管理编辑登录会话的有效性，定时任务刷新时增加版本号，
    使所有已登录的会话失效，需要重新登录
    """
    version = models.BigIntegerField(default=1, verbose_name="版本号")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    updated_by = models.CharField(max_length=64, blank=True, default="", verbose_name="更新来源")

    class Meta:
        db_table = "edit_session_version"
        verbose_name = "编辑会话版本"
        verbose_name_plural = "编辑会话版本"

    def __str__(self):
        return f"Version {self.version} (updated: {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')})"

    @classmethod
    def get_current_version(cls):
        """获取当前会话版本"""
        obj, created = cls.objects.get_or_create(
            id=1,
            defaults={'version': 1, 'updated_by': 'system'}
        )
        return obj.version

    @classmethod
    def increment_version(cls, updated_by="system"):
        """增加版本号（使所有现有会话失效）"""
        obj, created = cls.objects.get_or_create(
            id=1,
            defaults={'version': 1, 'updated_by': updated_by}
        )
        obj.version += 1
        obj.updated_by = updated_by
        obj.save()
        return obj.version

    @classmethod
    def check_version(cls, client_version):
        """检查客户端版本是否有效"""
        if client_version is None:
            return False
        current = cls.get_current_version()
        return int(client_version) == current


class RobotInfo(models.Model):
    """
    机器人基本信息表

    用于存储机器人的基础信息，方便管理和查询
    """
    robot = models.CharField(max_length=64, db_index=True, verbose_name="机器人")
    shop = models.CharField(max_length=64, null=True, blank=True, verbose_name="车间")
    reference = models.CharField(max_length=128, null=True, blank=True, verbose_name="参考编号")
    number = models.FloatField(null=True, blank=True, verbose_name="编号")
    type = models.CharField(max_length=128, null=True, blank=True, verbose_name="类型")
    tech = models.CharField(max_length=128, null=True, blank=True, verbose_name="工艺")
    mark = models.IntegerField(default=0, verbose_name="标记")
    remark = models.TextField(blank=True, default="", verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "robot_info"
        verbose_name = "机器人基本信息"
        verbose_name_plural = "机器人基本信息"
        ordering = ["robot"]
        indexes = [
            models.Index(fields=["robot"]),
            models.Index(fields=["shop"]),
            models.Index(fields=["reference"]),
            models.Index(fields=["robot", "reference"]),
        ]

    def __str__(self):
        return f"{self.robot} - {self.reference or 'N/A'}"

