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


def import_robot_components_csv(
    file_path: str = None,
    folder_path: str = None,
    project: str = None,
    source: str = "manual"
) -> dict:
    """
    直接将 weeklyresult.csv 文件导入到 RobotComponent 表
    跳过 WeeklyResult 表，直接更新机器人状态界面数据

    真覆盖模式：CSV 中不存在的机器人数据将被删除

    参数:
        file_path: CSV 文件路径，如果为 None 则自动获取最新文件
        folder_path: 文件夹路径（用于自动查找）
        project: 项目名称（用于自动查找）
        source: 数据来源 ("manual" 手动同步 / "auto" 自动同步)

    返回:
        导入结果统计
    """
    from .models import RobotComponent, RobotGroup, RefreshLog

    # 步骤0：先归档上次的高风险数据（必须在导入新数据之前执行！）
    log_print("开始归档上次的高风险数据...")
    archive_result = archive_high_risk_robots()
    if archive_result.get('archived_count', 0) > 0:
        log_print(f"已归档 {archive_result['archived_count']} 条高风险数据到历史快照表")

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
    csv_robots = set()  # 记录 CSV 中所有的 robot 值，用于删除旧数据

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
        robot_val = safe_str(row.get('robot', ''))
        if not robot_val:
            skipped_no_robot += 1
            continue  # 跳过没有 robot 的行

        # 记录 CSV 中所有的 robot 值，用于后续删除旧数据
        csv_robots.add(robot_val)

        # 检查 RobotComponent 是否存在（通过 robot 查找）
        existing = RobotComponent.objects.filter(robot=robot_val).first()

        if existing:
            # 更新现有记录（不再使用快照保护机制，快照表只用于历史记录）
            existing.group = group
            existing.robot = robot_val
            existing.shop = shop_name  # 修复：更新 shop 字段
            existing.reference = safe_str(row.get('reference', ''))
            existing.number = safe_int(row.get('number', 0))
            existing.type = safe_str(row.get('type', ''))
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
            existing.a1 = safe_str(row.get('A1'))
            existing.a2 = safe_str(row.get('A2'))
            existing.a3 = safe_str(row.get('A3'))
            existing.a4 = safe_str(row.get('A4'))
            existing.a5 = safe_str(row.get('A5'))
            existing.a6 = safe_str(row.get('A6'))
            existing.a7 = safe_str(row.get('A7'))
            existing.p_change = safe_float(row.get('P_Change'))
            existing.save(update_fields=[
                'group', 'robot', 'shop', 'reference',  # 修复：添加 'shop' 字段
                'number', 'type', 'tech', 'mark', 'remark', 'level',
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

            # 注意：不再立即创建快照，快照将在下次同步时创建
        else:
            # 创建新记录
            new_component = RobotComponent.objects.create(
                group=group,
                robot=robot_val,
                shop=shop_name,  # 修复：创建时设置 shop 字段
                reference=safe_str(row.get('reference', '')),
                number=safe_int(row.get('number', 0)),
                type=safe_str(row.get('type', '')),
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
                a1=safe_str(row.get('A1')),
                a2=safe_str(row.get('A2')),
                a3=safe_str(row.get('A3')),
                a4=safe_str(row.get('A4')),
                a5=safe_str(row.get('A5')),
                a6=safe_str(row.get('A6')),
                a7=safe_str(row.get('A7')),
                p_change=safe_float(row.get('P_Change')),
            )
            records_created += 1
            shop_stats[shop_name]['created'] += 1

            # 注意：不再立即创建快照，快照将在下次同步时创建

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

    # 真覆盖模式：删除 CSV 中不存在的机器人数据
    deleted_count = 0
    if csv_robots:
        deleted_count = RobotComponent.objects.exclude(robot__in=csv_robots).delete()[0]
        if deleted_count > 0:
            log_print(f"已删除 {deleted_count} 条 CSV 中不存在的旧数据（真覆盖模式）")
    else:
        log_print("警告：CSV 中没有有效的 robot 数据，不执行删除操作")

    # 记录当前的高风险机器人列表，供下次同步时归档使用
    save_current_high_risk_robots()

    # 写入刷新日志
    RefreshLog.objects.create(
        source=source,
        trigger="scheduled" if source == "auto" else "manual",
        status="success",
        source_file=source_file,
        file_date=week_start,
        records_created=records_created,
        records_updated=records_updated,
        records_deleted=deleted_count,
        total_records=records_created + records_updated,
    )
    log_print(f"已记录刷新日志: {source} 同步完成")

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
