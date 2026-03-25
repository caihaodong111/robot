import json
import logging
import os
import re
from datetime import datetime, timedelta

import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import (
    Band,
    BoxAnnotation,
    Button,
    ColumnDataSource,
    CustomJS,
    Dialog,
    Div,
    HoverTool,
    LabelSet,
    Select,
    Spacer,
)
from bokeh.plotting import figure
from sqlalchemy import create_engine

from .bokeh_charts import AXIS_CONFIG, get_db_engine

logger = logging.getLogger(__name__)

def _apply_axis_proxy(deft: "pd.DataFrame", q: "pd.DataFrame", axis: str) -> tuple["pd.DataFrame", "pd.DataFrame"]:
    axis_key = axis if axis in AXIS_CONFIG else "A1"
    cfg = AXIS_CONFIG[axis_key]

    def _series(df: "pd.DataFrame", col: str):
        if col in df.columns:
            return df[col]
        return pd.Series([None] * len(df), index=df.index)

    curr_col = cfg["curr"]
    min_curr_col = cfg["min_curr"]
    max_curr_col = cfg["max_curr"]
    torque_col = cfg["torque"]
    speed_col = cfg["speed"]
    fol_col = cfg["fol"]
    axisp_col = cfg["axisp"]
    lq_col = f"{curr_col}_LQ"
    hq_col = f"{curr_col}_HQ"

    deft = deft.assign(
        Curr=_series(deft, curr_col),
        MinCurr=_series(deft, min_curr_col),
        MaxCurr=_series(deft, max_curr_col),
        Torque=_series(deft, torque_col),
        Speed=_series(deft, speed_col),
        Fol=_series(deft, fol_col),
        AxisP=_series(deft, axisp_col),
    )
    q = q.assign(
        Curr_LQ=_series(q, lq_col),
        Curr_HQ=_series(q, hq_col),
        MinCurr=_series(q, min_curr_col),
        MaxCurr=_series(q, max_curr_col),
    )
    return deft, q


def _get_request_arg(doc, key: str) -> str | None:
    try:
        ctx = doc.session_context
        if not ctx or not getattr(ctx, "request", None):
            return None
        args = ctx.request.arguments or {}
        raw = args.get(key)
        if not raw:
            return None
        if isinstance(raw, (list, tuple)):
            raw = raw[0] if raw else None
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            return raw.decode("utf-8", errors="ignore")
        return str(raw)
    except Exception:
        return None


def _validate_table_name(value: str) -> str:
    value = (value or "").strip()
    if not re.match(r"^[0-9a-zA-Z_-]+$", value):
        raise ValueError("非法的表名参数")
    return value


def _is_date_only(value: str) -> bool:
    return bool(re.match(r"^\\d{4}-\\d{2}-\\d{2}$", value or ""))


def _parse_range(start_value: str, end_value: str) -> tuple[datetime | None, datetime | None]:
    if not start_value or not end_value:
        return None, None
    start_dt = pd.to_datetime(start_value, errors="coerce")
    end_dt = pd.to_datetime(end_value, errors="coerce")
    if pd.isna(start_dt) or pd.isna(end_dt):
        return None, None
    start_time = start_dt.to_pydatetime()
    end_time = end_dt.to_pydatetime()
    if _is_date_only(start_value):
        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    if _is_date_only(end_value):
        # 与 Digitaltwin_timefree.py 的 update() 一致：end_date 覆盖整天
        end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)
    if start_time > end_time:
        start_time, end_time = end_time, start_time
    return start_time, end_time


def fetch_data_from_mysql(table_name: str, start_time: datetime, end_time: datetime, engine, time_column: str = "Timestamp"):
    query = (
        f"SELECT * FROM `{table_name}` "
        f"WHERE `{time_column}` BETWEEN '{start_time.strftime('%Y-%m-%d %H:%M:%S')}' "
        f"AND '{end_time.strftime('%Y-%m-%d %H:%M:%S')}';"
    )
    return pd.read_sql(query, engine)


def _preprocess_df(df: "pd.DataFrame") -> "pd.DataFrame":
    if df is None:
        return pd.DataFrame()
    if df.empty:
        # 保留 columns，避免后续 KeyError
        return df

    # 与 Digitaltwin_timefree.py 一致：直接删除并去重
    del df["A1_marker"], df["A2_marker"], df["A3_marker"], df["A4_marker"], df["A5_marker"], df["A6_marker"], df["A7_marker"], df["SUB"]
    df = df.drop_duplicates()

    df["Time"] = pd.to_datetime(df["Timestamp"]) + timedelta(hours=8)
    df["Timestamp"] = df["Time"].astype(str)
    df["SNR_C"] = df["SNR_C"].astype(int)

    df["AxisP1"] = df["AxisP1"].astype(float)
    df["AxisP2"] = df["AxisP2"].astype(float)
    df["AxisP3"] = df["AxisP3"].astype(float)
    df["AxisP4"] = df["AxisP4"].astype(float)
    df["AxisP5"] = df["AxisP5"].astype(float)
    df["AxisP6"] = df["AxisP6"].astype(float)
    df["AxisP7"] = df["AxisP7"].astype(float)

    return df


def _compute_agg(deft: "pd.DataFrame") -> tuple["pd.DataFrame", list[str]]:
    ref = deft.groupby("SNR_C")[
        [
            "MAXCurr_A1",
            "MAXCurr_A2",
            "MAXCurr_A3",
            "MAXCurr_A4",
            "MAXCurr_A5",
            "MAXCurr_A6",
            "MAXCurr_E1",
            "MinCurr_A1",
            "MinCurr_A2",
            "MinCurr_A3",
            "MinCurr_A4",
            "MinCurr_A5",
            "MinCurr_A6",
            "MinCurr_E1",
        ]
    ].last()

    x_tex = deft["SNR_C"].sort_values(ascending=True).unique().astype(str).tolist()

    lq = (
        deft.groupby("SNR_C")[["Curr_A1", "Curr_A2", "Curr_A3", "Curr_A4", "Curr_A5", "Curr_A6", "Curr_E1"]]
        .quantile(q=0.01, interpolation="nearest")
        .rename(
            columns={
                "Curr_A1": "Curr_A1_LQ",
                "Curr_A2": "Curr_A2_LQ",
                "Curr_A3": "Curr_A3_LQ",
                "Curr_A4": "Curr_A4_LQ",
                "Curr_A5": "Curr_A5_LQ",
                "Curr_A6": "Curr_A6_LQ",
                "Curr_E1": "Curr_E1_LQ",
            }
        )
    )
    hq = (
        deft.groupby("SNR_C")[["Curr_A1", "Curr_A2", "Curr_A3", "Curr_A4", "Curr_A5", "Curr_A6", "Curr_E1"]]
        .quantile(q=0.99, interpolation="nearest")
        .rename(
            columns={
                "Curr_A1": "Curr_A1_HQ",
                "Curr_A2": "Curr_A2_HQ",
                "Curr_A3": "Curr_A3_HQ",
                "Curr_A4": "Curr_A4_HQ",
                "Curr_A5": "Curr_A5_HQ",
                "Curr_A6": "Curr_A6_HQ",
                "Curr_E1": "Curr_E1_HQ",
            }
        )
    )
    labeltext = deft.groupby("SNR_C")["P_name"].last()

    q = (
        pd.merge(pd.merge(pd.merge(lq, hq, left_on=["SNR_C"], right_index=True, how="outer"), ref, left_on=["SNR_C"], right_index=True, how="inner"), labeltext, left_on=["SNR_C"], right_index=True, how="inner")
        .reset_index()
    )
    q["SNR_C"] = x_tex
    return q, x_tex


def bkapp(doc):
    # === 参数（来自 Django embed 的 querystring）===
    default_table = os.getenv("BI_DEFAULT_TABLE", "as33_020rb_400")
    table_arg = _get_request_arg(doc, "table") or _get_request_arg(doc, "robot") or default_table
    program_arg = (_get_request_arg(doc, "program") or "").strip()
    axis_arg = (_get_request_arg(doc, "axis") or "").strip() or "A1"
    start_arg = (_get_request_arg(doc, "start_date") or "").strip()
    end_arg = (_get_request_arg(doc, "end_date") or "").strip()

    table_name = _validate_table_name(table_arg)

    logger.info(f"[BI LOAD START] table={table_name}, program={program_arg}, axis={axis_arg}, range={start_arg} ~ {end_arg}")

    # === 数据库连接（与项目一致：SG_DB_*）===
    db_config = get_db_engine()
    engine = create_engine(
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}",
        pool_recycle=3600,  # 1小时回收连接，避免 MySQL wait_timeout 断开
        pool_pre_ping=True,  # 使用连接前检查有效性
        connect_args={
            "connect_timeout": 60,  # 连接超时 60 秒
            "read_timeout": 300,    # 读超时 5 分钟
            "write_timeout": 300,   # 写超时 5 分钟
        }
    )

    # === 时间范围（与 Digitaltwin_timefree.py 一致：默认最近7天；日期入参覆盖整天）===
    start_time, end_time = _parse_range(start_arg, end_arg)
    if not start_time or not end_time:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

    # === 限制时间范围，避免查询超时 ===
    max_days = 90
    days_diff = (end_time - start_time).days
    if days_diff > max_days:
        logger.warning(f"[BI LOAD] Time range too large: {days_diff} days > {max_days} days")
        doc.add_root(
            column(
                Div(
                    text=(
                        "<div style='padding:16px;font-size:14px;color:#e74c3c;'>"
                        "<b>时间范围过大</b><br/>"
                        f"当前选择: <code>{days_diff}</code> 天<br/>"
                        f"最大支持: <code>{max_days}</code> 天<br/>"
                        f"请缩小时间范围后重试"
                        "</div>"
                    )
                )
            )
        )
        return doc

    # === 首次拉取数据 ===
    logger.info(f"[BI LOAD] Fetching data from database...")
    df = fetch_data_from_mysql(table_name, start_time, end_time, engine, time_column="Timestamp")
    if df is None or df.empty:
        logger.warning(f"[BI LOAD] No data found for table={table_name}")
        doc.add_root(
            column(
                Div(
                    text=(
                        "<div style='padding:16px;font-size:14px;'>"
                        "<b>BI 无数据</b><br/>"
                        f"robot/table: <code>{table_name}</code><br/>"
                        f"range: <code>{start_time.strftime('%Y-%m-%d %H:%M:%S')}</code> ~ "
                        f"<code>{end_time.strftime('%Y-%m-%d %H:%M:%S')}</code>"
                        "</div>"
                    )
                ),
            )
        )
        return
    logger.info(f"[BI LOAD] Data fetched: {len(df)} rows")
    df = _preprocess_df(df)
    logger.info(f"[BI LOAD] Data preprocessed: {len(df)} rows after deduplication")

    c_opt = df["Name_C"].unique().tolist() if not df.empty and "Name_C" in df.columns else []
    default_program = program_arg if program_arg and program_arg in c_opt else (c_opt[0] if c_opt else "")
    default_axis = axis_arg if axis_arg in AXIS_CONFIG else "A1"

    deft = df[df["Name_C"] == default_program] if default_program else df
    if deft is None or deft.empty:
        doc.add_root(
            column(
                Div(
                    text=(
                        "<div style='padding:16px;font-size:14px;'>"
                        "<b>BI 无 program 数据</b><br/>"
                        f"robot/table: <code>{table_name}</code><br/>"
                        f"program: <code>{default_program}</code>"
                        "</div>"
                    )
                ),
            )
        )
        return

    deft = deft.sort_values(by=["SNR_C", "Time"])
    deft["sort"] = range(1, len(deft) + 1)

    logger.info(f"[BI LOAD] Computing aggregation for {len(deft)} rows...")
    q, x_tex = _compute_agg(deft) if not deft.empty else (pd.DataFrame(), [])
    logger.info(f"[BI LOAD] Aggregation computed: {len(q)} groups, {len(x_tex)} SNR_C values")

    deft, q = _apply_axis_proxy(deft, q, default_axis)
    source = ColumnDataSource(deft)
    source1 = ColumnDataSource(q)

    # === energy ===
    logger.info(f"[BI LOAD] Fetching energy data...")
    energy_query = (
        "SELECT TimeStamp2,ENERGY,LOSTENERGY FROM energy "
        f"WHERE RobotName= '{table_name}' and TimeStamp2 BETWEEN '{start_time.strftime('%Y-%m-%d %H:%M:%S')}' AND '{end_time.strftime('%Y-%m-%d %H:%M:%S')}';"
    )
    try:
        energy = pd.read_sql(energy_query, engine)
    except Exception:
        energy = pd.DataFrame()
    if not energy.empty:
        energy["TimeStamp2"] = pd.to_datetime(energy["TimeStamp2"]) + timedelta(hours=8)
        energy["ENERGY"] = energy["ENERGY"].astype(float)
        energy["LOSTENERGY"] = energy["LOSTENERGY"].astype(float)
        energy = energy.sort_values(by="TimeStamp2", ascending=True)
    logger.info(f"[BI LOAD] Energy data fetched: {len(energy)} rows")
    energy_source = ColumnDataSource(energy)

    # === widgets（PROGRAM CYCLE SYNC 页面已在外层提供 robot/日期选择，这里仅保留 program/axis）===
    program_select = Select(title="program_name", value=default_program, options=c_opt, width=420)
    program_select.name = "program_select"

    axis_select = Select(title="Axis select", value=default_axis, options=list(AXIS_CONFIG.keys()), width=220)
    axis_select.name = "axis_select"

    # === 图表（布局和思路与 Digitaltwin_timefree.py 对齐）===
    hover = HoverTool(tooltips=[("Timestamp", "@Timestamp"), ("Current", "@Curr"), ("SNR_C", "@SNR_C"), ("P_name", "@P_name")])
    hover_temp = HoverTool(tooltips=[("Timestamp", "@Timestamp"), ("Tem_1", "@Tem_1"), ("SNR_C", "@SNR_C"), ("P_name", "@P_name")])
    hover_torque = HoverTool(tooltips=[("Timestamp", "@Timestamp"), ("Torque", "@Torque"), ("SNR_C", "@SNR_C"), ("P_name", "@P_name")])
    hover_fol = HoverTool(tooltips=[("Timestamp", "@Timestamp"), ("Following Error", "@Fol"), ("SNR_C", "@SNR_C"), ("P_name", "@P_name")])
    hover_speed = HoverTool(tooltips=[("Timestamp", "@Timestamp"), ("Speed", "@Speed"), ("SNR_C", "@SNR_C"), ("P_name", "@P_name")])
    hover_axisp = HoverTool(tooltips=[("Timestamp", "@Timestamp"), ("Position", "@AxisP"), ("SNR_C", "@SNR_C"), ("P_name", "@P_name")])

    p_curr = figure(
        title=f"{default_axis} - Current Analysis",
        sizing_mode="stretch_width",
        width=1400,
        height=190,
        x_axis_label="motion_time",
        y_axis_label="Current %",
        output_backend="webgl",
    )
    p_curr.xaxis.visible = False
    g_min = p_curr.step(x="sort", y="MinCurr", source=source, line_width=2, mode="center", color="red")
    g_max = p_curr.step(x="sort", y="MaxCurr", source=source, line_width=2, mode="center", color="red")
    g_curr = p_curr.scatter(x="sort", y="Curr", source=source, size=3, alpha=0.7)
    p_curr.add_tools(hover)

    p_temp = figure(
        x_range=p_curr.x_range,
        y_range=(15, 100),
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label="motion_time",
        y_axis_label="Temperature",
        output_backend="webgl",
    )
    p_temp.xaxis.visible = False
    g_temp = p_temp.scatter(x="sort", y="Tem_1", source=source, size=3, color="orange")
    p_temp.add_tools(hover_temp)

    p_pos = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label="motion_time",
        y_axis_label="Axis_position",
        output_backend="webgl",
    )
    p_pos.xaxis.visible = False
    g_pos = p_pos.scatter(x="sort", y="AxisP", source=source, size=3, color="green")
    p_pos.add_tools(hover_axisp)

    p_speed = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label="motion_time",
        y_axis_label="motor speed",
        output_backend="webgl",
    )
    p_speed.xaxis.visible = False
    g_speed = p_speed.scatter(x="sort", y="Speed", source=source, size=3, color="blue")
    p_speed.add_tools(hover_speed)

    p_fol = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label="motion_time",
        y_axis_label="Following error",
        output_backend="webgl",
    )
    p_fol.xaxis.visible = False
    g_fol = p_fol.scatter(x="sort", y="Fol", source=source, size=3, color="lime")
    p_fol.add_tools(hover_fol)

    p_torque = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label="motion_time",
        y_axis_label="Torque",
        output_backend="webgl",
    )
    p_torque.xaxis.visible = False
    g_torque = p_torque.scatter(x="sort", y="Torque", source=source, size=3, color="sienna")
    p_torque.add_tools(hover_torque)

    line_plot = figure(
        title=default_program or table_name,
        sizing_mode="stretch_width",
        width=1400,
        height=200,
        x_range=[str(x) for x in x_tex],
        y_range=p_curr.y_range,
        output_backend="webgl",
    )
    lq_line = line_plot.line(x="SNR_C", y="Curr_LQ", source=source1, line_color="blue", line_width=2, alpha=1)
    hq_line = line_plot.line(x="SNR_C", y="Curr_HQ", source=source1, line_color="orange", line_width=2, alpha=1)
    ref_band = Band(base="SNR_C", lower="MinCurr", upper="MaxCurr", source=source1, fill_alpha=0.3, fill_color="green", line_color="red")
    line_plot.add_layout(ref_band)
    band = BoxAnnotation(top=-90, fill_alpha=0.2, fill_color="#D55E00")
    band2 = BoxAnnotation(bottom=90, fill_alpha=0.2, fill_color="#D55E00")
    line_plot.add_layout(band)
    line_plot.add_layout(band2)

    label_setmax = LabelSet(
        x="SNR_C",
        y="Curr_HQ",
        text="P_name",
        level="glyph",
        x_offset=3,
        y_offset=3,
        source=source1,
        text_font_size="7pt",
        angle=0,
        text_font_style="bold",
    )
    line_plot.add_layout(label_setmax, "center")

    # Energy
    energy_plot = figure(
        x_axis_type="datetime",
        title="Energy",
        sizing_mode="stretch_width",
        width=360,
        height=260,
        x_axis_label="Time",
        y_axis_label="Energy",
        output_backend="webgl",
    )
    if not energy.empty:
        energy_plot.line(x="TimeStamp2", y="ENERGY", source=energy_source, line_color="orange", line_width=2)
        energy_plot.line(x="TimeStamp2", y="LOSTENERGY", source=energy_source, line_color="yellow", line_width=2)

    # === 轴切换：仅更新代理列（避免 JS 修改 glyph.field 在部分版本/后端下不生效）===
    axis_callback = CustomJS(
        args=dict(
            axis_select=axis_select,
            source=source,
            source1=source1,
            p_curr=p_curr,
            axis_config_json=json.dumps(AXIS_CONFIG),
            hover=hover,
            hover_torque=hover_torque,
            hover_fol=hover_fol,
            hover_speed=hover_speed,
            hover_axisp=hover_axisp,
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
        const lqCol = currCol + "_LQ";
        const hqCol = currCol + "_HQ";

        const s = source.data || {};
        s['Curr'] = s[currCol] || [];
        s['MinCurr'] = s[minCurrCol] || [];
        s['MaxCurr'] = s[maxCurrCol] || [];
        s['Torque'] = s[torqueCol] || [];
        s['Speed'] = s[speedCol] || [];
        s['Fol'] = s[folCol] || [];
        s['AxisP'] = s[axispCol] || [];

        const a = source1.data || {};
        a['Curr_LQ'] = a[lqCol] || [];
        a['Curr_HQ'] = a[hqCol] || [];
        a['MinCurr'] = a[minCurrCol] || [];
        a['MaxCurr'] = a[maxCurrCol] || [];

        p_curr.title.text = axis + " - Current Analysis";

        hover.tooltips = [['Timestamp','@Timestamp'],['Current (' + axis + ')','@Curr'],['SNR_C','@SNR_C'],['P_name','@P_name']];
        hover_torque.tooltips = [['Timestamp','@Timestamp'],['Torque (' + axis + ')','@Torque'],['SNR_C','@SNR_C'],['P_name','@P_name']];
        hover_fol.tooltips = [['Timestamp','@Timestamp'],['Following Error (' + axis + ')','@Fol'],['SNR_C','@SNR_C'],['P_name','@P_name']];
        hover_speed.tooltips = [['Timestamp','@Timestamp'],['Speed (' + axis + ')','@Speed'],['SNR_C','@SNR_C'],['P_name','@P_name']];
        hover_axisp.tooltips = [['Timestamp','@Timestamp'],['Position (' + axis + ')','@AxisP'],['SNR_C','@SNR_C'],['P_name','@P_name']];

        source.change.emit();
        source1.change.emit();
        """,
    )
    axis_select.js_on_change("value", axis_callback)

    # === program 切换：Python 侧更新 source/source1（与 Digitaltwin_timefree.py 对齐）===
    def _update_program(attr, old, new):
        nonlocal deft, q, x_tex
        if not new:
            return
        next_deft = df[df["Name_C"] == new].sort_values(by=["SNR_C", "Time"])
        next_deft["sort"] = range(1, len(next_deft) + 1)

        next_q, next_x = _compute_agg(next_deft) if not next_deft.empty else (pd.DataFrame(), [])
        # 依据当前 axis 生成代理列，保持轴切换纯前端更新
        next_deft, next_q = _apply_axis_proxy(next_deft, next_q, axis_select.value)

        source.data = ColumnDataSource.from_df(next_deft)
        source1.data = ColumnDataSource.from_df(next_q) if not next_q.empty else {}
        line_plot.x_range.factors = [str(x) for x in next_x]
        line_plot.title.text = new

    program_select.on_change("value", _update_program)

    logger.info(f"[BI LOAD] Creating charts and layout...")
    energy_dialog = Dialog(
        title="Energy",
        visible=False,
        close_action="hide",
        content=column(energy_plot, sizing_mode="stretch_width", width=980),
        styles={"width": "min(1100px, 92vw)"},
    )

    energy_button = Button(label="Energy", button_type="primary", width=140, height=32)

    energy_button_stack = column(Spacer(height=19), energy_button, width=140)

    def _open_energy():
        energy_dialog.visible = True

    energy_button.on_click(_open_energy)

    top_controls = row(
        program_select,
        axis_select,
        energy_button_stack,
        sizing_mode="stretch_width",
        styles={
            "justify-content": "center",
            "align-items": "flex-start",
            "gap": "12px",
            "padding": "6px 0",
        },
    )
    charts = column(line_plot, p_curr, p_temp, p_pos, p_speed, p_fol, p_torque, sizing_mode="stretch_width")
    doc.add_root(column(top_controls, charts, sizing_mode="stretch_width"))
    doc.add_root(energy_dialog)
    logger.info(f"[BI LOAD COMPLETE] BI charts ready for table={table_name}, program={default_program}, axis={default_axis}")
