"""
周结果 CSV 导入服务
从 weeklyresult.csv 文件导入数据到数据库
"""
import os
import glob
import pandas as pd
from datetime import datetime
from django.utils import timezone
from django.conf import settings


def log_print(message: str):
    """打印日志到终端，带时间戳"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")
    return f"[{timestamp}] {message}"


def add_to_high_risk_history(component, source_file: str = "", record_source: str = "sync") -> bool:
    """
    将高风险机器人添加到历史记录表

    Args:
        component: RobotComponent 实例
        source_file: 数据来源文件名
        record_source: 记录来源 (sync/manual/api)

    Returns:
        是否成功添加到历史表
    """
    from .models import HighRiskHistory

    # 始终追加新记录到历史表（不检查是否已存在）
    HighRiskHistory.objects.create(
        component=component,
        part_no=component.part_no,
        group_key=component.group.key,
        group_name=component.group.name,
        robot_id=component.robot_id,
        name=component.name,
        reference_no=component.reference_no,
        number=component.number,
        type_spec=component.type_spec,
        tech=component.tech,
        mark=component.mark,
        remark=component.remark,
        checks=component.checks,
        level=component.level,
        status=component.status,
        battery=component.battery,
        health=component.health,
        motor_temp=component.motor_temp,
        network_latency=component.network_latency,
        last_seen=component.last_seen,
        risk_score=component.risk_score,
        risk_level=component.risk_level,
        record_source=record_source
    )
    return True


def create_high_risk_snapshot(component, source_file: str = "", snapshot_source: str = "manual") -> bool:
    """
    为高风险机器人创建数据快照

    Args:
        component: RobotComponent 实例
        source_file: 数据来源文件名
        snapshot_source: 快照来源 (manual/auto_sync/api)

    Returns:
        是否创建了新快照
    """
    from .models import RobotHighRiskSnapshot

    part_no = component.part_no

    # 检查是否已存在快照
    existing = RobotHighRiskSnapshot.objects.filter(part_no=part_no).first()
    if existing:
        # 更新现有快照
        existing.component = component
        existing.group_key = component.group.key
        existing.group_name = component.group.name
        existing.robot_id = component.robot_id
        existing.name = component.name
        existing.reference_no = component.reference_no
        existing.number = component.number
        existing.type_spec = component.type_spec
        existing.tech = component.tech
        existing.mark = component.mark
        existing.remark = component.remark
        existing.checks = component.checks
        existing.level = component.level
        existing.status = component.status
        existing.battery = component.battery
        existing.health = component.health
        existing.motor_temp = component.motor_temp
        existing.network_latency = component.network_latency
        existing.last_seen = component.last_seen
        existing.risk_score = component.risk_score
        existing.risk_level = component.risk_level
        existing.risk_history = component.risk_history
        existing.snapshot_source = snapshot_source
        existing.is_active = True
        existing.save(update_fields=[
            'component', 'group_key', 'group_name', 'robot_id', 'name',
            'reference_no', 'number', 'type_spec', 'tech', 'mark', 'remark',
            'checks', 'level', 'status', 'battery', 'health', 'motor_temp',
            'network_latency', 'last_seen', 'risk_score', 'risk_level',
            'risk_history', 'snapshot_source', 'is_active'
        ])
        return False

    # 创建新快照
    RobotHighRiskSnapshot.objects.create(
        component=component,
        part_no=part_no,
        group_key=component.group.key,
        group_name=component.group.name,
        robot_id=component.robot_id,
        name=component.name,
        reference_no=component.reference_no,
        number=component.number,
        type_spec=component.type_spec,
        tech=component.tech,
        mark=component.mark,
        remark=component.remark,
        checks=component.checks,
        level=component.level,
        status=component.status,
        battery=component.battery,
        health=component.health,
        motor_temp=component.motor_temp,
        network_latency=component.network_latency,
        last_seen=component.last_seen,
        risk_score=component.risk_score,
        risk_level=component.risk_level,
        risk_history=component.risk_history,
        snapshot_reason=f"从 {source_file} 导入时等级为 H",
        snapshot_source=snapshot_source,
        is_active=True
    )
    return True


def get_latest_weeklyresult_csv(folder_path: str = None, project: str = None) -> str:
    """
    获取最新的 weeklyresult.csv 文件路径

    参数:
        folder_path: 文件夹路径，测试阶段默认为 '/Users/caihd/Desktop/sg'
        project: 项目名称（暂未使用，保留参数兼容性）

    返回:
        最新的 weeklyresult.csv 文件路径

    抛出:
        FileNotFoundError: 如果未找到文件
    """
    # 测试阶段使用本地路径
    if folder_path is None:
        folder_path = '/Users/caihd/Desktop/sg'

    # 直接在指定路径查找所有 weeklyresult.csv 文件
    pattern = os.path.join(folder_path, '*weeklyresult.csv')
    csv_files = glob.glob(pattern)

    if not csv_files:
        raise FileNotFoundError(f"未找到匹配的 weeklyresult.csv 文件: {pattern}")

    # 按修改时间降序排序获取最新文件
    target_files = [(f, os.path.getmtime(f)) for f in csv_files]
    sorted_files = sorted(target_files, key=lambda x: x[1], reverse=True)
    latest_file = sorted_files[0][0]

    return latest_file


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


def import_weeklyresult_csv(file_path: str = None, folder_path: str = None, project: str = None) -> dict:
    """
    从 weeklyresult.csv 文件导入数据到数据库

    参数:
        file_path: CSV 文件路径，如果为 None 则自动获取最新文件
        folder_path: 文件夹路径（用于自动查找）
        project: 项目名称（用于自动查找）

    返回:
        导入结果统计:
        {
            'success': True,
            'file': '文件路径',
            'records_imported': 100,
            'records_updated': 10,
            'week_start': '2025-04-10',
            'week_end': '2025-05-16'
        }
    """
    from .models import WeeklyResult

    # 获取文件路径
    if file_path is None:
        file_path = get_latest_weeklyresult_csv(folder_path, project)

    # 解析周日期
    week_start, week_end = parse_week_from_filename(file_path)
    source_file = os.path.basename(file_path)

    # 读取 CSV 文件
    df = pd.read_csv(file_path)

    # 统计信息
    records_imported = 0
    records_updated = 0

    # 删除该批次之前的旧数据（可选，根据需求决定是否保留历史数据）
    # WeeklyResult.objects.filter(source_file=source_file).delete()

    for _, row in df.iterrows():
        # 处理 NaN 值
        def safe_float(val):
            if pd.isna(val) or val == '':
                return None
            # 处理字符串值（如 "high"）
            if isinstance(val, str):
                return None  # 将 "high" 等字符串值转换为 None
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

        # 检查是否已存在相同机器人和周的数据
        existing = WeeklyResult.objects.filter(
            robot=safe_str(row.get('robot', '')),
            source_file=source_file
        ).first()

        if existing:
            # 更新现有记录
            existing.shop = safe_str(row.get('shop', ''))
            existing.reference = safe_str(row.get('reference', ''))
            existing.number = safe_float(row.get('number'))
            existing.type = safe_str(row.get('type', ''))
            existing.tech = safe_str(row.get('tech', ''))
            existing.mark = safe_int(row.get('mark', 0))
            existing.remark = safe_str(row.get('remark', ''))
            existing.error1_c1 = safe_float(row.get('error1_c1'))
            existing.tem1_m = safe_float(row.get('tem1_m'))
            existing.tem2_m = safe_float(row.get('tem2_m'))
            existing.tem3_m = safe_float(row.get('tem3_m'))
            existing.tem4_m = safe_float(row.get('tem4_m'))
            existing.tem5_m = safe_float(row.get('tem5_m'))
            existing.tem6_m = safe_float(row.get('tem6_m'))
            existing.tem7_m = safe_float(row.get('tem7_m'))
            existing.a1_e_rate = safe_float(row.get('A1_e_rate'))
            existing.a2_e_rate = safe_float(row.get('A2_e_rate'))
            existing.a3_e_rate = safe_float(row.get('A3_e_rate'))
            existing.a4_e_rate = safe_float(row.get('A4_e_rate'))
            existing.a5_e_rate = safe_float(row.get('A5_e_rate'))
            existing.a6_e_rate = safe_float(row.get('A6_e_rate'))
            existing.a7_e_rate = safe_float(row.get('A7_e_rate'))
            existing.a1_rms = safe_float(row.get('A1_Rms'))
            existing.a2_rms = safe_float(row.get('A2_Rms'))
            existing.a3_rms = safe_float(row.get('A3_Rms'))
            existing.a4_rms = safe_float(row.get('A4_Rms'))
            existing.a5_rms = safe_float(row.get('A5_Rms'))
            existing.a6_rms = safe_float(row.get('A6_Rms'))
            existing.a7_rms = safe_float(row.get('A7_Rms'))
            existing.a1_e = safe_float(row.get('A1_E'))
            existing.a2_e = safe_float(row.get('A2_E'))
            existing.a3_e = safe_float(row.get('A3_E'))
            existing.a4_e = safe_float(row.get('A4_E'))
            existing.a5_e = safe_float(row.get('A5_E'))
            existing.a6_e = safe_float(row.get('A6_E'))
            existing.a7_e = safe_float(row.get('A7_E'))
            existing.q1 = safe_float(row.get('Q1'))
            existing.q2 = safe_float(row.get('Q2'))
            existing.q3 = safe_float(row.get('Q3'))
            existing.q4 = safe_float(row.get('Q4'))
            existing.q5 = safe_float(row.get('Q5'))
            existing.q6 = safe_float(row.get('Q6'))
            existing.q7 = safe_float(row.get('Q7'))
            existing.curr_a1_max = safe_float(row.get('Curr_A1_max'))
            existing.curr_a2_max = safe_float(row.get('Curr_A2_max'))
            existing.curr_a3_max = safe_float(row.get('Curr_A3_max'))
            existing.curr_a4_max = safe_float(row.get('Curr_A4_max'))
            existing.curr_a5_max = safe_float(row.get('Curr_A5_max'))
            existing.curr_a6_max = safe_float(row.get('Curr_A6_max'))
            existing.curr_a7_max = safe_float(row.get('Curr_A7_max'))
            existing.curr_a1_min = safe_float(row.get('Curr_A1_min'))
            existing.curr_a2_min = safe_float(row.get('Curr_A2_min'))
            existing.curr_a3_min = safe_float(row.get('Curr_A3_min'))
            existing.curr_a4_min = safe_float(row.get('Curr_A4_min'))
            existing.curr_a5_min = safe_float(row.get('Curr_A5_min'))
            existing.curr_a6_min = safe_float(row.get('Curr_A6_min'))
            existing.curr_a7_min = safe_float(row.get('Curr_A7_min'))
            existing.a1 = safe_float(row.get('A1'))
            existing.a2 = safe_float(row.get('A2'))
            existing.a3 = safe_float(row.get('A3'))
            existing.a4 = safe_float(row.get('A4'))
            existing.a5 = safe_float(row.get('A5'))
            existing.a6 = safe_float(row.get('A6'))
            existing.a7 = safe_float(row.get('A7'))
            existing.p_change = safe_float(row.get('P_Change'))
            existing.level = safe_str(row.get('level', 'L'))
            existing.week_start = week_start
            existing.week_end = week_end
            existing.save()
            records_updated += 1
        else:
            # 创建新记录
            WeeklyResult.objects.create(
                robot=safe_str(row.get('robot', '')),
                shop=safe_str(row.get('shop', '')),
                reference=safe_str(row.get('reference', '')),
                number=safe_float(row.get('number')),
                type=safe_str(row.get('type', '')),
                tech=safe_str(row.get('tech', '')),
                mark=safe_int(row.get('mark', 0)),
                remark=safe_str(row.get('remark', '')),
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
                a1=safe_float(row.get('A1')),
                a2=safe_float(row.get('A2')),
                a3=safe_float(row.get('A3')),
                a4=safe_float(row.get('A4')),
                a5=safe_float(row.get('A5')),
                a6=safe_float(row.get('A6')),
                a7=safe_float(row.get('A7')),
                p_change=safe_float(row.get('P_Change')),
                level=safe_str(row.get('level', 'L')),
                source_file=source_file,
                week_start=week_start,
                week_end=week_end,
            )
            records_imported += 1

    return {
        'success': True,
        'file': file_path,
        'source_file': source_file,
        'records_imported': records_imported,
        'records_updated': records_updated,
        'total_records': records_imported + records_updated,
        'week_start': week_start.isoformat() if week_start else None,
        'week_end': week_end.isoformat() if week_end else None,
    }


def get_available_csv_files(folder_path: str = None, project: str = None) -> list:
    """
    获取所有可用的 weeklyresult.csv 文件列表

    参数:
        folder_path: 文件夹路径，测试阶段默认为 '/Users/caihd/Desktop/sg'
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
    if folder_path is None:
        folder_path = '/Users/caihd/Desktop/sg'

    pattern = os.path.join(folder_path, '*weeklyresult.csv')
    csv_files = glob.glob(pattern)

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


def import_robot_components_csv(file_path: str = None, folder_path: str = None, project: str = None) -> dict:
    """
    直接将 weeklyresult.csv 文件导入到 RobotComponent 表
    跳过 WeeklyResult 表，直接更新机器人状态界面数据

    参数:
        file_path: CSV 文件路径，如果为 None 则自动获取最新文件
        folder_path: 文件夹路径（用于自动查找）
        project: 项目名称（用于自动查找）

    返回:
        导入结果统计
    """
    from .models import RobotComponent, RobotGroup

    # 获取文件路径
    log_print("开始导入流程...")
    if file_path is None:
        log_print("未指定文件路径，正在查找最新CSV文件...")
        file_path = get_latest_weeklyresult_csv(folder_path, project)
        log_print(f"找到文件: {file_path}")
    else:
        log_print(f"使用指定文件: {file_path}")

    # 解析日期
    week_start, week_end = parse_week_from_filename(file_path)
    source_file = os.path.basename(file_path)
    if week_start:
        log_print(f"解析日期范围: {week_start} ~ {week_end}")

    # 读取 CSV 文件
    log_print("正在读取CSV文件...")
    df = pd.read_csv(file_path)
    total_rows = len(df)
    log_print(f"读取完成，共 {total_rows} 行数据")

    # 统计信息
    records_created = 0
    records_updated = 0
    records_protected = 0
    shop_stats = {}
    skipped_no_robot = 0

    log_print("开始处理数据行...")

    for idx, row in df.iterrows():
        # 处理 NaN 值
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

        # 获取车间名称，如果为空则使用默认值
        shop_name = safe_str(row.get('shop', ''))
        if not shop_name:
            shop_name = '未分配'  # 空车间使用"未分配"

        # 统计各车间数量
        if shop_name not in shop_stats:
            shop_stats[shop_name] = {'created': 0, 'updated': 0}

        # 获取或创建 RobotGroup
        group, _ = RobotGroup.objects.get_or_create(
            key=shop_name,
            defaults={'name': shop_name, 'expected_total': 0}
        )

        # 获取机器人编号
        robot_id = safe_str(row.get('robot', ''))
        if not robot_id:
            skipped_no_robot += 1
            continue  # 跳过没有 robot_id 的行

        # 检查 RobotComponent 是否存在（通过 part_no 查找）
        existing = RobotComponent.objects.filter(part_no=robot_id).first()

        if existing:
            # 检查是否有高风险快照保护
            from .models import RobotHighRiskSnapshot
            snapshot = RobotHighRiskSnapshot.objects.filter(
                part_no=robot_id,
                is_active=True
            ).first()

            if snapshot:
                # 有快照保护，跳过更新，保持原有数据
                records_protected += 1
                continue

            # 更新现有记录
            existing.group = group
            existing.robot_id = robot_id
            existing.name = f"{safe_str(row.get('type', ''))} - {safe_str(row.get('tech', ''))}"
            existing.reference_no = safe_str(row.get('reference', ''))
            existing.number = safe_int(row.get('number', 0))
            existing.type_spec = safe_str(row.get('type', ''))
            existing.tech = safe_str(row.get('tech', ''))
            existing.mark = safe_int(row.get('mark', 0))
            existing.remark = safe_str(row.get('remark', ''))
            existing.level = safe_str(row.get('level', 'L'))
            # 详细数据字段
            existing.error1_c1 = safe_float(row.get('error1_c1'))
            existing.tem1_m = safe_float(row.get('tem1_m'))
            existing.tem2_m = safe_float(row.get('tem2_m'))
            existing.tem3_m = safe_float(row.get('tem3_m'))
            existing.tem4_m = safe_float(row.get('tem4_m'))
            existing.tem5_m = safe_float(row.get('tem5_m'))
            existing.tem6_m = safe_float(row.get('tem6_m'))
            existing.tem7_m = safe_float(row.get('tem7_m'))
            existing.a1_e_rate = safe_float(row.get('A1_e_rate'))
            existing.a2_e_rate = safe_float(row.get('A2_e_rate'))
            existing.a3_e_rate = safe_float(row.get('A3_e_rate'))
            existing.a4_e_rate = safe_float(row.get('A4_e_rate'))
            existing.a5_e_rate = safe_float(row.get('A5_e_rate'))
            existing.a6_e_rate = safe_float(row.get('A6_e_rate'))
            existing.a7_e_rate = safe_float(row.get('A7_e_rate'))
            existing.a1_rms = safe_float(row.get('A1_Rms'))
            existing.a2_rms = safe_float(row.get('A2_Rms'))
            existing.a3_rms = safe_float(row.get('A3_Rms'))
            existing.a4_rms = safe_float(row.get('A4_Rms'))
            existing.a5_rms = safe_float(row.get('A5_Rms'))
            existing.a6_rms = safe_float(row.get('A6_Rms'))
            existing.a7_rms = safe_float(row.get('A7_Rms'))
            existing.a1_e = safe_float(row.get('A1_E'))
            existing.a2_e = safe_float(row.get('A2_E'))
            existing.a3_e = safe_float(row.get('A3_E'))
            existing.a4_e = safe_float(row.get('A4_E'))
            existing.a5_e = safe_float(row.get('A5_E'))
            existing.a6_e = safe_float(row.get('A6_E'))
            existing.a7_e = safe_float(row.get('A7_E'))
            existing.q1 = safe_float(row.get('Q1'))
            existing.q2 = safe_float(row.get('Q2'))
            existing.q3 = safe_float(row.get('Q3'))
            existing.q4 = safe_float(row.get('Q4'))
            existing.q5 = safe_float(row.get('Q5'))
            existing.q6 = safe_float(row.get('Q6'))
            existing.q7 = safe_float(row.get('Q7'))
            existing.curr_a1_max = safe_float(row.get('Curr_A1_max'))
            existing.curr_a2_max = safe_float(row.get('Curr_A2_max'))
            existing.curr_a3_max = safe_float(row.get('Curr_A3_max'))
            existing.curr_a4_max = safe_float(row.get('Curr_A4_max'))
            existing.curr_a5_max = safe_float(row.get('Curr_A5_max'))
            existing.curr_a6_max = safe_float(row.get('Curr_A6_max'))
            existing.curr_a7_max = safe_float(row.get('Curr_A7_max'))
            existing.curr_a1_min = safe_float(row.get('Curr_A1_min'))
            existing.curr_a2_min = safe_float(row.get('Curr_A2_min'))
            existing.curr_a3_min = safe_float(row.get('Curr_A3_min'))
            existing.curr_a4_min = safe_float(row.get('Curr_A4_min'))
            existing.curr_a5_min = safe_float(row.get('Curr_A5_min'))
            existing.curr_a6_min = safe_float(row.get('Curr_A6_min'))
            existing.curr_a7_min = safe_float(row.get('Curr_A7_min'))
            existing.a1 = safe_float(row.get('A1'))
            existing.a2 = safe_float(row.get('A2'))
            existing.a3 = safe_float(row.get('A3'))
            existing.a4 = safe_float(row.get('A4'))
            existing.a5 = safe_float(row.get('A5'))
            existing.a6 = safe_float(row.get('A6'))
            existing.a7 = safe_float(row.get('A7'))
            existing.p_change = safe_float(row.get('P_Change'))
            existing.save(update_fields=[
                'group', 'robot_id', 'name', 'reference_no',
                'number', 'type_spec', 'tech', 'mark', 'remark', 'level',
                'error1_c1', 'tem1_m', 'tem2_m', 'tem3_m', 'tem4_m', 'tem5_m', 'tem6_m', 'tem7_m',
                'a1_e_rate', 'a2_e_rate', 'a3_e_rate', 'a4_e_rate', 'a5_e_rate', 'a6_e_rate', 'a7_e_rate',
                'a1_rms', 'a2_rms', 'a3_rms', 'a4_rms', 'a5_rms', 'a6_rms', 'a7_rms',
                'a1_e', 'a2_e', 'a3_e', 'a4_e', 'a5_e', 'a6_e', 'a7_e',
                'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7',
                'curr_a1_max', 'curr_a2_max', 'curr_a3_max', 'curr_a4_max', 'curr_a5_max', 'curr_a6_max', 'curr_a7_max',
                'curr_a1_min', 'curr_a2_min', 'curr_a3_min', 'curr_a4_min', 'curr_a5_min', 'curr_a6_min', 'curr_a7_min',
                'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
                'p_change',
            ])
            records_updated += 1
            shop_stats[shop_name]['updated'] += 1

            # 如果更新后的等级为 H，自动创建快照并添加到历史表
            if existing.level == 'H':
                create_high_risk_snapshot(existing, source_file, 'auto_sync')
                add_to_high_risk_history(existing, source_file, 'sync')
        else:
            # 创建新记录
            new_component = RobotComponent.objects.create(
                group=group,
                robot_id=robot_id,
                part_no=robot_id,
                name=f"{safe_str(row.get('type', ''))} - {safe_str(row.get('tech', ''))}",
                reference_no=safe_str(row.get('reference', '')),
                number=safe_int(row.get('number', 0)),
                type_spec=safe_str(row.get('type', '')),
                tech=safe_str(row.get('tech', '')),
                mark=safe_int(row.get('mark', 0)),
                remark=safe_str(row.get('remark', '')),
                level=safe_str(row.get('level', 'L')),
                # 详细数据字段
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
                a1=safe_float(row.get('A1')),
                a2=safe_float(row.get('A2')),
                a3=safe_float(row.get('A3')),
                a4=safe_float(row.get('A4')),
                a5=safe_float(row.get('A5')),
                a6=safe_float(row.get('A6')),
                a7=safe_float(row.get('A7')),
                p_change=safe_float(row.get('P_Change')),
            )
            records_created += 1
            shop_stats[shop_name]['created'] += 1

            # 如果新创建的等级为 H，自动创建快照并添加到历史表
            if new_component.level == 'H':
                create_high_risk_snapshot(new_component, source_file, 'auto_sync')
                add_to_high_risk_history(new_component, source_file, 'sync')

        # 每处理50行记录一次日志
        if (idx + 1) % 50 == 0:
            log_print(f"已处理 {idx + 1}/{total_rows} 行...")

    # 添加最终统计日志
    log_print("数据处理完成!")
    log_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log_print("统计结果:")
    log_print(f"  - 总处理行数: {total_rows}")
    log_print(f"  - 新增记录: {records_created} 条")
    log_print(f"  - 更新记录: {records_updated} 条")
    log_print(f"  - 保护记录(高风险): {records_protected} 条")
    log_print(f"  - 跳过记录(无机器人ID): {skipped_no_robot} 条")
    log_print(f"  - 有效记录: {records_created + records_updated} 条")
    log_print(" ")
    log_print("各车间统计:")
    for shop, stats in sorted(shop_stats.items()):
        log_print(f"  - {shop}: 新增 {stats['created']} 条, 更新 {stats['updated']} 条")
    log_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

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

    return {
        'success': True,
        'file': file_path,
        'source_file': source_file,
        'records_created': records_created,
        'records_updated': records_updated,
        'records_protected': records_protected,
        'total_records': records_created + records_updated,
        'shop_stats': shop_stats,
        'skipped_no_robot': skipped_no_robot,
        'total_rows': total_rows,
        'date': week_start.isoformat() if week_start else None,
    }


def sync_weeklyresult_to_robotcomponent() -> dict:
    """
    将 WeeklyResult 表的数据同步到 RobotComponent 表
    包含所有详细字段

    返回:
        同步结果统计
    """
    from .models import RobotComponent, RobotGroup, WeeklyResult

    log_print("开始从 WeeklyResult 同步数据到 RobotComponent...")

    wr_count = WeeklyResult.objects.count()
    if wr_count == 0:
        return {
            'success': False,
            'error': '没有可用的周结果数据，请先导入 CSV 文件'
        }

    synced_count = 0
    updated_count = 0
    shop_stats = {}

    # 同步所有 WeeklyResult 数据
    for wr in WeeklyResult.objects.all():
        shop_name = wr.shop or '(空)'

        # 统计各车间数量
        if shop_name not in shop_stats:
            shop_stats[shop_name] = {'created': 0, 'updated': 0}

        # 获取或创建 RobotGroup
        group, _ = RobotGroup.objects.get_or_create(
            key=shop_name,
            defaults={'name': shop_name, 'expected_total': 0}
        )

        # 检查 RobotComponent 是否存在
        existing = RobotComponent.objects.filter(part_no=wr.robot).first()

        if existing:
            # 检查是否有高风险快照保护
            from .models import RobotHighRiskSnapshot
            snapshot = RobotHighRiskSnapshot.objects.filter(
                part_no=wr.robot,
                is_active=True
            ).first()

            if snapshot:
                # 有快照保护，跳过更新
                continue

            # 更新现有记录（包含所有详细字段）
            existing.group = group
            existing.robot_id = wr.robot
            existing.name = f"{wr.type or ''} - {wr.tech or ''}"
            existing.reference_no = wr.reference or ''
            existing.number = int(wr.number) if wr.number else 0
            existing.type_spec = wr.type or ''
            existing.tech = wr.tech or ''
            existing.mark = wr.mark
            existing.remark = wr.remark or ''
            existing.level = wr.level or 'L'
            # 详细数据字段
            existing.error1_c1 = wr.error1_c1
            existing.tem1_m = wr.tem1_m
            existing.tem2_m = wr.tem2_m
            existing.tem3_m = wr.tem3_m
            existing.tem4_m = wr.tem4_m
            existing.tem5_m = wr.tem5_m
            existing.tem6_m = wr.tem6_m
            existing.tem7_m = wr.tem7_m
            existing.a1_e_rate = wr.a1_e_rate
            existing.a2_e_rate = wr.a2_e_rate
            existing.a3_e_rate = wr.a3_e_rate
            existing.a4_e_rate = wr.a4_e_rate
            existing.a5_e_rate = wr.a5_e_rate
            existing.a6_e_rate = wr.a6_e_rate
            existing.a7_e_rate = wr.a7_e_rate
            existing.a1_rms = wr.a1_rms
            existing.a2_rms = wr.a2_rms
            existing.a3_rms = wr.a3_rms
            existing.a4_rms = wr.a4_rms
            existing.a5_rms = wr.a5_rms
            existing.a6_rms = wr.a6_rms
            existing.a7_rms = wr.a7_rms
            existing.a1_e = wr.a1_e
            existing.a2_e = wr.a2_e
            existing.a3_e = wr.a3_e
            existing.a4_e = wr.a4_e
            existing.a5_e = wr.a5_e
            existing.a6_e = wr.a6_e
            existing.a7_e = wr.a7_e
            existing.q1 = wr.q1
            existing.q2 = wr.q2
            existing.q3 = wr.q3
            existing.q4 = wr.q4
            existing.q5 = wr.q5
            existing.q6 = wr.q6
            existing.q7 = wr.q7
            existing.curr_a1_max = wr.curr_a1_max
            existing.curr_a2_max = wr.curr_a2_max
            existing.curr_a3_max = wr.curr_a3_max
            existing.curr_a4_max = wr.curr_a4_max
            existing.curr_a5_max = wr.curr_a5_max
            existing.curr_a6_max = wr.curr_a6_max
            existing.curr_a7_max = wr.curr_a7_max
            existing.curr_a1_min = wr.curr_a1_min
            existing.curr_a2_min = wr.curr_a2_min
            existing.curr_a3_min = wr.curr_a3_min
            existing.curr_a4_min = wr.curr_a4_min
            existing.curr_a5_min = wr.curr_a5_min
            existing.curr_a6_min = wr.curr_a6_min
            existing.curr_a7_min = wr.curr_a7_min
            existing.a1 = wr.a1
            existing.a2 = wr.a2
            existing.a3 = wr.a3
            existing.a4 = wr.a4
            existing.a5 = wr.a5
            existing.a6 = wr.a6
            existing.a7 = wr.a7
            existing.p_change = wr.p_change
            existing.save(update_fields=[
                'group', 'robot_id', 'name', 'reference_no',
                'number', 'type_spec', 'tech', 'mark', 'remark', 'level',
                'error1_c1', 'tem1_m', 'tem2_m', 'tem3_m', 'tem4_m', 'tem5_m', 'tem6_m', 'tem7_m',
                'a1_e_rate', 'a2_e_rate', 'a3_e_rate', 'a4_e_rate', 'a5_e_rate', 'a6_e_rate', 'a7_e_rate',
                'a1_rms', 'a2_rms', 'a3_rms', 'a4_rms', 'a5_rms', 'a6_rms', 'a7_rms',
                'a1_e', 'a2_e', 'a3_e', 'a4_e', 'a5_e', 'a6_e', 'a7_e',
                'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7',
                'curr_a1_max', 'curr_a2_max', 'curr_a3_max', 'curr_a4_max', 'curr_a5_max', 'curr_a6_max', 'curr_a7_max',
                'curr_a1_min', 'curr_a2_min', 'curr_a3_min', 'curr_a4_min', 'curr_a5_min', 'curr_a6_min', 'curr_a7_min',
                'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
                'p_change',
            ])
            updated_count += 1
            shop_stats[shop_name]['updated'] += 1

            # 如果更新后的等级为 H，自动创建快照并添加到历史表
            if existing.level == 'H':
                create_high_risk_snapshot(existing, 'WeeklyResult同步', 'sync')
                add_to_high_risk_history(existing, 'WeeklyResult同步', 'sync')
        else:
            # 创建新记录（包含所有详细字段）
            new_component = RobotComponent.objects.create(
                group=group,
                robot_id=wr.robot,
                part_no=wr.robot,
                name=f"{wr.type or ''} - {wr.tech or ''}",
                reference_no=wr.reference or '',
                number=int(wr.number) if wr.number else 0,
                type_spec=wr.type or '',
                tech=wr.tech or '',
                mark=wr.mark,
                remark=wr.remark or '',
                level=wr.level or 'L',
                # 详细数据字段
                error1_c1=wr.error1_c1,
                tem1_m=wr.tem1_m,
                tem2_m=wr.tem2_m,
                tem3_m=wr.tem3_m,
                tem4_m=wr.tem4_m,
                tem5_m=wr.tem5_m,
                tem6_m=wr.tem6_m,
                tem7_m=wr.tem7_m,
                a1_e_rate=wr.a1_e_rate,
                a2_e_rate=wr.a2_e_rate,
                a3_e_rate=wr.a3_e_rate,
                a4_e_rate=wr.a4_e_rate,
                a5_e_rate=wr.a5_e_rate,
                a6_e_rate=wr.a6_e_rate,
                a7_e_rate=wr.a7_e_rate,
                a1_rms=wr.a1_rms,
                a2_rms=wr.a2_rms,
                a3_rms=wr.a3_rms,
                a4_rms=wr.a4_rms,
                a5_rms=wr.a5_rms,
                a6_rms=wr.a6_rms,
                a7_rms=wr.a7_rms,
                a1_e=wr.a1_e,
                a2_e=wr.a2_e,
                a3_e=wr.a3_e,
                a4_e=wr.a4_e,
                a5_e=wr.a5_e,
                a6_e=wr.a6_e,
                a7_e=wr.a7_e,
                q1=wr.q1,
                q2=wr.q2,
                q3=wr.q3,
                q4=wr.q4,
                q5=wr.q5,
                q6=wr.q6,
                q7=wr.q7,
                curr_a1_max=wr.curr_a1_max,
                curr_a2_max=wr.curr_a2_max,
                curr_a3_max=wr.curr_a3_max,
                curr_a4_max=wr.curr_a4_max,
                curr_a5_max=wr.curr_a5_max,
                curr_a6_max=wr.curr_a6_max,
                curr_a7_max=wr.curr_a7_max,
                curr_a1_min=wr.curr_a1_min,
                curr_a2_min=wr.curr_a2_min,
                curr_a3_min=wr.curr_a3_min,
                curr_a4_min=wr.curr_a4_min,
                curr_a5_min=wr.curr_a5_min,
                curr_a6_min=wr.curr_a6_min,
                curr_a7_min=wr.curr_a7_min,
                a1=wr.a1,
                a2=wr.a2,
                a3=wr.a3,
                a4=wr.a4,
                a5=wr.a5,
                a6=wr.a6,
                a7=wr.a7,
                p_change=wr.p_change,
            )
            synced_count += 1
            shop_stats[shop_name]['created'] += 1

            # 如果新创建的等级为 H，自动创建快照并添加到历史表
            if new_component.level == 'H':
                create_high_risk_snapshot(new_component, 'WeeklyResult同步', 'sync')
                add_to_high_risk_history(new_component, 'WeeklyResult同步', 'sync')

    # 记录同步时间
    from django.utils import timezone
    from .models import SystemConfig
    sync_time = timezone.now().isoformat()
    SystemConfig.set(
        'last_sync_time',
        sync_time,
        '最后同步机器人数据的时间'
    )

    log_print(f"同步完成！处理 {wr_count} 条 WeeklyResult 记录")
    log_print(f"  新增: {synced_count} 条")
    log_print(f"  更新: {updated_count} 条")

    return {
        'success': True,
        'total_processed': wr_count,
        'records_created': synced_count,
        'records_updated': updated_count,
        'shop_stats': shop_stats,
    }
