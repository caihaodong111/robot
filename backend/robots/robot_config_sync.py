"""
机器人配置CSV文件同步服务

用于在编辑机器人数据后同步更新本地CSV配置文件
"""
import csv
import logging
import os
import glob
from pathlib import Path
from django.conf import settings
from .models import PathConfig

logger = logging.getLogger(__name__)

# 默认CSV文件路径（配置缺失时兜底）
DEFAULT_CSV_PATH = Path(
    getattr(
        settings,
        "ROBOT_CONFIG_CSV",
        str(Path(settings.BASE_DIR).parent / "机器人配置文件.csv"),
    )
)


def get_default_csv_path() -> Path:
    """从数据库配置读取路径，未配置时使用默认值"""
    try:
        configured = PathConfig.get_path("robot_config_csv", str(DEFAULT_CSV_PATH))
        return Path(configured)
    except Exception:
        return DEFAULT_CSV_PATH


def _split_csv_paths(value) -> list:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    parts = []
    for raw in str(value).replace("\n", ";").split(";"):
        parts.extend(raw.split(","))
    return [item.strip() for item in parts if item.strip()]


def _split_weekly_folders(value) -> list:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    parts = []
    for raw in str(value).replace("\n", ";").split(";"):
        parts.extend(raw.split(","))
    return [item.strip() for item in parts if item.strip()]


def get_configured_weekly_folders() -> list:
    """返回已配置的 weeklyresult 目录列表（支持多路径）"""
    try:
        configured = PathConfig.get_path(
            "weekly_result_folder",
            getattr(settings, "WEEKLY_RESULT_FOLDER", str(settings.BASE_DIR.parent)),
        )
    except Exception:
        configured = getattr(settings, "WEEKLY_RESULT_FOLDER", str(settings.BASE_DIR.parent))
    return _split_weekly_folders(configured)


def _resolve_reference_dict_file(path: Path) -> Path:
    if path.is_dir():
        candidates = [
            "dic information .csv",
            "dic_information.csv",
            "dic information.csv",
        ]
        for name in candidates:
            candidate = path / name
            if candidate.exists():
                return candidate
        return path / candidates[0]
    return path


def get_configured_reference_dict_paths() -> list:
    """返回已配置的 reference dict CSV 路径列表（支持多路径）"""
    try:
        configured = PathConfig.get_path(
            "reference_dict_csv",
            getattr(settings, "REFERENCE_DICT_CSV", ""),
        )
    except Exception:
        configured = getattr(settings, "REFERENCE_DICT_CSV", "")

    configured_paths = _split_csv_paths(configured)
    if not configured_paths:
        return []

    csv_paths = []
    for path_str in configured_paths:
        path = Path(path_str)
        csv_paths.append(_resolve_reference_dict_file(path))
    return csv_paths


def get_configured_csv_paths() -> list:
    """返回已配置的 CSV 路径列表（支持多路径）"""
    try:
        configured = PathConfig.get_path("robot_config_csv", str(DEFAULT_CSV_PATH))
    except Exception:
        configured = str(DEFAULT_CSV_PATH)

    configured_paths = _split_csv_paths(configured)
    if not configured_paths:
        configured_paths = [str(DEFAULT_CSV_PATH)]

    csv_paths = []
    for path_str in configured_paths:
        path = Path(path_str)
        if path.is_dir():
            path = path / DEFAULT_CSV_PATH.name
        csv_paths.append(path)
    return csv_paths


def get_weekly_to_config_csv_map() -> list:
    """按配置顺序对齐 weekly 目录与 robot_config CSV 路径"""
    weekly_folders = get_configured_weekly_folders()
    csv_paths = get_configured_csv_paths()
    if not weekly_folders or not csv_paths:
        return []
    if len(weekly_folders) != len(csv_paths):
        logger.warning(
            "weekly_result_folder 与 robot_config_csv 数量不一致: %s vs %s",
            len(weekly_folders),
            len(csv_paths),
        )
    size = min(len(weekly_folders), len(csv_paths))
    return list(zip(weekly_folders[:size], csv_paths[:size]))


def get_weekly_to_reference_dict_map() -> list:
    """按配置顺序对齐 weekly 目录与 reference dict CSV 路径"""
    weekly_folders = get_configured_weekly_folders()
    dict_paths = get_configured_reference_dict_paths()
    if not weekly_folders or not dict_paths:
        return []
    if len(weekly_folders) != len(dict_paths):
        logger.warning(
            "weekly_result_folder 与 reference_dict_csv 数量不一致: %s vs %s",
            len(weekly_folders),
            len(dict_paths),
        )
    size = min(len(weekly_folders), len(dict_paths))
    return list(zip(weekly_folders[:size], dict_paths[:size]))


def _find_latest_weeklyresult_csv(folder: str):
    if not folder:
        return None
    pattern = os.path.join(folder, "*weeklyresult.csv")
    matched = glob.glob(pattern)
    if not matched:
        return None
    return max(matched, key=os.path.getctime)


def _robot_in_weeklyresult_csv(robot: str, csv_path: str) -> bool:
    if not robot or not csv_path:
        return False
    robot = str(robot).strip()
    if not robot:
        return False

    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            with open(csv_path, "r", encoding=encoding, newline="") as file_obj:
                reader = csv.reader(file_obj)
                header = next(reader, None)
                if not header:
                    return False
                header_norm = [(h or "").strip().lower() for h in header]
                if "robot" not in header_norm:
                    return False
                robot_idx = header_norm.index("robot")
                for row in reader:
                    if robot_idx < len(row) and str(row[robot_idx]).strip() == robot:
                        return True
            return False
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            logger.warning("读取 weeklyresult 失败: %s (%s)", csv_path, exc)
            return False
    logger.warning("无法识别 weeklyresult 编码: %s", csv_path)
    return False


def resolve_robot_config_csv_path(robot: str) -> Path | None:
    """
    根据机器人所属的 weeklyresult 文件定位对应的 robot_config CSV。
    """
    mapping = get_weekly_to_config_csv_map()
    if not mapping:
        return None
    if len(mapping) == 1:
        return mapping[0][1]

    matched_paths = []
    for weekly_folder, config_path in mapping:
        latest_file = _find_latest_weeklyresult_csv(weekly_folder)
        if not latest_file:
            continue
        if _robot_in_weeklyresult_csv(robot, latest_file):
            matched_paths.append(config_path)

    if not matched_paths:
        return None
    if len(matched_paths) > 1:
        logger.warning(
            "机器人在多个 weeklyresult 中命中，使用第一个: robot=%s paths=%s",
            robot,
            matched_paths,
        )
    return matched_paths[0]


def resolve_reference_dict_csv_path(robot: str) -> Path | None:
    """
    根据机器人所属的 weeklyresult 文件定位对应的 reference dict CSV。
    """
    mapping = get_weekly_to_reference_dict_map()
    if not mapping:
        return None
    if len(mapping) == 1:
        return mapping[0][1]

    matched_paths = []
    for weekly_folder, dict_path in mapping:
        latest_file = _find_latest_weeklyresult_csv(weekly_folder)
        if not latest_file:
            continue
        if _robot_in_weeklyresult_csv(robot, latest_file):
            matched_paths.append(dict_path)

    if not matched_paths:
        return None
    if len(matched_paths) > 1:
        logger.warning(
            "机器人在多个 weeklyresult 中命中，使用第一个 reference dict: robot=%s paths=%s",
            robot,
            matched_paths,
        )
    return matched_paths[0]


def _iter_reference_rows(csv_path: Path):
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            with csv_path.open("r", encoding=encoding, newline="") as file_obj:
                reader = csv.reader(file_obj)
                for row in reader:
                    yield row
            return
        except UnicodeDecodeError:
            continue


def get_reference_entries_for_robot(robot: str) -> list:
    if not robot:
        return []
    dict_path = resolve_reference_dict_csv_path(robot)
    if dict_path is None or not dict_path.exists():
        logger.warning("reference dict CSV 不存在: robot=%s path=%s", robot, dict_path)
        return []

    entries = []
    seen = set()
    for row in _iter_reference_rows(dict_path):
        if not row or len(row) < 3:
            continue
        row_robot = (row[0] or "").strip()
        if row_robot != robot:
            continue
        reference = (row[1] or "").strip()
        if not reference:
            continue
        number_raw = (row[2] or "").strip()
        if number_raw == "":
            number = None
        else:
            try:
                number = float(number_raw)
            except ValueError:
                continue
        key = (row_robot, reference)
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            {"robot": row_robot, "reference": reference, "number": number}
        )
    return entries


def resolve_reference_number_from_csv(robot: str, reference: str):
    if not robot or not reference:
        return None
    dict_path = resolve_reference_dict_csv_path(robot)
    if dict_path is None or not dict_path.exists():
        logger.warning("reference dict CSV 不存在: robot=%s path=%s", robot, dict_path)
        return None

    for row in _iter_reference_rows(dict_path):
        if not row or len(row) < 3:
            continue
        row_robot = (row[0] or "").strip()
        row_reference = (row[1] or "").strip()
        if row_robot != robot or row_reference != reference:
            continue
        number_raw = (row[2] or "").strip()
        if number_raw == "":
            return None
        try:
            return float(number_raw)
        except ValueError:
            return None
    return None


def read_robot_config_csv(csv_path=None):
    """
    读取机器人配置CSV文件

    返回: list of dict - 每行数据为一个字典
    """
    if csv_path is None:
        csv_paths = get_configured_csv_paths()
    else:
        csv_paths = [Path(csv_path)]

    target_path = next((p for p in csv_paths if p.exists()), None)
    if not target_path:
        logger.warning(f"CSV配置文件不存在: {csv_paths}")
        return []

    data = []
    # 尝试多种编码读取 CSV 文件
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "gb2312"):
        try:
            with target_path.open("r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            logger.info(f"读取CSV配置文件成功: {len(data)} 条记录 -> {target_path} (编码: {encoding})")
            return data
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"读取CSV配置文件失败 (编码: {encoding}): {e}")
            continue
    logger.error(f"无法识别CSV文件编码: {target_path}")
    return []


def write_robot_config_csv(data, csv_path=None):
    """
    写入机器人配置CSV文件

    Args:
        data: list of dict - 要写入的数据
        csv_path: CSV文件路径，默认使用配置文件路径
    """
    if csv_path is None:
        csv_paths = get_configured_csv_paths()
    elif isinstance(csv_path, (list, tuple)):
        csv_paths = [Path(p) for p in csv_path]
    else:
        csv_paths = [Path(csv_path)]

    if not data:
        logger.warning("没有数据需要写入CSV")
        return

    try:
        # 定义字段顺序
        fieldnames = ['robot', 'shop', 'reference', 'number', 'type', 'tech', 'mark', 'remark']

        results = []
        for path in csv_paths:
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"写入CSV配置文件成功: {len(data)} 条记录 -> {path}")
            results.append(True)
        return all(results) if results else False
    except Exception as e:
        logger.error(f"写入CSV配置文件失败: {e}")
        return False


def _update_robot_in_single_csv(robot, updates, csv_path):
    if not csv_path.exists():
        logger.warning(f"CSV配置文件不存在: {csv_path}")
        return False

    # 尝试多种编码读取 CSV 文件
    data = None
    detected_encoding = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "gb2312"):
        try:
            temp_data = []
            found = False
            with csv_path.open("r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['robot'] == robot:
                        # 更新匹配的行
                        for key, value in updates.items():
                            if value is not None:
                                row[key] = str(value)
                        found = True
                    temp_data.append(row)

            if not found:
                logger.warning(f"在CSV中未找到机器人: {robot} ({csv_path})")
                return False

            data = temp_data
            detected_encoding = encoding
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.warning(f"读取CSV失败 (编码: {encoding}): {e}")
            continue

    if data is None:
        logger.error(f"无法识别CSV文件编码: {csv_path}")
        return False

    try:
        # 写回文件（使用检测到的编码或默认 utf-8-sig）
        write_encoding = detected_encoding if detected_encoding and detected_encoding != "utf-8-sig" else "utf-8-sig"
        fieldnames = ['robot', 'shop', 'reference', 'number', 'type', 'tech', 'mark', 'remark']
        with csv_path.open("w", encoding=write_encoding, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"CSV文件更新成功: robot={robot}, updates={updates}, file={csv_path}, 编码: {write_encoding}")
        return True

    except Exception as e:
        logger.error(f"更新CSV文件失败: {e}")
        return False


def update_robot_in_csv(robot, updates, csv_path=None):
    """
    在CSV文件中更新指定机器人的数据

    Args:
        robot: 机器人名称
        updates: dict - 要更新的字段，如 {'reference': 'new_ref', 'remark': 'new_remark'}
        csv_path: CSV文件路径

    返回: bool - 是否更新成功
    """
    if csv_path is None:
        csv_paths = get_configured_csv_paths()
    elif isinstance(csv_path, (list, tuple)):
        csv_paths = [Path(p) for p in csv_path]
    else:
        csv_paths = [Path(csv_path)]

    results = []
    for path in csv_paths:
        results.append(_update_robot_in_single_csv(robot, updates, path))
    return any(results) if results else False


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

    target_path = resolve_robot_config_csv_path(robot_component.robot)
    if target_path is None:
        logger.warning(
            "未找到匹配的 robot_config CSV，跳过同步: robot=%s",
            robot_component.robot,
        )
        return False
    return update_robot_in_csv(robot_component.robot, updates, csv_path=target_path)


def get_csv_backup_path(csv_path=None):
    """
    获取CSV备份文件路径
    """
    if csv_path is None:
        csv_path = get_default_csv_path()

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
        csv_path = get_default_csv_path()

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
