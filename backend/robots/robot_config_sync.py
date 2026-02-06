"""
机器人配置CSV文件同步服务

用于在编辑机器人数据后同步更新本地CSV配置文件
"""
import csv
import logging
import os
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

# 默认CSV文件路径
DEFAULT_CSV_PATH = Path(settings.BASE_DIR).parent / "机器人配置文件.csv"


def read_robot_config_csv(csv_path=None):
    """
    读取机器人配置CSV文件

    返回: list of dict - 每行数据为一个字典
    """
    if csv_path is None:
        csv_path = DEFAULT_CSV_PATH

    if not csv_path.exists():
        logger.warning(f"CSV配置文件不存在: {csv_path}")
        return []

    data = []
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        logger.info(f"读取CSV配置文件成功: {len(data)} 条记录")
        return data
    except Exception as e:
        logger.error(f"读取CSV配置文件失败: {e}")
        return []


def write_robot_config_csv(data, csv_path=None):
    """
    写入机器人配置CSV文件

    Args:
        data: list of dict - 要写入的数据
        csv_path: CSV文件路径，默认使用配置文件路径
    """
    if csv_path is None:
        csv_path = DEFAULT_CSV_PATH

    if not data:
        logger.warning("没有数据需要写入CSV")
        return

    try:
        # 确保目录存在
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # 定义字段顺序
        fieldnames = ['robot', 'shop', 'reference', 'number', 'type', 'tech', 'mark', 'remark']

        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"写入CSV配置文件成功: {len(data)} 条记录 -> {csv_path}")
        return True
    except Exception as e:
        logger.error(f"写入CSV配置文件失败: {e}")
        return False


def update_robot_in_csv(robot, updates, csv_path=None, backup=True):
    """
    在CSV文件中更新指定机器人的数据

    Args:
        robot: 机器人名称
        updates: dict - 要更新的字段，如 {'reference': 'new_ref', 'remark': 'new_remark'}
        csv_path: CSV文件路径
        backup: bool - 是否在更新前备份

    返回: bool - 是否更新成功
    """
    if csv_path is None:
        csv_path = DEFAULT_CSV_PATH

    if not csv_path.exists():
        logger.warning(f"CSV配置文件不存在: {csv_path}")
        return False

    try:
        # 可选：先备份文件
        if backup:
            backup_csv_file(csv_path)

        # 读取现有数据
        data = []
        found = False
        updated_row = None

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['robot'] == robot:
                    # 更新匹配的行
                    for key, value in updates.items():
                        if value is not None:
                            row[key] = str(value)
                    found = True
                    updated_row = row.copy()
                data.append(row)

        if not found:
            logger.warning(f"在CSV中未找到机器人: {robot}")
            return False

        # 写回文件
        fieldnames = ['robot', 'shop', 'reference', 'number', 'type', 'tech', 'mark', 'remark']
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"CSV文件更新成功: robot={robot}, updates={updates}")
        return True

    except Exception as e:
        logger.error(f"更新CSV文件失败: {e}")
        return False


def sync_robot_component_to_csv(robot_component):
    """
    将RobotComponent的数据同步到CSV配置文件

    Args:
        robot_component: RobotComponent 实例

    返回: bool - 是否同步成功
    """
    updates = {
        'shop': robot_component.shop or '',
        'reference': robot_component.reference or '',
        'number': robot_component.number if robot_component.number is not None else '',
        'type': robot_component.type or '',
        'tech': robot_component.tech or '',
        'mark': robot_component.mark or 0,
        'remark': robot_component.remark or '',
    }

    return update_robot_in_csv(robot_component.robot, updates)


def get_csv_backup_path(csv_path=None):
    """
    获取CSV备份文件路径
    """
    if csv_path is None:
        csv_path = DEFAULT_CSV_PATH

    timestamp = csv_path.stem.replace('机器人配置文件', '') or ''
    backup_name = f"机器人配置文件_backup_{timestamp}"
    return csv_path.parent / f"{backup_name}.csv"


def backup_csv_file(csv_path=None):
    """
    备份CSV文件

    Args:
        csv_path: CSV文件路径

    返回: bool - 是否备份成功
    """
    if csv_path is None:
        csv_path = DEFAULT_CSV_PATH

    if not csv_path.exists():
        logger.warning(f"CSV文件不存在，无需备份: {csv_path}")
        return False

    try:
        import shutil
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = csv_path.parent / f"机器人配置文件_backup_{timestamp}.csv"

        shutil.copy2(csv_path, backup_path)
        logger.info(f"CSV文件备份成功: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"CSV文件备份失败: {e}")
        return False
