"""
Bokeh图表生成模块 - 静态嵌入Django使用
支持前端控件联动（程序切换、轴切换）
"""
import json
import logging
import re
import time
import uuid
from datetime import datetime, timedelta

import pandas as pd
from bokeh.embed import components
from bokeh.events import ButtonClick
from bokeh.models import (
    ColumnDataSource, HoverTool, Select,
    CustomJS, LabelSet, BoxAnnotation, Band, DatePicker, Range1d
)
from bokeh.plotting import figure
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

DEFAULT_RANGE_DAYS = 30
CACHE_TTL_SECONDS = 600
CACHE_VERSION = 2
_LOCAL_DF_CACHE: dict[str, tuple[float, "pd.DataFrame"]] = {}

# Program 切换内存缓存：{cache_key: (df_full, energy_full, timestamp, table_name, time_range)}
# 用于快速切换 program，避免重新查询数据库
_PROGRAM_DATA_CACHE: dict[str, tuple] = {}

try:
    from django.core.cache import cache
except Exception:  # pragma: no cover - optional when running outside Django
    cache = None


def _local_df_cache_get(key: str):
    item = _LOCAL_DF_CACHE.get(key)
    if not item:
        return None
    expires_at, df = item
    if expires_at <= time.time():
        _LOCAL_DF_CACHE.pop(key, None)
        return None
    return df


def _local_df_cache_set(key: str, df: "pd.DataFrame", ttl_seconds: int):
    try:
        _LOCAL_DF_CACHE[key] = (time.time() + int(ttl_seconds), df)
    except Exception:
        return


# Program 数据缓存管理（用于快速切换 program）
def _program_data_cache_key(table_name: str, start_date: str, end_date: str) -> str:
    """生成 program 数据缓存键"""
    return f"program_data:{table_name}:{start_date}:{end_date}"


def _program_data_cache_get(table_name: str, start_date: str, end_date: str):
    """从缓存获取 program 数据"""
    key = _program_data_cache_key(table_name, start_date, end_date)
    item = _PROGRAM_DATA_CACHE.get(key)
    if not item:
        return None
    timestamp, df_full, energy_full = item
    # 检查是否过期（10分钟）
    if time.time() - timestamp > 600:
        _PROGRAM_DATA_CACHE.pop(key, None)
        return None
    return df_full, energy_full


def _program_data_cache_set(table_name: str, start_date: str, end_date: str, df_full, energy_full):
    """缓存 program 数据"""
    key = _program_data_cache_key(table_name, start_date, end_date)
    _PROGRAM_DATA_CACHE[key] = (time.time(), df_full, energy_full)


def _program_data_cache_clear():
    """清空 program 数据缓存"""
    _PROGRAM_DATA_CACHE.clear()

# 轴配置 - A1到A7
_TABLE_NAME_CACHE = {}  # 表名缓存 {lower_name: real_name}
AXIS_CONFIG = {
    'A1': {'curr': 'Curr_A1', 'max_curr': 'MAXCurr_A1', 'min_curr': 'MinCurr_A1', 'torque': 'Torque1', 'speed': 'Speed1', 'fol': 'Fol1', 'axisp': 'AxisP1'},
    'A2': {'curr': 'Curr_A2', 'max_curr': 'MAXCurr_A2', 'min_curr': 'MinCurr_A2', 'torque': 'Torque2', 'speed': 'Speed2', 'fol': 'Fol2', 'axisp': 'AxisP2'},
    'A3': {'curr': 'Curr_A3', 'max_curr': 'MAXCurr_A3', 'min_curr': 'MinCurr_A3', 'torque': 'Torque3', 'speed': 'Speed3', 'fol': 'Fol3', 'axisp': 'AxisP3'},
    'A4': {'curr': 'Curr_A4', 'max_curr': 'MAXCurr_A4', 'min_curr': 'MinCurr_A4', 'torque': 'Torque4', 'speed': 'Speed4', 'fol': 'Fol4', 'axisp': 'AxisP4'},
    'A5': {'curr': 'Curr_A5', 'max_curr': 'MAXCurr_A5', 'min_curr': 'MinCurr_A5', 'torque': 'Torque5', 'speed': 'Speed5', 'fol': 'Fol5', 'axisp': 'AxisP5'},
    'A6': {'curr': 'Curr_A6', 'max_curr': 'MAXCurr_A6', 'min_curr': 'MinCurr_A6', 'torque': 'Torque6', 'speed': 'Speed6', 'fol': 'Fol6', 'axisp': 'AxisP6'},
    'A7': {'curr': 'Curr_E1', 'max_curr': 'MAXCurr_E1', 'min_curr': 'MinCurr_E1', 'torque': 'Torque7', 'speed': 'Speed7', 'fol': 'Fol7', 'axisp': 'AxisP7'},
}


def get_db_engine():
    """获取PROGRAM CYCLE SYNC数据库连接（仅使用SG_DB_*）"""
    import os

    sg_name = os.getenv('SG_DB_NAME')
    sg_user = os.getenv('SG_DB_USER')
    sg_password = os.getenv('SG_DB_PASSWORD')
    sg_host = os.getenv('SG_DB_HOST')
    sg_port = os.getenv('SG_DB_PORT')

    missing = [key for key, value in [
        ("SG_DB_NAME", sg_name),
        ("SG_DB_USER", sg_user),
        ("SG_DB_PASSWORD", sg_password),
        ("SG_DB_HOST", sg_host),
        ("SG_DB_PORT", sg_port),
    ] if not value]
    if missing:
        raise ValueError(f"Missing PROGRAM CYCLE SYNC DB env vars: {', '.join(missing)}")

    return {
        'user': sg_user,
        'password': sg_password,
        'host': sg_host,
        'port': sg_port or '3306',
        'database': sg_name,
    }


def get_real_table_name(table_name, engine):
    """获取数据库中实际的表名（不区分大小写匹配）"""
    import os
    from sqlalchemy import text

    lower_name = table_name.lower()

    # 检查缓存
    if lower_name in _TABLE_NAME_CACHE:
        return _TABLE_NAME_CACHE[lower_name]

    sg_db_name = os.getenv('SG_DB_NAME')
    if not sg_db_name:
        _TABLE_NAME_CACHE[lower_name] = table_name
        return table_name

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name "
                    "FROM information_schema.tables "
                    "WHERE table_schema = :schema "
                    "AND LOWER(table_name) = LOWER(:name) "
                    "LIMIT 1"
                ),
                {"schema": sg_db_name, "name": table_name}
            ).fetchone()

            if result and result[0]:
                real_name = result[0]
                if real_name != table_name:
                    logger.debug("表名自动修正: %s -> %s", table_name, real_name)
                _TABLE_NAME_CACHE[lower_name] = real_name
                return real_name
    except Exception as e:
        logger.warning(f"查找表名失败: {e}")

    _TABLE_NAME_CACHE[lower_name] = table_name
    return table_name


def get_table_recent_range(table_name, engine, days=DEFAULT_RANGE_DAYS):
    """获取数据库表最近时间范围（仅取MAX，避免全量MIN/MAX扫描）

    注意：这是“最近窗口”而不是表的真实最早/最晚时间范围。
    如果前端显式传入 start/end，请使用 get_table_time_bounds() 取得真实边界。
    """
    # 自动修正表名大小写
    real_table_name = get_real_table_name(table_name, engine)
    query = f"SELECT MAX(`Timestamp`) as max_time FROM `{real_table_name}`;"
    try:
        df = pd.read_sql(query, engine)
        if df.empty or df['max_time'].isna()[0]:
            end_time = datetime.now()
        else:
            end_time = df['max_time'][0]
        start_time = end_time - timedelta(days=days)
        return start_time, end_time
    except Exception as e:
        logger.error(f"获取时间范围失败: {e}")
        end_time = datetime.now()
        return end_time - timedelta(days=days), end_time


def get_table_time_bounds(table_name, engine, time_column: str = "Timestamp"):
    """获取数据库表真实时间边界 (MIN/MAX)。

    优先用 ORDER BY ... LIMIT 1（通常可走索引）来避免 MIN/MAX 的全表扫描风险。
    失败时回退到 MIN/MAX 聚合。
    """
    real_table_name = get_real_table_name(table_name, engine)
    from sqlalchemy import text

    def _fetch_one(sql: str):
        df = pd.read_sql(text(sql), engine)
        if df.empty:
            return None
        value = df.iloc[0, 0]
        return None if pd.isna(value) else value

    try:
        min_sql = (
            f"SELECT `{time_column}` "
            f"FROM `{real_table_name}` "
            f"WHERE `{time_column}` IS NOT NULL "
            f"ORDER BY `{time_column}` ASC "
            f"LIMIT 1;"
        )
        max_sql = (
            f"SELECT `{time_column}` "
            f"FROM `{real_table_name}` "
            f"WHERE `{time_column}` IS NOT NULL "
            f"ORDER BY `{time_column}` DESC "
            f"LIMIT 1;"
        )
        start_time = _fetch_one(min_sql)
        end_time = _fetch_one(max_sql)
        if start_time is None or end_time is None:
            raise ValueError("empty bounds")
        return start_time, end_time
    except Exception as e:
        logger.warning("ORDER BY 取边界失败，回退 MIN/MAX: %s", e)
        try:
            bounds_sql = (
                f"SELECT MIN(`{time_column}`) AS min_time, MAX(`{time_column}`) AS max_time "
                f"FROM `{real_table_name}`;"
            )
            df = pd.read_sql(text(bounds_sql), engine)
            if df.empty or df["min_time"].isna()[0] or df["max_time"].isna()[0]:
                now = datetime.now()
                return now, now
            return df["min_time"][0], df["max_time"][0]
        except Exception as e2:
            logger.error("获取真实时间边界失败: %s", e2)
            now = datetime.now()
            return now, now


def fetch_data_from_mysql(table_name, start_time, end_time, time_column, engine):
    """从MySQL获取数据 - 优化版本：直接使用表名，仅在必要时查询真实表名"""
    # 直接使用传入的表名（前端现在传入正确大小写）
    # 仅当表名全为小写时才查询真实表名（向后兼容）
    real_table_name = table_name
    if table_name == table_name.lower():
        # 只有当表名全小写时才查询（容错机制）
        real_table_name = get_real_table_name(table_name, engine)

    columns = None
    program = None
    if isinstance(time_column, dict):
        # Backward-compatible shim if older call sites pass a dict of options.
        options = time_column
        time_column = options.get("time_column", "Timestamp")
        columns = options.get("columns")
        program = options.get("program")

    select_cols = "*"
    if columns:
        safe_cols = [str(c) for c in columns if c]
        select_cols = ", ".join(f"`{c.replace('`', '')}`" for c in safe_cols)

    # 与 Digitaltwin_timefree.py 一致：使用字符串拼接，不在 SQL 层过滤 program
    base_sql = (
        f"SELECT {select_cols} "
        f"FROM `{real_table_name}` "
        f"WHERE `{time_column}` BETWEEN '{start_time}' AND '{end_time}';"
    )

    try:
        # 一次性读取数据，与 Digitaltwin_timefree.py 保持一致
        logger.info(
            "执行查询: table=%s, time_col=%s, cols=%s, range=%s..%s",
            real_table_name,
            time_column,
            "ALL" if select_cols == "*" else len(columns),
            start_time,
            end_time,
        )
        # 直接使用字符串 SQL，与 Digitaltwin_timefree.py 一致
        df = pd.read_sql(base_sql, engine)
        logger.debug("查询完成，共 %s 行", len(df))
        return df
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        return pd.DataFrame()


def _preprocess_bi_dataframe(df: "pd.DataFrame") -> "pd.DataFrame":
    """数据预处理 - 完全采用 Digitaltwin_timefree.py 的方式"""
    if df is None or df.empty:
        return pd.DataFrame()

    # 与 Digitaltwin_timefree.py 完全一致：直接操作，不检查
    del df['A1_marker'], df['A2_marker'], df['A3_marker'], df['A4_marker'], \
        df['A5_marker'], df['A6_marker'], df['A7_marker'], df['SUB']

    df = df.drop_duplicates()

    df['Time'] = pd.to_datetime(df['Timestamp']) + timedelta(hours=8)
    df['Timestamp'] = df['Time'].astype(str)

    df['SNR_C'] = df['SNR_C'].astype(int)

    # 与 Digitaltwin_timefree.py 完全一致：直接转换，不循环检查
    df['AxisP1'] = df['AxisP1'].astype(float)
    df['AxisP2'] = df['AxisP2'].astype(float)
    df['AxisP3'] = df['AxisP3'].astype(float)
    df['AxisP4'] = df['AxisP4'].astype(float)
    df['AxisP5'] = df['AxisP5'].astype(float)
    df['AxisP6'] = df['AxisP6'].astype(float)
    df['AxisP7'] = df['AxisP7'].astype(float)

    return df


def _coerce_datetime(value):
    if not value:
        return None
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None


def _is_date_only(value):
    if not isinstance(value, str):
        return False
    return re.match(r'^\d{4}-\d{2}-\d{2}$', value) is not None


def _normalize_date_bounds(start_value, end_value):
    start_dt = _coerce_datetime(start_value)
    end_dt = _coerce_datetime(end_value)
    if not start_dt or not end_dt:
        return start_dt, end_dt
    if _is_date_only(start_value):
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if _is_date_only(end_value):
        end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_dt, end_dt


def _format_datetime(value):
    if not value:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


def create_bi_charts(
    table_name='as33_020rb_400',
    days=None,
    axis='A1',
    program=None,
    start_date=None,
    end_date=None,
):
    """创建BI可视化图表 - 首屏只计算默认 program，切换 program 触发重载再算。"""

    # 从Django配置获取数据库连接参数
    db_config = get_db_engine()
    user = db_config['user']
    password = db_config['password']
    host = db_config['host']
    port = db_config['port']
    database = db_config['database']
    time_column = 'Timestamp'

    # 创建数据库连接
    try:
        engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')
        logger.info(f"数据库连接: {host}:{port}/{database}")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None, None, None, None, None

    # 直接使用传入的表名，不再查询真实表名
    # table_name 保持原样

    # 直接使用传入的时间范围，与 Digitaltwin_timefree.py 保持一致
    requested_start, requested_end = _normalize_date_bounds(start_date, end_date)
    if requested_start and requested_end:
        if requested_start > requested_end:
            requested_start, requested_end = requested_end, requested_start
        start_time = requested_start
        end_time = requested_end
    else:
        # 默认使用最近 7 天，与 Digitaltwin_timefree.py 保持一致
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

    logger.info("请求时间范围: %s 到 %s", start_time, end_time)

    # 与 Digitaltwin_timefree.py 一致：先查全量数据，再在 Python 中过滤
    logger.info("开始从数据库获取全量数据...")
    fetch_start = time.perf_counter()

    # 构建需要的列（与 Digitaltwin_timefree.py 一致，使用 SELECT *）
    df_full = fetch_data_from_mysql(
        table_name,
        _format_datetime(start_time),
        _format_datetime(end_time),
        time_column,  # 传递字符串，不使用 dict
        engine,
    )
    logger.info("全量数据: db fetch %.3fs, 行数=%s", time.perf_counter() - fetch_start, len(df_full))

    if df_full.empty:
        logger.warning("表 %s 在所选时间范围内没有数据", table_name)
        return None, None, None, None, None

    # 数据预处理
    preprocess_start = time.perf_counter()
    df_full = _preprocess_bi_dataframe(df_full)
    logger.info("数据预处理: %.3fs", time.perf_counter() - preprocess_start)

    # 缓存全量数据（用于快速切换 program）
    start_date_str = start_time.strftime('%Y-%m-%d')
    end_date_str = end_time.strftime('%Y-%m-%d')
    _program_data_cache_set(table_name, start_date_str, end_date_str, df_full, None)
    logger.info("数据已缓存到内存，用于快速切换 program")

    # 在 Python 中获取 program 列表和过滤数据（与 Digitaltwin_timefree.py 一致）
    c_opt = df_full['Name_C'].unique()
    logger.info("可用程序列表: %s", len(c_opt))

    if not c_opt:
        logger.warning("没有 program 数据")
        return None, None, None, None, None

    # 确定默认 program / axis（与 Digitaltwin_timefree.py 一致）
    default_program = program if program and program in c_opt else c_opt[0]
    default_axis = axis if axis in AXIS_CONFIG else "A1"

    # 在 Python 中过滤 program（与 Digitaltwin_timefree.py 一致）
    # 直接过滤，不复制（避免大数据复制开销）
    df_prog = df_full[df_full['Name_C'] == default_program]
    logger.info("程序 %s 数据条数: %s", default_program, len(df_prog))

    if df_prog is None or df_prog.empty:
        logger.warning("表 %s program=%s 没有数据", table_name, default_program)
        return None, None, None, None, None
    logger.info("加载数据条数: %s, 列数=%s (program=%s)", len(df_prog), len(df_prog.columns), default_program)

    # 获取能量数据
    energy_cache_key = (
        f"bi:energy:{CACHE_VERSION}:{table_name}:"
        f"{start_time.strftime('%Y%m%d%H%M%S')}:{end_time.strftime('%Y%m%d%H%M%S')}"
    )
    energy_cached = cache.get(energy_cache_key) if cache else None
    if energy_cached is not None:
        # 缓存命中，直接使用（与 Digitaltwin_timefree.py 保持一致）
        energy_full = energy_cached
        logger.info("能量数据: cache hit")
    else:
        energy_query = (
            "SELECT TimeStamp2,ENERGY,LOSTENERGY FROM energy "
            f"WHERE LOWER(RobotName)= LOWER('{table_name}') "
            f"AND TimeStamp2 BETWEEN '{_format_datetime(start_time)}' "
            f"AND '{_format_datetime(end_time)}'"
        )
        try:
            energy_fetch_start = time.perf_counter()
            energy_full = pd.read_sql(energy_query, engine)
            logger.info("能量数据: db fetch %.3fs", time.perf_counter() - energy_fetch_start)
            logger.info(f"能量数据条数: {len(energy_full)}")
        except Exception as e:
            logger.warning(f"能量数据获取失败: {e}")
            energy_full = pd.DataFrame()
        if cache:
            # 直接存储，不 copy（与 Digitaltwin_timefree.py 保持一致）
            cache.set(energy_cache_key, energy_full, timeout=CACHE_TTL_SECONDS)

    # df_full 已经做过统一预处理，这里无需重复处理

    # 能量数据处理
    if not energy_full.empty:
        energy_full['TimeStamp2'] = pd.to_datetime(energy_full['TimeStamp2']) + timedelta(hours=8)
        energy_full['ENERGY'] = energy_full['ENERGY'].astype(float)
        energy_full['LOSTENERGY'] = energy_full['LOSTENERGY'].astype(float)
        energy_full = energy_full.sort_values(by='TimeStamp2', ascending=True)

    # 更新缓存（包含 energy 数据）
    _program_data_cache_set(table_name, start_date_str, end_date_str, df_full, energy_full)
    logger.info("缓存已更新（包含 energy 数据）")

    # ============ 仅为默认 program 计算数据（program 切换时重载页面再算） ============
    agg_start = time.perf_counter()
    prog_data = df_prog  # 直接使用，不复制（与 Digitaltwin_timefree.py 一致）
    prog_data = prog_data.sort_values(by=["SNR_C", "Time"])
    prog_data["sort"] = range(1, len(prog_data) + 1)

    # 聚合数据（与 Digitaltwin_timefree.py 完全一致：直接写死列名）
    ref = prog_data.groupby("SNR_C")[['MAXCurr_A1','MAXCurr_A2','MAXCurr_A3','MAXCurr_A4',
                                      'MAXCurr_A5','MAXCurr_A6','MAXCurr_E1',
                                      'MinCurr_A1','MinCurr_A2','MinCurr_A3','MinCurr_A4',
                                      'MinCurr_A5','MinCurr_A6','MinCurr_E1']].last()

    LQ = prog_data.groupby("SNR_C")[['Curr_A1','Curr_A2','Curr_A3','Curr_A4',
                                          'Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.01, interpolation='nearest').rename(
        columns={'Curr_A1': 'Curr_A1_LQ', 'Curr_A2': 'Curr_A2_LQ', 'Curr_A3': 'Curr_A3_LQ',
                 'Curr_A4': 'Curr_A4_LQ', 'Curr_A5': 'Curr_A5_LQ', 'Curr_A6': 'Curr_A6_LQ',
                 'Curr_E1': 'Curr_E1_LQ'})
    HQ = prog_data.groupby("SNR_C")[['Curr_A1','Curr_A2','Curr_A3','Curr_A4',
                                          'Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.99, interpolation='nearest').rename(
        columns={'Curr_A1': 'Curr_A1_HQ', 'Curr_A2': 'Curr_A2_HQ', 'Curr_A3': 'Curr_A3_HQ',
                 'Curr_A4': 'Curr_A4_HQ', 'Curr_A5': 'Curr_A5_HQ', 'Curr_A6': 'Curr_A6_HQ',
                 'Curr_E1': 'Curr_E1_HQ'})
    labeltext = prog_data.groupby("SNR_C")["P_name"].last()

    # 使用 Digitaltwin_timefree.py 的 merge 方式
    Q = pd.merge(pd.merge(pd.merge(LQ, HQ, left_on=['SNR_C'], right_index=True, how='outer'),
                          ref, left_on=['SNR_C'], right_index=True, how='inner'),
                 labeltext, left_on=['SNR_C'], right_index=True, how='inner').reset_index()

    # 生成 x_tex（与 Digitaltwin_timefree.py 一致）
    x_tex = prog_data["SNR_C"].sort_values(ascending=True).unique().astype(str)
    Q["SNR_C"] = x_tex

    source = ColumnDataSource(prog_data)
    agg_source = ColumnDataSource(Q)
    logger.info("程序数据聚合: %.3fs (program=%s)", time.perf_counter() - agg_start, default_program)

    # 能量数据源
    energy_source = ColumnDataSource(energy_full) if not energy_full.empty else ColumnDataSource(pd.DataFrame())

    # ============ 创建控件 ============
    from bokeh.models import Div, Spacer

    # 创建标签 Div（与下拉框在同一行）
    program_label = Div(text="<span style='font-size: 12px; font-weight: bold;'>program_name:</span>")
    axis_label = Div(text="<span style='font-size: 12px; font-weight: bold;'>Axis select:</span>")

    program_select = Select(
        title="",  # 空标题，标签单独显示
        value=default_program,
        options=c_opt,  # 使用 c_opt 替代 programs
        width=260,
        min_width=220,
        sizing_mode="stretch_width"
    )
    program_select.name = "program_select"

    axis_select = Select(
        title="",  # 空标题，标签单独显示
        value=default_axis,
        options=list(AXIS_CONFIG.keys()),
        width=180,
        min_width=140,
        sizing_mode="stretch_width"
    )
    axis_select.name = "axis_select"

    # ============ 创建图表 ============
    chart_create_start = time.perf_counter()
    # 创建代理数据源，使用固定的列名，这样渲染器不需要修改列引用
    # 当切换轴或程序时，我们只需要更新这些代理列的数据

    # 从默认轴和程序获取初始数据
    default_config = AXIS_CONFIG[default_axis]
    default_source_data = source.data
    default_agg_data = agg_source.data

    # 创建代理数据源 - 使用固定的列名
    # 时间序列图表使用固定列名
    proxy_source = ColumnDataSource(data={
        'sort': default_source_data.get('sort', []),
        'Timestamp': default_source_data.get('Timestamp', []),
        'SNR_C': default_source_data.get('SNR_C', []),
        'P_name': default_source_data.get('P_name', []),
        'Time': default_source_data.get('Time', []),
        'Tem_1': default_source_data.get('Tem_1', []),
        # 使用固定列名，初始值为默认轴的数据
        'curr_value': default_source_data.get(default_config['curr'], []),
        'max_curr_value': default_source_data.get(default_config['max_curr'], []),
        'min_curr_value': default_source_data.get(default_config['min_curr'], []),
        'torque_value': default_source_data.get(default_config['torque'], []),
        'speed_value': default_source_data.get(default_config['speed'], []),
        'fol_value': default_source_data.get(default_config['fol'], []),
        'axisp_value': default_source_data.get(default_config['axisp'], []),
    })

    # 聚合图表也使用固定列名
    # 找到对应的_LQ和_HQ列名（例如 Curr_A1_LQ, Curr_A1_HQ）
    curr_col = default_config['curr']
    lq_col = f'{curr_col}_LQ'
    hq_col = f'{curr_col}_HQ'

    proxy_agg_source = ColumnDataSource(data={
        'SNR_C': default_agg_data.get('SNR_C', []),
        'P_name': default_agg_data.get('P_name', []),
        'max_curr_value': default_agg_data.get(default_config['max_curr'], []),
        'min_curr_value': default_agg_data.get(default_config['min_curr'], []),
        'lq_value': default_agg_data.get(lq_col, []),
        'hq_value': default_agg_data.get(hq_col, []),
    })

    # 获取默认轴和程序的配置
    max_curr_col = default_config['max_curr']
    min_curr_col = default_config['min_curr']
    torque_col = default_config['torque']
    speed_col = default_config['speed']
    fol_col = default_config['fol']
    axisp_col = default_config['axisp']

    # Hover工具定义 - 使用动态列名显示
    hover = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Current', '@curr_value'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover_temp = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Tem_1', '@Tem_1'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover_torque = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Torque', '@torque_value'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover_fol = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Following Error', '@fol_value'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover_speed = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Speed', '@speed_value'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover_axisp = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Position', '@axisp_value'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    # 创建图表 - 使用固定的代理列名
    # 创建共享的y_range，让聚合分析和电流分析图联动
    #shared_y_range = Range1d(start=0, end=100, bounds='auto')

    p_curr = figure(
        title=f'{default_axis} - Current Analysis',
        sizing_mode="stretch_width",
        width=2100,
        height=220,
        x_axis_label='Motion Time',
        y_axis_label='Current %',
       #y_range=shared_y_range,
        tools=[hover, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10),
        output_backend='webgl'
    )
    p_curr.step(x='sort', y='min_curr_value', source=proxy_source, line_width=2, mode="center", color='red', legend_label='Min Current')
    p_curr.step(x='sort', y='max_curr_value', source=proxy_source, line_width=2, mode="center", color='red', legend_label='Max Current')
    p_curr.scatter(x='sort', y='curr_value', source=proxy_source, size=2, alpha=0.6, color='navy', legend_label='Real-time Current')
    p_curr.legend.location = 'top_right'
    p_curr.legend.click_policy = "hide"
    p_curr.xaxis.visible = False

    p_temp = figure(
        x_range=p_curr.x_range,
        y_range=(15, 100),
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='Motion Time',
        y_axis_label='Temperature (°C)',
        tools=[hover_temp, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10),
        output_backend='webgl'
    )
    p_temp.scatter(x='sort', y='Tem_1', source=proxy_source, size=2, color='orange', legend_label='Temperature')
    p_temp.legend.location = 'top_right'
    p_temp.legend.click_policy = "hide"
    p_temp.xaxis.visible = False

    p_pos = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='Motion Time',
        y_axis_label='Axis Position',
        tools=[hover_axisp, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10),
        output_backend='webgl'
    )
    p_pos.scatter(x='sort', y='axisp_value', source=proxy_source, size=2, color='green', legend_label='Position')
    p_pos.legend.location = 'top_right'
    p_pos.legend.click_policy = "hide"
    p_pos.xaxis.visible = False

    p_speed = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='Motion Time',
        y_axis_label='Motor Speed',
        tools=[hover_speed, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10),
        output_backend='webgl'
    )
    p_speed.scatter(x='sort', y='speed_value', source=proxy_source, size=2, color='blue', legend_label='Speed')
    p_speed.legend.location = 'top_right'
    p_speed.legend.click_policy = "hide"
    p_speed.xaxis.visible = False

    p_fol = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='Motion Time',
        y_axis_label='Following Error',
        tools=[hover_fol, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10),
        output_backend='webgl'
    )
    p_fol.scatter(x='sort', y='fol_value', source=proxy_source, size=2, color='lime', legend_label='Following Error')
    p_fol.legend.location = 'top_right'
    p_fol.legend.click_policy = "hide"
    p_fol.xaxis.visible = False

    p_torque = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='Motion Time',
        y_axis_label='Torque',
        tools=[hover_torque, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10),
        output_backend='webgl'
    )
    p_torque.scatter(x='sort', y='torque_value', source=proxy_source, size=2, color='sienna', legend_label='Torque')
    p_torque.legend.location = 'top_right'
    p_torque.legend.click_policy = "hide"
    p_torque.xaxis.visible = False

    # 聚合分析图 - 使用代理数据源和固定列名
    # 使用与电流分析图共享的y_range，实现纵轴联动
    line_plot = figure(
        title=f"Aggregate Analysis - {default_program}",
        sizing_mode="stretch_width",
        width=2100,
        height=280,
        x_range=x_tex,
        y_range=p_curr.y_range,
        tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=40,
        margin=(5, 10, 5, 10),
        output_backend='webgl'
    )

    hover_line = HoverTool(
        tooltips=[
            ("SNR_C", "@SNR_C"),
            ("P_name", "@P_name"),
            ("1% Quantile", "@lq_value"),
            ("99% Quantile", "@hq_value"),
        ]
    )
    line_plot.add_tools(hover_line)

    line_plot.line(x="SNR_C", y="lq_value", source=proxy_agg_source, line_color="blue",
                    line_width=2, legend_label="1% Quantile", alpha=1)
    line_plot.line(x="SNR_C", y="hq_value", source=proxy_agg_source, line_color="orange",
                    line_width=2, legend_label="99% Quantile", alpha=1)
    l1 = Band(base="SNR_C", lower="min_curr_value", upper="max_curr_value", source=proxy_agg_source,
              fill_alpha=0.3, fill_color="green", line_color="red")
    line_plot.add_layout(l1)

    label_setmax = LabelSet(x="SNR_C", y="hq_value", text='P_name', level='glyph',
                            x_offset=3, y_offset=3, source=proxy_agg_source,
                            text_font_size='7pt', angle=0, text_font_style='bold')
    line_plot.add_layout(label_setmax)

    low_box = BoxAnnotation(top=-90, fill_alpha=0.2, fill_color='#D55E00')
    high_box = BoxAnnotation(bottom=90, fill_alpha=0.2, fill_color='#D55E00')
    line_plot.add_layout(low_box)
    line_plot.add_layout(high_box)

    line_plot.legend.location = 'bottom'
    line_plot.legend.orientation = 'horizontal'
    line_plot.legend.label_text_font_size = '8pt'
    line_plot.xaxis.major_label_orientation = 1.5
    line_plot.legend.click_policy = "hide"

    # 能量图
    EnergyP = None
    if not energy_full.empty:
        EnergyP = figure(
            x_axis_type="datetime",
            title='Energy Analysis',
            sizing_mode="stretch_width",
            width=280,
            height=300,
            x_axis_label='Time',
            y_axis_label='Energy',
            tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
            min_border_left=40,
            min_border_right=10,
            min_border_top=20,
            min_border_bottom=40,
            output_backend='webgl'
        )
        EnergyP.line(x="TimeStamp2", y="ENERGY", source=energy_source,
                     line_color="orange", line_width=2, legend_label="Energy Consumption", alpha=1)
        EnergyP.line(x="TimeStamp2", y="LOSTENERGY", source=energy_source,
                     line_color="yellow", line_width=2, legend_label="Lost Energy", alpha=1)
        EnergyP.legend.location = 'top_left'
        EnergyP.legend.background_fill_alpha = 0.7

    # ============ 添加程序和轴切换的 JavaScript 回调 ============
    # 轴切换：复用当前 program 已加载的数据（纯前端更新）。
    # program 切换：通过接口拉取数据并更新 ColumnDataSource，避免整页重载导致黑屏/样式闪烁。

    axis_callback = CustomJS(
        args=dict(
            axis_select=axis_select,
            program_select=program_select,
            source=source,
            agg_source=agg_source,
            proxy_source=proxy_source,
            proxy_agg_source=proxy_agg_source,
            curr_plot=p_curr,
            line_plot=line_plot,
            axis_config_json=json.dumps(AXIS_CONFIG),
        ),
        code="""
        const AXIS_CONFIG = JSON.parse(axis_config_json);
        const axis = axis_select.value;
        const config = AXIS_CONFIG[axis] || AXIS_CONFIG["A1"];

        const currCol = config.curr;
        const maxCurrCol = config.max_curr;
        const minCurrCol = config.min_curr;
        const torqueCol = config.torque;
        const speedCol = config.speed;
        const folCol = config.fol;
        const axispCol = config.axisp;

        curr_plot.title.text = axis + " - Current Analysis";

        proxy_source.data['sort'] = source.data['sort'];
        proxy_source.data['Timestamp'] = source.data['Timestamp'];
        proxy_source.data['SNR_C'] = source.data['SNR_C'];
        proxy_source.data['P_name'] = source.data['P_name'];
        proxy_source.data['Time'] = source.data['Time'];
        proxy_source.data['Tem_1'] = source.data['Tem_1'];

        proxy_source.data['curr_value'] = source.data[currCol] || [];
        proxy_source.data['max_curr_value'] = source.data[maxCurrCol] || [];
        proxy_source.data['min_curr_value'] = source.data[minCurrCol] || [];
        proxy_source.data['torque_value'] = source.data[torqueCol] || [];
        proxy_source.data['speed_value'] = source.data[speedCol] || [];
        proxy_source.data['fol_value'] = source.data[folCol] || [];
        proxy_source.data['axisp_value'] = source.data[axispCol] || [];

        proxy_agg_source.data['SNR_C'] = agg_source.data['SNR_C'];
        proxy_agg_source.data['P_name'] = agg_source.data['P_name'];
        proxy_agg_source.data['max_curr_value'] = agg_source.data[maxCurrCol] || [];
        proxy_agg_source.data['min_curr_value'] = agg_source.data[minCurrCol] || [];

        const lqCol = currCol + "_LQ";
        const hqCol = currCol + "_HQ";
        proxy_agg_source.data['lq_value'] = agg_source.data[lqCol] || [];
        proxy_agg_source.data['hq_value'] = agg_source.data[hqCol] || [];

        proxy_source.change.emit();
        proxy_agg_source.change.emit();

        // Notify parent to persist selections (without reloading).
        if (window.parent && window.parent !== window) {
          window.parent.postMessage(
            { type: 'biState', program: program_select.value, axis: axis_select.value },
            '*'
          );
        }
        """,
    )
    axis_select.js_on_change("value", axis_callback)

    program_reload_callback = CustomJS(
        args=dict(
            program_select=program_select,
            axis_select=axis_select,
            source=source,
            agg_source=agg_source,
            proxy_source=proxy_source,
            proxy_agg_source=proxy_agg_source,
            curr_plot=p_curr,
            line_plot=line_plot,
            axis_config_json=json.dumps(AXIS_CONFIG),
        ),
        code="""
        const AXIS_CONFIG = JSON.parse(axis_config_json);

        const nextProgram = program_select.value;
        const axis = axis_select.value;
        const config = AXIS_CONFIG[axis] || AXIS_CONFIG["A1"];

        const url = new URL(window.location.href);
        url.searchParams.set('program', nextProgram);
        url.searchParams.set('axis', axis);

        // Update URL without reload (for deep-linking / refresh).
        try {
          window.history.replaceState({}, '', url.toString());
        } catch (e) {}

        const overlay = document.getElementById('biLoadingOverlay');
        if (overlay) overlay.style.display = 'flex';

        // Notify parent to persist selections (without reloading).
        if (window.parent && window.parent !== window) {
          window.parent.postMessage(
            { type: 'biState', program: nextProgram, axis: axis },
            '*'
          );
        }

        // Prevent out-of-order responses from rapid switching.
        const requestId = Date.now().toString(36) + Math.random().toString(36).slice(2);
        window.__biProgramRequestId = requestId;

        const dataUrl = new URL('/api/robots/bi_program_data/', window.location.origin);
        dataUrl.searchParams.set('table', url.searchParams.get('table') || url.searchParams.get('robot') || '');
        dataUrl.searchParams.set('program', nextProgram);
        if (url.searchParams.get('start_date')) dataUrl.searchParams.set('start_date', url.searchParams.get('start_date'));
        if (url.searchParams.get('end_date')) dataUrl.searchParams.set('end_date', url.searchParams.get('end_date'));

        fetch(dataUrl.toString(), { method: 'GET', credentials: 'same-origin' })
          .then((res) => res.json())
          .then((payload) => {
            if (window.__biProgramRequestId !== requestId) return;
            if (!payload || !payload.ok) throw new Error((payload && payload.error) || 'PROGRAM_DATA_FAILED');

            // Replace backing sources (used for axis switching).
            source.data = payload.source || {};
            agg_source.data = payload.agg || {};

            // Refresh proxy sources for current axis.
            const currCol = config.curr;
            const maxCurrCol = config.max_curr;
            const minCurrCol = config.min_curr;
            const torqueCol = config.torque;
            const speedCol = config.speed;
            const folCol = config.fol;
            const axispCol = config.axisp;

            curr_plot.title.text = axis + " - Current Analysis";
            line_plot.title.text = "Aggregate Analysis - " + nextProgram;
            // Program 切换后 SNR_C 因子集合可能变化，必须同步更新 x_range，否则聚合线会错位/缺失。
            if (line_plot.x_range && Array.isArray(agg_source.data['SNR_C'])) {
              line_plot.x_range.factors = agg_source.data['SNR_C'];
            }

            proxy_source.data['sort'] = source.data['sort'];
            proxy_source.data['Timestamp'] = source.data['Timestamp'];
            proxy_source.data['SNR_C'] = source.data['SNR_C'];
            proxy_source.data['P_name'] = source.data['P_name'];
            proxy_source.data['Time'] = source.data['Time'];
            proxy_source.data['Tem_1'] = source.data['Tem_1'];

            proxy_source.data['curr_value'] = source.data[currCol] || [];
            proxy_source.data['max_curr_value'] = source.data[maxCurrCol] || [];
            proxy_source.data['min_curr_value'] = source.data[minCurrCol] || [];
            proxy_source.data['torque_value'] = source.data[torqueCol] || [];
            proxy_source.data['speed_value'] = source.data[speedCol] || [];
            proxy_source.data['fol_value'] = source.data[folCol] || [];
            proxy_source.data['axisp_value'] = source.data[axispCol] || [];

            proxy_agg_source.data['SNR_C'] = agg_source.data['SNR_C'];
            proxy_agg_source.data['P_name'] = agg_source.data['P_name'];
            proxy_agg_source.data['max_curr_value'] = agg_source.data[maxCurrCol] || [];
            proxy_agg_source.data['min_curr_value'] = agg_source.data[minCurrCol] || [];

            const lqCol = currCol + "_LQ";
            const hqCol = currCol + "_HQ";
            proxy_agg_source.data['lq_value'] = agg_source.data[lqCol] || [];
            proxy_agg_source.data['hq_value'] = agg_source.data[hqCol] || [];

            source.change.emit();
            agg_source.change.emit();
            proxy_source.change.emit();
            proxy_agg_source.change.emit();
          })
          .catch((err) => {
            // Fallback: reload the page if dynamic update fails.
            try { console.error('program switch failed', err); } catch (e) {}
            window.location.href = url.toString();
          })
          .finally(() => {
            if (window.__biProgramRequestId !== requestId) return;
            if (overlay) overlay.style.display = 'none';
          });
        """,
    )
    program_select.js_on_change("value", program_reload_callback)

    # ============ 创建布局 ============
    from bokeh.layouts import row, column

    # 能量分析图脚本和div（用于模态框）
    energy_script_content = ''
    energy_div_content = ''
    energy_modal_id = f"energy_modal_{uuid.uuid4().hex[:8]}"

    if EnergyP:
        energy_script_content, energy_div_content = components(EnergyP)

    # 能耗模态框HTML（仅结构，交互由Bokeh按钮绑定）
    energy_modal_html = ''
    if EnergyP:
        energy_modal_html = f'''
        <div id="{energy_modal_id}" class="energy-modal-bg" style="display: none;"></div>
        <div id="{energy_modal_id}_content" class="energy-modal-content" style="display: none;">
            <div class="energy-modal-header">
                <div class="energy-modal-title">能耗分析</div>
                <button id="{energy_modal_id}_close" class="energy-modal-close">关闭</button>
            </div>
            <div id="{energy_modal_id}_chart" class="energy-modal-body">{energy_div_content}</div>
        </div>
        '''

    # 能耗按钮改为模板中的浮动按钮，这里不再创建Bokeh按钮

    # 顶部控件栏 - 标签与下拉框在同一行
    controls_center = row(
        Spacer(width=50, height=1),
        program_label,
        Spacer(width=5, height=1),
        program_select,
        Spacer(width=30, height=1),
        axis_label,
        Spacer(width=5, height=1),
        axis_select,
        Spacer(sizing_mode="stretch_width"),
        sizing_mode="stretch_width",
        css_classes=["bi-controls"]
    )

    top_controls = column(Spacer(height=20), controls_center, sizing_mode="stretch_width")

    # 图表区域 - 只拉伸宽度，保持各自高度
    charts_column = column(
        line_plot,   # 聚合分析图
        p_curr,      # 电流图
        p_temp,      # 温度图
        p_pos,       # 位置图
        p_speed,     # 速度图
        p_fol,       # 跟随误差图
        p_torque,    # 扭矩图
        sizing_mode="stretch_width",
        width=2100
    )

    # 主布局 - 垂直排列：顶部控件 + 图表区域
    main_layout = column(top_controls, charts_column, sizing_mode="stretch_width", width=2100)

    # 使用components生成图表脚本和div
    logger.info("图表对象创建: %.3fs", time.perf_counter() - chart_create_start)
    components_start = time.perf_counter()
    script, div = components(main_layout)
    logger.info("components生成: %.3fs", time.perf_counter() - components_start)

    return script, div, {
        'table_name': table_name,
        'program_name': default_program,
        'data_count': len(df_prog),
        'energy_count': len(energy_full),
        'programs': c_opt,  # 使用 c_opt 替代 programs
        'date_range': f"{start_time.strftime('%Y-%m-%d')} 至 {end_time.strftime('%Y-%m-%d')}",
    }, energy_modal_html, energy_script_content


def _to_jsonable_value(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return item()
        except Exception:
            pass
    return str(value)


def _dataframe_to_jsonable_dict(df: "pd.DataFrame") -> dict:
    if df is None:
        return {}
    if df.empty:
        return {col: [] for col in df.columns}
    safe_df = df.copy()
    safe_df = safe_df.where(pd.notnull(safe_df), None)
    payload = safe_df.to_dict(orient="list")
    for key, values in payload.items():
        payload[key] = [_to_jsonable_value(v) for v in values]
    return payload


def get_bi_program_payload(
    table_name: str,
    program: str,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    获取指定 program 的数据与聚合结果，用于前端无刷新切换 program_name。
    返回 dict:
      { ok: bool, error?: str, source?: dict, agg?: dict }
    """
    # 从Django配置获取数据库连接参数
    db_config = get_db_engine()
    user = db_config["user"]
    password = db_config["password"]
    host = db_config["host"]
    port = db_config["port"]
    database = db_config["database"]
    time_column = "Timestamp"

    try:
        engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")
    except Exception as e:
        logger.error("数据库连接失败: %s", e)
        return {"ok": False, "error": "数据库连接失败"}

    table_name = (table_name or "").strip()
    program = (program or "").strip()
    if not table_name:
        return {"ok": False, "error": "缺少 table 参数"}
    if not program:
        return {"ok": False, "error": "缺少 program 参数"}

    # 直接使用传入的表名和时间范围，与 Digitaltwin_timefree.py 保持一致
    requested_start, requested_end = _normalize_date_bounds(start_date, end_date)
    if requested_start and requested_end:
        if requested_start > requested_end:
            requested_start, requested_end = requested_end, requested_start
        start_time = requested_start
        end_time = requested_end
    else:
        # 默认使用最近 7 天
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

    # 生成缓存键
    start_date_str = start_time.strftime('%Y-%m-%d')
    end_date_str = end_time.strftime('%Y-%m-%d')

    # 先检查缓存（与 Digitaltwin_timefree.py 一致：数据已在内存）
    cached_data = _program_data_cache_get(table_name, start_date_str, end_date_str)
    df_full = None
    from_cache = False

    if cached_data is not None:
        df_full, energy_full = cached_data
        from_cache = True
        logger.info("program切换: 从内存缓存读取数据，行数=%s", len(df_full))
    else:
        # 缓存未命中，查询数据库
        fetch_start = time.perf_counter()
        df_full = fetch_data_from_mysql(
            table_name,
            _format_datetime(start_time),
            _format_datetime(end_time),
            time_column,  # 传递字符串，不使用 dict
            engine,
        )
        logger.info("program切换全量数据: db fetch %.3fs, 行数=%s", time.perf_counter() - fetch_start, len(df_full))

        if df_full.empty:
            return {"ok": False, "error": "该 program 无数据"}

        # 数据预处理（只在从数据库查询时需要）
        df_full = _preprocess_bi_dataframe(df_full)
        # 缓存预处理后的数据
        _program_data_cache_set(table_name, start_date_str, end_date_str, df_full, None)

    # 数据已经预处理过（无论是从缓存还是数据库），直接过滤 program
    # 与 Digitaltwin_timefree.py 一致：从内存数据中过滤
    agg_start = time.perf_counter()
    df_prog = df_full[df_full['Name_C'] == program]  # 不复制，直接过滤

    if df_prog is None or df_prog.empty:
        return {"ok": False, "error": "该 program 无数据"}

    # 聚合计算（与 Digitaltwin_timefree.py 完全一致）
    prog_data = df_prog  # 直接使用，不复制
    prog_data = prog_data.sort_values(by=["SNR_C", "Time"])
    prog_data["sort"] = range(1, len(prog_data) + 1)

    # 聚合数据（与 Digitaltwin_timefree.py 完全一致：直接写死列名）
    ref = prog_data.groupby("SNR_C")[['MAXCurr_A1','MAXCurr_A2','MAXCurr_A3','MAXCurr_A4',
                                      'MAXCurr_A5','MAXCurr_A6','MAXCurr_E1',
                                      'MinCurr_A1','MinCurr_A2','MinCurr_A3','MinCurr_A4',
                                      'MinCurr_A5','MinCurr_A6','MinCurr_E1']].last()

    LQ = prog_data.groupby("SNR_C")[['Curr_A1','Curr_A2','Curr_A3','Curr_A4',
                                          'Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.01, interpolation='nearest').rename(
        columns={'Curr_A1': 'Curr_A1_LQ', 'Curr_A2': 'Curr_A2_LQ', 'Curr_A3': 'Curr_A3_LQ',
                 'Curr_A4': 'Curr_A4_LQ', 'Curr_A5': 'Curr_A5_LQ', 'Curr_A6': 'Curr_A6_LQ',
                 'Curr_E1': 'Curr_E1_LQ'})
    HQ = prog_data.groupby("SNR_C")[['Curr_A1','Curr_A2','Curr_A3','Curr_A4',
                                          'Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.99, interpolation='nearest').rename(
        columns={'Curr_A1': 'Curr_A1_HQ', 'Curr_A2': 'Curr_A2_HQ', 'Curr_A3': 'Curr_A3_HQ',
                 'Curr_A4': 'Curr_A4_HQ', 'Curr_A5': 'Curr_A5_HQ', 'Curr_A6': 'Curr_A6_HQ',
                 'Curr_E1': 'Curr_E1_HQ'})
    labeltext = prog_data.groupby("SNR_C")["P_name"].last()

    # 使用 Digitaltwin_timefree.py 的 merge 方式
    Q = pd.merge(pd.merge(pd.merge(LQ, HQ, left_on=['SNR_C'], right_index=True, how='outer'),
                          ref, left_on=['SNR_C'], right_index=True, how='inner'),
                 labeltext, left_on=['SNR_C'], right_index=True, how='inner').reset_index()

    # 生成 x_tex（与 Digitaltwin_timefree.py 一致）
    x_tex = prog_data["SNR_C"].sort_values(ascending=True).unique().astype(str)
    Q["SNR_C"] = x_tex

    # 日志：显示聚合计算时间
    cache_status = "缓存" if from_cache else "数据库"
    logger.info("program切换完成: 数据来源=%s, 聚合=%.3fs (program=%s)",
                cache_status, time.perf_counter() - agg_start, program)

    return {
        "ok": True,
        "source": _dataframe_to_jsonable_dict(prog_data),
        "agg": _dataframe_to_jsonable_dict(Q),
    }
