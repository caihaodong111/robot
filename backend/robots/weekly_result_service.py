"""
周结果 CSV 导入服务
从 weeklyresult.csv 文件导入数据到数据库
"""
import os
import glob
import logging
import csv
import tempfile
import hashlib
import json
from typing import Optional, Tuple
import pandas as pd
from django.db import transaction, connection
from datetime import datetime
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


CSV_FIELD_SPECS = [
    ("reference", "reference", "''"),
    ("number", "number", "0"),
    ("type", "type", "''"),
    ("tech", "tech", "''"),
    ("mark", "mark", "0"),
    ("remark", "remark", "''"),
    ("error1_c1", "error1_c1", None),
    ("tem1_m", "tem1_m", None),
    ("tem2_m", "tem2_m", None),
    ("tem3_m", "tem3_m", None),
    ("tem4_m", "tem4_m", None),
    ("tem5_m", "tem5_m", None),
    ("tem6_m", "tem6_m", None),
    ("tem7_m", "tem7_m", None),
    ("a1_e_rate", "A1_e_rate", None),
    ("a2_e_rate", "A2_e_rate", None),
    ("a3_e_rate", "A3_e_rate", None),
    ("a4_e_rate", "A4_e_rate", None),
    ("a5_e_rate", "A5_e_rate", None),
    ("a6_e_rate", "A6_e_rate", None),
    ("a7_e_rate", "A7_e_rate", None),
    ("a1_rms", "A1_Rms", None),
    ("a2_rms", "A2_Rms", None),
    ("a3_rms", "A3_Rms", None),
    ("a4_rms", "A4_Rms", None),
    ("a5_rms", "A5_Rms", None),
    ("a6_rms", "A6_Rms", None),
    ("a7_rms", "A7_Rms", None),
    ("a1_e", "A1_E", None),
    ("a2_e", "A2_E", None),
    ("a3_e", "A3_E", None),
    ("a4_e", "A4_E", None),
    ("a5_e", "A5_E", None),
    ("a6_e", "A6_E", None),
    ("a7_e", "A7_E", None),
    ("q1", "Q1", None),
    ("q2", "Q2", None),
    ("q3", "Q3", None),
    ("q4", "Q4", None),
    ("q5", "Q5", None),
    ("q6", "Q6", None),
    ("q7", "Q7", None),
    ("curr_a1_max", "Curr_A1_max", None),
    ("curr_a2_max", "Curr_A2_max", None),
    ("curr_a3_max", "Curr_A3_max", None),
    ("curr_a4_max", "Curr_A4_max", None),
    ("curr_a5_max", "Curr_A5_max", None),
    ("curr_a6_max", "Curr_A6_max", None),
    ("curr_a7_max", "Curr_A7_max", None),
    ("curr_a1_min", "Curr_A1_min", None),
    ("curr_a2_min", "Curr_A2_min", None),
    ("curr_a3_min", "Curr_A3_min", None),
    ("curr_a4_min", "Curr_A4_min", None),
    ("curr_a5_min", "Curr_A5_min", None),
    ("curr_a6_min", "Curr_A6_min", None),
    ("curr_a7_min", "Curr_A7_min", None),
    ("a1", "A1", "''"),
    ("a2", "A2", "''"),
    ("a3", "A3", "''"),
    ("a4", "A4", "''"),
    ("a5", "A5", "''"),
    ("a6", "A6", "''"),
    ("a7", "A7", "''"),
    ("p_change", "P_Change", None),
    ("level", "level", "'L'"),
]

def _load_path_config_file() -> dict:
    config_path = getattr(
        settings,
        "PATH_CONFIG_FILE",
        str(settings.BASE_DIR.parent / "path_config.json"),
    )
    if not config_path or not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("读取路径配置文件失败: %s (%s)", config_path, exc)
        return {}
    return data if isinstance(data, dict) else {}


def _get_weekly_result_sources_from_config() -> list:
    data = _load_path_config_file()
    entries = data.get("weekly_result_folders", []) if data else []
    sources = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("key", "")).strip()
        folder = str(entry.get("path") or entry.get("folder") or "").strip()
        description = str(entry.get("description") or "").strip()
        if not key or not folder:
            continue
        sources.append(
            {
                "key": key,
                "folder": folder,
                "description": description,
            }
        )
    return sources


def sync_weekly_result_path_config() -> list:
    sources = _get_weekly_result_sources_from_config()
    if not sources:
        return []
    from .models import PathConfig, RobotComponent

    for entry in sources:
        key = entry["key"]
        folder = entry["folder"]
        description = entry.get("description", "")
        PathConfig.set_path(f"weekly_result_folder:{key}", folder, description)
        RobotComponent.objects.filter(source_key=key).exclude(source_path=folder).update(
            source_path=folder
        )
    return sources


def _detect_csv_encoding(file_path: str) -> str:
    with open(file_path, "rb") as file_obj:
        sample = file_obj.read(4096)
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            sample.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _read_csv_header(file_path: str, encoding: str) -> list:
    with open(file_path, "r", encoding=encoding, newline="") as file_obj:
        reader = csv.reader(file_obj)
        header = next(reader, [])
    if header:
        header[0] = header[0].lstrip("\ufeff")
    return header


def _ensure_utf8_csv(file_path: str, encoding: str) -> Tuple[str, str, bool]:
    if encoding in ("utf-8", "utf-8-sig"):
        return file_path, encoding, False
    with open(file_path, "r", encoding=encoding, newline="") as src:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".csv", encoding="utf-8", newline=""
        ) as dst:
            for line in src:
                dst.write(line)
            return dst.name, "utf-8", True


def _sql_value(headers: set, source_col: str, default_sql: Optional[str]) -> str:
    if source_col not in headers:
        return default_sql if default_sql is not None else "NULL"
    if default_sql is None:
        return f"NULLIF(s.`{source_col}`, '')"
    return f"IFNULL(NULLIF(s.`{source_col}`, ''), {default_sql})"


def _mysql_load_csv(
    file_path: str,
    log_print_func,
    source_key: Optional[str] = None,
    source_path: Optional[str] = None,
) -> dict:
    encoding = _detect_csv_encoding(file_path)
    header = _read_csv_header(file_path, encoding)
    if not header or "robot" not in header:
        raise ValueError("CSV header 缺少 robot 列，无法使用 MySQL LOAD DATA")

    normalized_header = [col.strip() for col in header if col.strip()]
    normalized_header[0] = normalized_header[0].lstrip("\ufeff")
    header_set = set(normalized_header)

    tmp_file_path = file_path
    cleanup_tmp = False
    if encoding not in ("utf-8", "utf-8-sig"):
        tmp_file_path, encoding, cleanup_tmp = _ensure_utf8_csv(file_path, encoding)
        log_print_func(f"CSV 已转换为 UTF-8: {tmp_file_path}")

    tmp_table = "tmp_weeklyresult_import"

    columns_sql = ", ".join(f"`{col}`" for col in normalized_header)
    create_columns_sql = ", ".join(f"`{col}` TEXT NULL" for col in normalized_header)

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TEMPORARY TABLE IF EXISTS `{tmp_table}`")
            cursor.execute(
                f"CREATE TEMPORARY TABLE `{tmp_table}` (`__row_id` BIGINT NOT NULL, {create_columns_sql}) "
                "CHARACTER SET utf8mb4"
            )
            cursor.execute("SET @rownum := 0")
            load_sql = (
                f"LOAD DATA LOCAL INFILE %s INTO TABLE `{tmp_table}` "
                "CHARACTER SET utf8mb4 "
                "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' "
                "LINES TERMINATED BY '\\n' "
                "IGNORE 1 LINES "
                f"({columns_sql}) "
                "SET `__row_id` = (@rownum := @rownum + 1)"
            )
            cursor.execute(load_sql, [tmp_file_path])
            if normalized_header:
                last_col = normalized_header[-1]
                cursor.execute(
                    f"UPDATE `{tmp_table}` SET `{last_col}` = TRIM(TRAILING '\\r' FROM `{last_col}`)"
                )

            cursor.execute(
                f"ALTER TABLE `{tmp_table}` "
                "ADD COLUMN `__robot_norm` VARCHAR(64) NULL, "
                "ADD COLUMN `__shop_norm` VARCHAR(64) NULL"
            )
            cursor.execute(
                f"UPDATE `{tmp_table}` SET "
                f"`__robot_norm` = NULLIF(`robot`, ''), "
                f"`__shop_norm` = COALESCE(NULLIF(`shop`, ''), '未分配')"
                if "shop" in header_set
                else f"UPDATE `{tmp_table}` SET `__robot_norm` = NULLIF(`robot`, ''), `__shop_norm` = '未分配'"
            )

            cursor.execute(
                f"SELECT COUNT(*) FROM `{tmp_table}` WHERE `__robot_norm` IS NULL"
            )
            skipped_no_robot = cursor.fetchone()[0]

            cursor.execute(
                f"SELECT "
                f"  s.__shop_norm AS shop, "
                f"  COUNT(*) AS created "
                f"FROM `{tmp_table}` s "
                f"WHERE s.__robot_norm IS NOT NULL "
                f"GROUP BY s.__shop_norm"
            )
            shop_stats = {row[0]: {"created": int(row[1]), "updated": 0} for row in cursor.fetchall()}
            records_created = sum(stat["created"] for stat in shop_stats.values())
            records_updated = 0

            delete_sql = "DELETE FROM robot_components"
            delete_params = []
            if source_key:
                delete_sql += " WHERE source_key = %s"
                delete_params.append(source_key)
            elif source_path:
                delete_sql += " WHERE source_path = %s"
                delete_params.append(source_path)
            cursor.execute(delete_sql, delete_params)

            cursor.execute(
                "INSERT IGNORE INTO robot_groups (`key`, `name`, `expected_total`, `created_at`, `updated_at`) "
                f"SELECT DISTINCT s.__shop_norm, s.__shop_norm, 0, NOW(), NOW() "
                f"FROM `{tmp_table}` s "
                f"WHERE s.__shop_norm IS NOT NULL AND s.__shop_norm != ''"
            )

            insert_columns = [
                "`group_id`",
                "`robot`",
                "`shop`",
            ]
            insert_values = [
                "g.id",
                "s.__robot_norm",
                "s.__shop_norm",
            ]
            insert_params = []
            if source_key is not None:
                insert_columns.append("`source_key`")
                insert_values.append("%s")
                insert_params.append(source_key)
            if source_path is not None:
                insert_columns.append("`source_path`")
                insert_values.append("%s")
                insert_params.append(source_path)
            for target_col, source_col, default_sql in CSV_FIELD_SPECS:
                insert_columns.append(f"`{target_col}`")
                insert_values.append(_sql_value(header_set, source_col, default_sql))
            insert_columns.extend(["`created_at`", "`updated_at`"])
            insert_values.extend(["NOW()", "NOW()"])
            insert_sql = (
                f"INSERT INTO robot_components ({', '.join(insert_columns)}) "
                f"SELECT {', '.join(insert_values)} "
                f"FROM `{tmp_table}` s "
                "JOIN robot_groups g ON g.`key` = s.__shop_norm "
                "WHERE s.__robot_norm IS NOT NULL"
            )
            cursor.execute(insert_sql, insert_params)
    finally:
        if cleanup_tmp and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

    return {
        "records_created": records_created,
        "records_updated": records_updated,
        "shop_stats": shop_stats,
        "skipped_no_robot": skipped_no_robot,
        "total_rows": records_created + records_updated + skipped_no_robot,
    }


def _split_weekly_result_folders(value) -> list:
    """支持逗号/分号/换行分隔的多路径配置"""
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    parts = []
    for raw in str(value).replace("\n", ";").split(";"):
        parts.extend(raw.split(","))
    return [item.strip() for item in parts if item.strip()]


def _resolve_weekly_result_sources(folder_path: str = None) -> list:
    """优先使用路径配置文件，缺失时使用数据库配置或默认值"""
    if folder_path:
        folders = _split_weekly_result_folders(folder_path)
        return [
            {"key": None, "folder": folder, "description": ""}
            for folder in folders
        ]

    sources = _get_weekly_result_sources_from_config()
    if sources:
        return sources

    try:
        from .models import PathConfig
        stored = PathConfig.objects.filter(key__startswith="weekly_result_folder:")
        if stored.exists():
            entries = []
            for item in stored:
                key = item.key.split(":", 1)[1]
                entries.append(
                    {
                        "key": key,
                        "folder": item.path,
                        "description": item.description,
                    }
                )
            return entries
    except Exception:
        logger.warning("读取 weekly_result_folder 配置失败，使用默认路径")

    default_path = getattr(settings, "WEEKLY_RESULT_FOLDER", str(settings.BASE_DIR.parent))
    try:
        from .models import PathConfig
        resolved = PathConfig.get_path("weekly_result_folder", default_path)
    except Exception:
        resolved = default_path
    folders = _split_weekly_result_folders(resolved)
    if not folders:
        return []
    if len(folders) == 1:
        return [{"key": "default", "folder": folders[0], "description": ""}]
    return [
        {"key": f"default_{idx}", "folder": folder, "description": ""}
        for idx, folder in enumerate(folders, 1)
    ]


def _resolve_weekly_result_folders(folder_path: str = None) -> list:
    return [entry["folder"] for entry in _resolve_weekly_result_sources(folder_path)]


def _find_weekly_result_source(folder: str, sources: list) -> dict | None:
    if not folder:
        return None
    target = os.path.abspath(folder)
    for entry in sources:
        entry_folder = entry.get("folder")
        if not entry_folder:
            continue
        if os.path.abspath(entry_folder) == target:
            return entry
    return None


def _weekly_result_state_key(folder: str) -> str:
    digest = hashlib.sha1(folder.encode("utf-8")).hexdigest()
    # Keep within SystemConfig.key max_length=64 (24 + 40 = 64).
    return f"weekly_result_last_mtime{digest}"


def _get_last_import_state(folder: str) -> dict:
    from .models import SystemConfig
    key = _weekly_result_state_key(folder)
    raw = SystemConfig.get(key)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _set_last_import_state(folder: str, file_path: str, file_mtime: float) -> None:
    from .models import SystemConfig
    key = _weekly_result_state_key(folder)
    payload = {
        "folder": folder,
        "file": file_path,
        "mtime": file_mtime,
    }
    SystemConfig.set(key, json.dumps(payload), "weeklyresult csv last import mtime per folder")


def log_print(message: str):
    """打印日志到终端，带时间戳"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")
    return f"[{timestamp}] {message}"


def create_high_risk_snapshot(component) -> bool:
    """
    为高风险机器人创建数据快照

    Args:
        component: RobotComponent 实例

    Returns:
        是否成功创建快照
    """
    from .models import RobotHighRiskSnapshot

    # 字段与 RobotComponent 完全一致
    RobotHighRiskSnapshot.objects.create(
        group=component.group,
        robot=component.robot,
        shop=component.shop,
        reference=component.reference,
        number=component.number,
        type=component.type,
        tech=component.tech,
        mark=component.mark,
        remark=component.remark,
        error1_c1=component.error1_c1,
        tem1_m=component.tem1_m,
        tem2_m=component.tem2_m,
        tem3_m=component.tem3_m,
        tem4_m=component.tem4_m,
        tem5_m=component.tem5_m,
        tem6_m=component.tem6_m,
        tem7_m=component.tem7_m,
        a1_e_rate=component.a1_e_rate,
        a2_e_rate=component.a2_e_rate,
        a3_e_rate=component.a3_e_rate,
        a4_e_rate=component.a4_e_rate,
        a5_e_rate=component.a5_e_rate,
        a6_e_rate=component.a6_e_rate,
        a7_e_rate=component.a7_e_rate,
        a1_rms=component.a1_rms,
        a2_rms=component.a2_rms,
        a3_rms=component.a3_rms,
        a4_rms=component.a4_rms,
        a5_rms=component.a5_rms,
        a6_rms=component.a6_rms,
        a7_rms=component.a7_rms,
        a1_e=component.a1_e,
        a2_e=component.a2_e,
        a3_e=component.a3_e,
        a4_e=component.a4_e,
        a5_e=component.a5_e,
        a6_e=component.a6_e,
        a7_e=component.a7_e,
        q1=component.q1,
        q2=component.q2,
        q3=component.q3,
        q4=component.q4,
        q5=component.q5,
        q6=component.q6,
        q7=component.q7,
        curr_a1_max=component.curr_a1_max,
        curr_a2_max=component.curr_a2_max,
        curr_a3_max=component.curr_a3_max,
        curr_a4_max=component.curr_a4_max,
        curr_a5_max=component.curr_a5_max,
        curr_a6_max=component.curr_a6_max,
        curr_a7_max=component.curr_a7_max,
        curr_a1_min=component.curr_a1_min,
        curr_a2_min=component.curr_a2_min,
        curr_a3_min=component.curr_a3_min,
        curr_a4_min=component.curr_a4_min,
        curr_a5_min=component.curr_a5_min,
        curr_a6_min=component.curr_a6_min,
        curr_a7_min=component.curr_a7_min,
        a1=component.a1,
        a2=component.a2,
        a3=component.a3,
        a4=component.a4,
        a5=component.a5,
        a6=component.a6,
        a7=component.a7,
        p_change=component.p_change,
        level=component.level,
        source_key=component.source_key,
        source_path=component.source_path,
    )
    return True


def archive_high_risk_robots() -> dict:
    """
    将上次记录的高风险机器人数据存入历史快照表

    流程：
    1. 从 SystemConfig 获取上次记录的高风险机器人 robot 列表
    2. 根据 robot 列表从 robot_components 表获取数据
    3. 将数据存入 _robot_high_risk_snapshots 表

    Returns:
        归档结果统计
    """
    from .models import RobotComponent, SystemConfig

    # 获取上次记录的高风险机器人列表
    last_high_risk_robots = SystemConfig.get('last_high_risk_robots', '[]')

    try:
        import json
        robot_list = json.loads(last_high_risk_robots)
    except json.JSONDecodeError:
        log_print("警告：上次的高风险机器人列表格式错误，重新初始化")
        robot_list = []

    if not robot_list:
        # 兜底：SystemConfig 缺失或为空时，直接使用当前高风险机器人
        robot_list = list(
            RobotComponent.objects.filter(level='H').values_list('robot', flat=True)
        )
        if not robot_list:
            log_print("没有需要归档的高风险机器人（首次同步或上次无高风险数据）")
            return {'archived_count': 0, 'message': '没有需要归档的高风险机器人'}
        log_print("未找到上次高风险列表，改用当前高风险机器人进行归档")

    log_print(f"准备归档 {len(robot_list)} 个高风险机器人: {', '.join(robot_list[:10])}{'...' if len(robot_list) > 10 else ''}")

    # 获取这些机器人的数据
    components = RobotComponent.objects.filter(robot__in=robot_list)
    archived_count = 0

    for component in components:
        create_high_risk_snapshot(component)
        archived_count += 1

    log_print(f"已归档 {archived_count} 条高风险机器人数据到历史快照表")

    return {'archived_count': archived_count}


def save_current_high_risk_robots() -> None:
    """
    记录当前的高风险机器人列表到 SystemConfig
    供下次同步时归档使用
    """
    from .models import RobotComponent, SystemConfig
    import json

    # 获取当前 level='H' 的机器人列表
    high_risk_robots = list(
        RobotComponent.objects.filter(level='H').values_list('robot', flat=True).distinct()
    )

    # 存入 SystemConfig
    SystemConfig.set(
        'last_high_risk_robots',
        json.dumps(high_risk_robots),
        '上次同步时的高风险机器人列表（用于下次同步时归档）'
    )

    # 详细日志
    if high_risk_robots:
        log_print(f"已记录 {len(high_risk_robots)} 个高风险机器人，供下次同步时归档")
        log_print(f"高风险机器人列表: {', '.join(high_risk_robots[:10])}{'...' if len(high_risk_robots) > 10 else ''}")
    else:
        log_print("当前没有高风险机器人需要记录")


def get_latest_weeklyresult_csv(folder_path: str = None, project: str = None) -> str:
    """
    获取最新的 weeklyresult.csv 文件路径

    参数:
        folder_path: 文件夹路径，未提供则使用数据库配置或默认路径
        project: 项目名称（暂未使用，保留参数兼容性）

    返回:
        最新的 weeklyresult.csv 文件路径

    抛出:
        FileNotFoundError: 如果未找到文件
    """
    folder_paths = _resolve_weekly_result_folders(folder_path)
    if not folder_paths:
        raise FileNotFoundError("未配置 weeklyresult.csv 搜索路径")

    # 直接在指定路径查找所有 weeklyresult.csv 文件
    csv_files = []
    patterns = []
    for folder in folder_paths:
        pattern = os.path.join(folder, '*weeklyresult.csv')
        patterns.append(pattern)
        csv_files.extend(glob.glob(pattern))

    if not csv_files:
        raise FileNotFoundError(f"未找到匹配的 weeklyresult.csv 文件: {', '.join(patterns)}")

    # 按创建时间降序排序获取最新文件（Windows ctime 为创建时间）
    target_files = [(f, os.path.getctime(f)) for f in csv_files]
    sorted_files = sorted(target_files, key=lambda x: x[1], reverse=True)
    latest_file = sorted_files[0][0]

    return latest_file


def get_all_weeklyresult_csvs(folder_path: str = None, project: str = None) -> list:
    """
    获取所有路径中的 weeklyresult.csv 文件列表（按修改时间排序）

    参数:
        folder_path: 文件夹路径，未提供则使用数据库配置或默认路径
        project: 项目名称（暂未使用，保留参数兼容性）

    返回:
        所有 weeklyresult.csv 文件路径列表（按修改时间降序排序）

    抛出:
        FileNotFoundError: 如果未找到文件
    """
    folder_paths = _resolve_weekly_result_folders(folder_path)
    if not folder_paths:
        raise FileNotFoundError("未配置 weeklyresult.csv 搜索路径")

    # 在所有路径中查找 weeklyresult.csv 文件
    csv_files = []
    patterns = []
    for folder in folder_paths:
        pattern = os.path.join(folder, '*weeklyresult.csv')
        patterns.append(pattern)
        found_files = glob.glob(pattern)
        for f in found_files:
            csv_files.append((f, os.path.getmtime(f), folder))

    if not csv_files:
        raise FileNotFoundError(f"未找到匹配的 weeklyresult.csv 文件: {', '.join(patterns)}")

    # 按修改时间降序排序
    sorted_files = sorted(csv_files, key=lambda x: x[1], reverse=True)

    # 返回文件路径列表
    return [f[0] for f in sorted_files]


def get_latest_weeklyresult_csvs(folder_path: str = None, project: str = None) -> list:
    """
    获取每个路径下最新的 weeklyresult.csv 文件（按修改时间排序）

    参数:
        folder_path: 文件夹路径，未提供则使用数据库配置或默认路径
        project: 项目名称（暂未使用，保留参数兼容性）

    返回:
        每个路径下最新 weeklyresult.csv 文件路径列表（按修改时间降序排序）

    抛出:
        FileNotFoundError: 如果未找到文件
    """
    folder_paths = _resolve_weekly_result_folders(folder_path)
    if not folder_paths:
        raise FileNotFoundError("未配置 weeklyresult.csv 搜索路径")

    latest_files = []
    patterns = []
    for folder in folder_paths:
        pattern = os.path.join(folder, '*weeklyresult.csv')
        patterns.append(pattern)
        matched = glob.glob(pattern)
        if not matched:
            continue
        latest = max(matched, key=lambda x: os.path.getmtime(x))
        latest_files.append((latest, os.path.getmtime(latest)))

    if not latest_files:
        raise FileNotFoundError(f"未找到匹配的 weeklyresult.csv 文件: {', '.join(patterns)}")

    sorted_files = sorted(latest_files, key=lambda x: x[1], reverse=True)
    return [f[0] for f in sorted_files]


def get_latest_weeklyresult_csvs_with_meta(folder_path: str = None, project: str = None) -> list:
    """
    获取每个路径下最新的 weeklyresult.csv 文件及元信息（按修改时间排序）
    """
    sources = _resolve_weekly_result_sources(folder_path)
    if not sources:
        raise FileNotFoundError("未配置 weeklyresult.csv 搜索路径")

    latest_files = []
    patterns = []
    for entry in sources:
        folder = entry["folder"]
        pattern = os.path.join(folder, '*weeklyresult.csv')
        patterns.append(pattern)
        matched = glob.glob(pattern)
        if not matched:
            continue
        latest = max(matched, key=lambda x: os.path.getmtime(x))
        latest_files.append({
            "path": latest,
            "folder": folder,
            "mtime": os.path.getmtime(latest),
            "source_key": entry.get("key"),
            "source_path": folder,
        })

    if not latest_files:
        raise FileNotFoundError(f"未找到匹配的 weeklyresult.csv 文件: {', '.join(patterns)}")

    latest_files.sort(key=lambda item: item["mtime"], reverse=True)
    return latest_files


def parse_week_from_filename(filename: str) -> tuple:
    """
    从文件名解析日期
    支持格式：
    - 1.30_weeklyresult.csv (月.日)
    - 250410-250516 (YYMMDD-YYMMDD)

    参数:
        filename: CSV 文件名

    返回:
        (date_start, date_end) 日期元组
    """
    basename = os.path.basename(filename)
    date_start = None
    date_end = None

    import re

    # 尝试匹配格式: 1.30_weeklyresult.csv 或 01.30_weeklyresult.csv
    date_pattern = r'(\d{1,2})\.(\d{1,2})_weeklyresult\.csv'
    match = re.search(date_pattern, basename)

    if match:
        month_str, day_str = match.groups()
        try:
            # 假设是当前年份
            current_year = datetime.now().year
            date_obj = datetime.strptime(f"{current_year}-{month_str.zfill(2)}-{day_str.zfill(2)}", '%Y-%m-%d').date()
            date_start = date_obj
            date_end = date_obj
        except ValueError:
            pass
    else:
        # 尝试匹配旧格式 (YYMMDD-YYMMDD)
        old_pattern = r'(\d{6})-(\d{6})'
        old_match = re.search(old_pattern, basename)
        if old_match:
            start_str, end_str = old_match.groups()
            try:
                start_dt = datetime.strptime(start_str, '%y%m%d').date()
                end_dt = datetime.strptime(end_str, '%y%m%d').date()
                date_start = start_dt
                date_end = end_dt
            except ValueError:
                pass

    return date_start, date_end


def get_available_csv_files(folder_path: str = None, project: str = None) -> list:
    """
    获取所有可用的 weeklyresult.csv 文件列表

    参数:
        folder_path: 文件夹路径，未提供则使用数据库配置或默认路径
        project: 项目名称（暂未使用，保留参数兼容性）

    返回:
        文件信息列表:
        [
            {
                'path': '完整路径',
                'name': '文件名',
                'created_time': '创建时间',
                'week_start': '周开始日期',
                'week_end': '周结束日期'
            },
            ...
        ]
    """
    # 测试阶段使用本地路径
    folder_paths = _resolve_weekly_result_folders(folder_path)
    csv_files = []
    for folder in folder_paths:
        pattern = os.path.join(folder, '*weeklyresult.csv')
        csv_files.extend(glob.glob(pattern))

    results = []
    for f in csv_files:
        week_start, week_end = parse_week_from_filename(f)
        results.append({
            'path': f,
            'name': os.path.basename(f),
            'created_time': datetime.fromtimestamp(os.path.getmtime(f)).isoformat(),
            'week_start': week_start.isoformat() if week_start else None,
            'week_end': week_end.isoformat() if week_end else None,
        })

    # 按修改时间降序排序
    results.sort(key=lambda x: x['created_time'], reverse=True)
    return results


def import_robot_components_csv(
    file_path: str = None,
    folder_path: str = None,
    project: str = None,
    source: str = "manual",
    use_mysql_load_data: Optional[bool] = None
) -> dict:
    """
    直接将 weeklyresult.csv 文件导入到 RobotComponent 表
    跳过 WeeklyResult 表，直接更新机器人状态界面数据

    多文件模式：自动导入所有路径中的 CSV 文件

    参数:
        file_path: CSV 文件路径，如果为 None 则自动查找所有 CSV 文件
        folder_path: 文件夹路径（用于自动查找）
        project: 项目名称（用于自动查找）
        source: 数据来源 ("manual" 手动同步 / "auto" 自动同步)

    返回:
        导入结果统计
    """
    from .models import RobotComponent, RobotGroup, RefreshLog

    # 获取文件路径（支持多文件）
    log_print("开始导入流程...")
    sync_weekly_result_path_config()
    csv_files = []
    skipped_files = []
    if file_path is None:
        log_print("未指定文件路径，正在查找每个路径下最新CSV文件...")
        candidates = get_latest_weeklyresult_csvs_with_meta(folder_path, project)
        log_print(f"找到 {len(candidates)} 个 CSV 文件(每个路径最新):")
        for i, info in enumerate(candidates, 1):
            log_print(f"  {i}. {os.path.basename(info['path'])}")
        force_import = not RobotComponent.objects.exists()
        if force_import:
            log_print("检测到 robot_components 为空，忽略上次导入状态，强制导入最新CSV")
        for info in candidates:
            if not force_import:
                last_state = _get_last_import_state(info["folder"])
                last_mtime = last_state.get("mtime") if last_state else None
                if last_mtime is not None and info["mtime"] <= float(last_mtime):
                    skipped_files.append({
                        "path": info["path"],
                        "folder": info["folder"],
                    })
                    continue
            csv_files.append(info)
    else:
        log_print(f"使用指定文件: {file_path}")
        sources = _resolve_weekly_result_sources(None)
        matched_source = _find_weekly_result_source(os.path.dirname(file_path), sources)
        csv_files = [{
            "path": file_path,
            "folder": os.path.dirname(file_path),
            "mtime": os.path.getmtime(file_path),
            "source_key": matched_source.get("key") if matched_source else None,
            "source_path": matched_source.get("folder") if matched_source else os.path.dirname(file_path),
        }]

    if not csv_files:
        log_print("未发现更新的CSV文件，跳过同步")
        return {
            "success": True,
            "skipped": True,
            "message": "no new weeklyresult.csv to import",
            "records_created": 0,
            "records_updated": 0,
            "records_deleted": 0,
            "total_records": 0,
            "shop_stats": {},
            "skipped_files": skipped_files,
        }

    # 步骤0：先归档上次的高风险数据（必须在导入新数据之前执行！）
    log_print("开始归档上次的高风险数据...")
    archive_result = archive_high_risk_robots()
    if archive_result.get('archived_count', 0) > 0:
        log_print(f"已归档 {archive_result['archived_count']} 条高风险数据到历史快照表")

    # 全局统计信息（累加所有文件）
    total_records_created = 0
    total_records_updated = 0
    total_skipped = 0
    all_shop_stats = {}  # 累加各车间统计

    # 处理辅助函数（定义在循环外）
    def safe_float(val):
        if pd.isna(val) or val == '':
            return None
        if isinstance(val, str):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def safe_str(val):
        if pd.isna(val):
            return ''
        return str(val) if val is not None else ''

    def safe_int(val):
        if pd.isna(val) or val == '':
            return 0
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    if use_mysql_load_data is None:
        use_mysql_load_data = getattr(settings, "ENABLE_MYSQL_LOAD_DATA", False)

    # 循环处理每个 CSV 文件
    batch_size = 1000

    for file_idx, file_info in enumerate(csv_files, 1):
        current_file = file_info["path"]
        source_key = file_info.get("source_key")
        source_path = file_info.get("source_path") or file_info.get("folder")
        log_print(f"\n{'='*60}")
        log_print(f"正在处理第 {file_idx}/{len(csv_files)} 个文件: {os.path.basename(current_file)}")
        log_print(f"{'='*60}")

        # 解析日期
        week_start, week_end = parse_week_from_filename(current_file)
        source_file = os.path.basename(current_file)
        if week_start:
            log_print(f"解析日期范围: {week_start} ~ {week_end}")

        load_result = None
        if use_mysql_load_data:
            log_print("使用 MySQL LOAD DATA 进行快速导入...")
            try:
                load_result = _mysql_load_csv(
                    current_file,
                    log_print,
                    source_key=source_key,
                    source_path=source_path,
                )
            except Exception as exc:
                log_print(f"MySQL LOAD DATA 导入失败，回退到 ORM 批量导入: {exc}")
                load_result = None

        if load_result is not None:
            records_created = load_result["records_created"]
            records_updated = load_result["records_updated"]
            shop_stats = load_result["shop_stats"]
            skipped_no_robot = load_result["skipped_no_robot"]
            total_rows = load_result["total_rows"]
            parsed_rows = []
        else:
            # 读取 CSV 文件（兼容常见中文编码）
            log_print("正在读取CSV文件...")
            df = None
            read_errors = []
            for encoding in ("utf-8", "utf-8-sig", "gb18030"):
                try:
                    df = pd.read_csv(current_file, encoding=encoding)
                    log_print(f"已使用编码 {encoding} 读取CSV")
                    break
                except UnicodeDecodeError as e:
                    read_errors.append(f"{encoding}: {e}")
            if df is None:
                raise UnicodeDecodeError(
                    "csv",
                    b"",
                    0,
                    0,
                    "无法识别CSV编码，已尝试 utf-8/utf-8-sig/gb18030; " + "; ".join(read_errors)
                )
            total_rows = len(df)
            log_print(f"读取完成，共 {total_rows} 行数据")

            # 当前文件统计信息
            records_created = 0
            records_updated = 0
            records_protected = 0
            shop_stats = {}
            skipped_no_robot = 0

            log_print("开始处理数据行...")

            raw_records = df.to_dict(orient="records")
            parsed_rows = []
            shop_names = set()
            robots_to_replace = set()

            for idx, row in enumerate(raw_records, 1):
                shop_name = safe_str(row.get('shop', ''))
                if not shop_name:
                    shop_name = '未分配'

                robot_val = safe_str(row.get('robot', ''))
                if not robot_val:
                    skipped_no_robot += 1
                    continue

                parsed_rows.append((robot_val, shop_name, row))
                shop_names.add(shop_name)
                robots_to_replace.add(robot_val)

                if shop_name not in shop_stats:
                    shop_stats[shop_name] = {'created': 0, 'updated': 0}

                if idx % 5000 == 0:
                    log_print(f"已预处理 {idx}/{total_rows} 行...")

        if load_result is None:
            if not parsed_rows:
                log_print("当前文件没有有效的 robot 数据，跳过导入")
                total_skipped += skipped_no_robot
                continue

            existing_groups = {g.key: g for g in RobotGroup.objects.filter(key__in=shop_names)}
            missing_keys = [key for key in shop_names if key not in existing_groups]
            if missing_keys:
                RobotGroup.objects.bulk_create(
                    [RobotGroup(key=key, name=key, expected_total=0) for key in missing_keys],
                    ignore_conflicts=True,
                    batch_size=batch_size,
                )
                existing_groups = {g.key: g for g in RobotGroup.objects.filter(key__in=shop_names)}

            if source_key or source_path:
                scope_desc = source_key or source_path
                log_print(f"删除来源 {scope_desc} 下的旧数据...")
                delete_qs = RobotComponent.objects.all()
                if source_key:
                    delete_qs = delete_qs.filter(source_key=source_key)
                else:
                    delete_qs = delete_qs.filter(source_path=source_path)
                delete_qs.delete()
            elif robots_to_replace:
                log_print(f"删除当前文件涉及的 {len(robots_to_replace)} 个机器人旧数据...")
                RobotComponent.objects.filter(robot__in=robots_to_replace).delete()

            pending_create = []

            for idx, (robot_val, shop_name, row) in enumerate(parsed_rows, 1):
                group = existing_groups.get(shop_name)
                if group is None:
                    skipped_no_robot += 1
                    continue

                values = dict(
                    group_id=group.id,
                    robot=robot_val,
                    shop=shop_name,
                    reference=safe_str(row.get('reference', '')),
                    number=safe_int(row.get('number', 0)),
                    type=safe_str(row.get('type', '')),
                    tech=safe_str(row.get('tech', '')),
                    mark=safe_int(row.get('mark', 0)),
                    remark=safe_str(row.get('remark', '')),
                    level=safe_str(row.get('level', 'L')),
                    error1_c1=safe_float(row.get('error1_c1')),
                    tem1_m=safe_float(row.get('tem1_m')),
                    tem2_m=safe_float(row.get('tem2_m')),
                    tem3_m=safe_float(row.get('tem3_m')),
                    tem4_m=safe_float(row.get('tem4_m')),
                    tem5_m=safe_float(row.get('tem5_m')),
                    tem6_m=safe_float(row.get('tem6_m')),
                    tem7_m=safe_float(row.get('tem7_m')),
                    a1_e_rate=safe_float(row.get('A1_e_rate')),
                    a2_e_rate=safe_float(row.get('A2_e_rate')),
                    a3_e_rate=safe_float(row.get('A3_e_rate')),
                    a4_e_rate=safe_float(row.get('A4_e_rate')),
                    a5_e_rate=safe_float(row.get('A5_e_rate')),
                    a6_e_rate=safe_float(row.get('A6_e_rate')),
                    a7_e_rate=safe_float(row.get('A7_e_rate')),
                    a1_rms=safe_float(row.get('A1_Rms')),
                    a2_rms=safe_float(row.get('A2_Rms')),
                    a3_rms=safe_float(row.get('A3_Rms')),
                    a4_rms=safe_float(row.get('A4_Rms')),
                    a5_rms=safe_float(row.get('A5_Rms')),
                    a6_rms=safe_float(row.get('A6_Rms')),
                    a7_rms=safe_float(row.get('A7_Rms')),
                    a1_e=safe_float(row.get('A1_E')),
                    a2_e=safe_float(row.get('A2_E')),
                    a3_e=safe_float(row.get('A3_E')),
                    a4_e=safe_float(row.get('A4_E')),
                    a5_e=safe_float(row.get('A5_E')),
                    a6_e=safe_float(row.get('A6_E')),
                    a7_e=safe_float(row.get('A7_E')),
                    q1=safe_float(row.get('Q1')),
                    q2=safe_float(row.get('Q2')),
                    q3=safe_float(row.get('Q3')),
                    q4=safe_float(row.get('Q4')),
                    q5=safe_float(row.get('Q5')),
                    q6=safe_float(row.get('Q6')),
                    q7=safe_float(row.get('Q7')),
                    curr_a1_max=safe_float(row.get('Curr_A1_max')),
                    curr_a2_max=safe_float(row.get('Curr_A2_max')),
                    curr_a3_max=safe_float(row.get('Curr_A3_max')),
                    curr_a4_max=safe_float(row.get('Curr_A4_max')),
                    curr_a5_max=safe_float(row.get('Curr_A5_max')),
                    curr_a6_max=safe_float(row.get('Curr_A6_max')),
                    curr_a7_max=safe_float(row.get('Curr_A7_max')),
                    curr_a1_min=safe_float(row.get('Curr_A1_min')),
                    curr_a2_min=safe_float(row.get('Curr_A2_min')),
                    curr_a3_min=safe_float(row.get('Curr_A3_min')),
                    curr_a4_min=safe_float(row.get('Curr_A4_min')),
                    curr_a5_min=safe_float(row.get('Curr_A5_min')),
                    curr_a6_min=safe_float(row.get('Curr_A6_min')),
                    curr_a7_min=safe_float(row.get('Curr_A7_min')),
                    a1=safe_str(row.get('A1')),
                    a2=safe_str(row.get('A2')),
                    a3=safe_str(row.get('A3')),
                    a4=safe_str(row.get('A4')),
                    a5=safe_str(row.get('A5')),
                    a6=safe_str(row.get('A6')),
                    a7=safe_str(row.get('A7')),
                    p_change=safe_float(row.get('P_Change')),
                    source_key=source_key,
                    source_path=source_path,
                )

                pending_create.append(RobotComponent(**values))
                records_created += 1
                shop_stats[shop_name]['created'] += 1

                if len(pending_create) >= batch_size:
                    RobotComponent.objects.bulk_create(pending_create, batch_size=batch_size)
                    pending_create = []

                if idx % 5000 == 0:
                    log_print(f"已准备 {idx}/{len(parsed_rows)} 行...")

            if pending_create:
                RobotComponent.objects.bulk_create(pending_create, batch_size=batch_size)

        # 当前文件处理完成，累加统计到全局统计
        log_print(f"\n文件 {os.path.basename(current_file)} 处理完成!")
        log_print(f"  - 新增: {records_created} 条")
        log_print(f"  - 更新: {records_updated} 条")
        log_print(f"  - 跳过: {skipped_no_robot} 条")

        # 累加到全局统计
        total_records_created += records_created
        total_records_updated += records_updated
        total_skipped += skipped_no_robot

        # 累加车间统计
        for shop, stats in shop_stats.items():
            if shop not in all_shop_stats:
                all_shop_stats[shop] = {'created': 0, 'updated': 0}
            all_shop_stats[shop]['created'] += stats['created']
            all_shop_stats[shop]['updated'] += stats['updated']

        _set_last_import_state(
            file_info["folder"],
            current_file,
            file_info["mtime"],
        )

    # 所有文件处理完成
    log_print(f"\n{'='*60}")
    log_print(f"所有文件处理完成！")
    log_print(f"{'='*60}")
    log_print(f"总统计:")
    log_print(f"  - 总新增记录: {total_records_created} 条")
    log_print(f"  - 总更新记录: {total_records_updated} 条")
    log_print(f"  - 总跳过记录: {total_skipped} 条")
    log_print(f"  - 总有效记录: {total_records_created + total_records_updated} 条")
    log_print("\n各车间总统计:")
    for shop, stats in sorted(all_shop_stats.items()):
        log_print(f"  - {shop}: 新增 {stats['created']} 条, 更新 {stats['updated']} 条")
    log_print(f"{'='*60}\n")

    # 记录同步时间
    from django.utils import timezone
    from .models import SystemConfig
    sync_time = timezone.now().isoformat()
    SystemConfig.set(
        'last_sync_time',
        sync_time,
        '最后同步机器人数据的时间'
    )
    log_print(f"已记录同步时间: {sync_time}")

    # 记录当前的高风险机器人列表，供下次同步时归档使用
    save_current_high_risk_robots()

    # 写入刷新日志（使用第一个文件的信息作为代表）
    first_file = csv_files[0]["path"] if csv_files else "unknown"
    first_week_start, _ = parse_week_from_filename(first_file)

    RefreshLog.objects.create(
        source=source,
        trigger="scheduled" if source == "auto" else "manual",
        status="success",
        source_file=os.path.basename(first_file),
        file_date=first_week_start,
        records_created=total_records_created,
        records_updated=total_records_updated,
        records_deleted=0,
        total_records=total_records_created + total_records_updated,
    )
    log_print(f"已记录刷新日志: {source} 同步完成")

    try:
        from .tasks import _refresh_reference_dict
        log_print("开始同步 reference 字典...")
        _refresh_reference_dict()
        log_print("reference 字典同步完成")
    except Exception as exc:
        log_print(f"reference 字典同步失败: {exc}")

    return {
        'success': True,
        'file': first_file,
        'source_file': os.path.basename(first_file),
        'records_created': total_records_created,
        'records_updated': total_records_updated,
        'records_protected': 0,
        'total_records': total_records_created + total_records_updated,
        'shop_stats': all_shop_stats,
        'skipped_no_robot': total_skipped,
        'total_rows': total_records_created + total_records_updated + total_skipped,
        'date': first_week_start.isoformat() if first_week_start else None,
    }
