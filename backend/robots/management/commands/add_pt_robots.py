from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from robots.models import RobotComponent, RobotGroup


CHECK_KEYS = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
CHECK_LABELS = {
    "A1": "供电/线束",
    "A2": "温度/散热",
    "A3": "通信/网络",
    "A4": "传感器/对位",
    "A5": "抓手/执行器",
    "A6": "控制/程序",
    "A7": "安全/急停",
}


def create_checks() -> dict:
    """创建默认的关节检查项（全部正常）"""
    checks = {}
    for key in CHECK_KEYS:
        checks[key] = {"ok": True, "label": CHECK_LABELS[key]}
    return checks


class Command(BaseCommand):
    help = "添加 PT 车间和三个机器人 (HC41_010RB_100, UB43_350RB_300, UB43_360RB_100)"

    @transaction.atomic
    def handle(self, *args, **options):
        # 创建或获取 PT 车间
        group, created = RobotGroup.objects.get_or_create(
            key="pt",
            defaults={
                "name": "PT",
                "expected_total": 3,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"创建车间: {group.name} ({group.key})"))
        else:
            self.stdout.write(self.style.WARNING(f"车间已存在: {group.name} ({group.key})"))

        # 定义三个机器人数据
        robots_data = [
            {
                "robot_id": "PT-HC41-001",
                "name": "HC41 Robot",
                "part_no": "HC41_010RB_100",
                "reference_no": "240412-240621",
                "type_spec": "HC41_010RB_100",
                "tech": "涂胶 + 检测",
            },
            {
                "robot_id": "PT-UB43-001",
                "name": "UB43-350 Robot",
                "part_no": "UB43_350RB_300",
                "reference_no": "241101-241220",
                "type_spec": "UB43_350RB_300",
                "tech": "搬运 + 码垛",
            },
            {
                "robot_id": "PT-UB43-002",
                "name": "UB43-360 Robot",
                "part_no": "UB43_360RB_100",
                "reference_no": "250410-250516",
                "type_spec": "UB43_360RB_100",
                "tech": "焊接 + 拧紧",
            },
        ]

        created_count = 0
        updated_count = 0

        for robot_spec in robots_data:
            # 使用 part_no 作为唯一标识
            component, created = RobotComponent.objects.update_or_create(
                part_no=robot_spec["part_no"],
                defaults={
                    "group": group,
                    "robot_id": robot_spec["robot_id"],
                    "name": robot_spec["name"],
                    "reference_no": robot_spec["reference_no"],
                    "type_spec": robot_spec["type_spec"],
                    "tech": robot_spec["tech"],
                    "number": 0,
                    "mark": 0,
                    "remark": "",
                    "checks": create_checks(),
                    "level": "L",
                    "status": "online",
                    "battery": 100,
                    "health": 100,
                    "motor_temp": 60,
                    "network_latency": 30,
                    "last_seen": timezone.now(),
                    "risk_score": 0,
                    "risk_level": "low",
                    "risk_history": [],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  创建机器人: {component.part_no} ({component.robot_id})"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"  更新机器人: {component.part_no} ({component.robot_id})"))

        # 更新车间预期数量
        group.expected_total = RobotComponent.objects.filter(group=group).count()
        group.save()

        self.stdout.write(self.style.SUCCESS(
            f"\n完成! 车间: {group.name}, 创建: {created_count}, 更新: {updated_count}, 总数: {group.expected_total}"
        ))
