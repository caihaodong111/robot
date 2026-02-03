"""
Bokeh图表生成模块 - 静态嵌入Django使用
支持前端控件联动（程序切换、轴切换）
"""
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource, HoverTool, Select,
    CustomJS, LabelSet, BoxAnnotation, Band, DatePicker, Range1d
)
from bokeh.embed import components
import pandas as pd
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import logging
import uuid

logger = logging.getLogger(__name__)


# 轴配置 - A1到A7
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
    """从Django配置获取数据库连接"""
    from django.conf import settings
    db_config = settings.DATABASES.get('default', {})
    return {
        'user': db_config.get('USER'),
        'password': db_config.get('PASSWORD'),
        'host': db_config.get('HOST'),
        'port': db_config.get('PORT') or '3306',
        'database': db_config.get('NAME'),
    }


def get_table_time_range(table_name, engine):
    """获取数据库表中的实际时间范围"""
    query = f"SELECT MIN(`Timestamp`) as min_time, MAX(`Timestamp`) as max_time FROM `{table_name}`;"
    try:
        df = pd.read_sql(query, engine)
        if df.empty or df['min_time'].isna()[0] or df['max_time'].isna()[0]:
            return datetime.now() - timedelta(days=30), datetime.now()
        return df['min_time'][0], df['max_time'][0]
    except Exception as e:
        logger.error(f"获取时间范围失败: {e}")
        return datetime.now() - timedelta(days=30), datetime.now()


def fetch_data_from_mysql(table_name, start_time, end_time, time_column, engine):
    """从MySQL获取数据"""
    query = f"SELECT * FROM `{table_name}` WHERE `{time_column}` BETWEEN '{start_time}' AND '{end_time}';"
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        return pd.DataFrame()


def _coerce_datetime(value):
    if not value:
        return None
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None


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
    """创建BI可视化图表 - 支持前端程序和轴切换"""

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
        return None, None, None

    # 获取数据库实际时间范围
    db_start_time, db_end_time = get_table_time_range(table_name, engine)
    start_time = db_start_time
    end_time = db_end_time

    requested_start = _coerce_datetime(start_date)
    requested_end = _coerce_datetime(end_date)
    if requested_start and requested_end:
        if requested_start > requested_end:
            requested_start, requested_end = requested_end, requested_start
        start_time = max(db_start_time, requested_start)
        end_time = min(db_end_time, requested_end)

    logger.info(f"数据库时间范围: {start_time} 到 {end_time}")

    # 获取主数据
    df_full = fetch_data_from_mysql(
        table_name,
        _format_datetime(start_time),
        _format_datetime(end_time),
        time_column,
        engine,
    )
    if df_full.empty:
        logger.warning(f"表 {table_name} 没有数据")
        return None, None, None
    logger.info(f"加载数据条数: {len(df_full)}, 列数={len(df_full.columns)}")

    # 获取能量数据
    energy_query = f"SELECT TimeStamp2,ENERGY,LOSTENERGY FROM energy WHERE RobotName= '{table_name}'"
    try:
        energy_full = pd.read_sql(energy_query, engine)
        logger.info(f"能量数据条数: {len(energy_full)}")
    except Exception as e:
        logger.warning(f"能量数据获取失败: {e}")
        energy_full = pd.DataFrame()

    # ============ 数据预处理 ============
    columns_to_drop = ['A1_marker', 'A2_marker', 'A3_marker', 'A4_marker',
                       'A5_marker', 'A6_marker', 'A7_marker', 'SUB']
    for col in columns_to_drop:
        if col in df_full.columns:
            del df_full[col]

    df_full = df_full.drop_duplicates()
    df_full['Time'] = pd.to_datetime(df_full['Timestamp']) + timedelta(hours=8)
    df_full['Timestamp'] = df_full['Time'].astype(str)
    df_full['SNR_C'] = df_full['SNR_C'].astype(int)
    for i in range(1, 8):
        col = f'AxisP{i}' if i < 7 else 'AxisP7'
        if col in df_full.columns:
            df_full[col] = df_full[col].astype(float)

    # 获取程序选项
    programs = df_full['Name_C'].unique().tolist()
    logger.info(f"可用程序列表: {programs}")

    # 确定默认程序
    if program and program in programs:
        default_program = program
    else:
        default_program = programs[0] if programs else 'N/A'

    # 确定默认轴
    default_axis = axis if axis in AXIS_CONFIG else 'A1'

    # 能量数据处理
    if not energy_full.empty:
        energy_full['TimeStamp2'] = pd.to_datetime(energy_full['TimeStamp2']) + timedelta(hours=8)
        energy_full['ENERGY'] = energy_full['ENERGY'].astype(float)
        energy_full['LOSTENERGY'] = energy_full['LOSTENERGY'].astype(float)
        energy_full = energy_full.sort_values(by='TimeStamp2', ascending=True)

    # ============ 为所有轴和所有程序准备数据 ============
    # 结构: axis_sources[axis_name][program_name] = {source, agg_source, x_tex}
    axis_sources = {}

    for axis_name, config in AXIS_CONFIG.items():
        curr_col = config['curr']
        max_curr_col = config['max_curr']
        min_curr_col = config['min_curr']

        program_sources = {}
        program_agg_sources = {}
        program_x_tex = {}

        for prog in programs:
            prog_data = df_full[df_full['Name_C'] == prog].copy()
            prog_data = prog_data.sort_values(by=['SNR_C', 'Time'])
            prog_data['sort'] = range(1, len(prog_data) + 1)

            if not prog_data.empty:
                # 聚合数据
                ref = prog_data.groupby('SNR_C')[[max_curr_col, min_curr_col]].last()
                x_tex = prog_data["SNR_C"].sort_values(ascending=True).unique().astype(str)

                LQ = prog_data.groupby('SNR_C')[curr_col].quantile(
                    q=0.01, interpolation='nearest').rename(f'{curr_col}_LQ')
                HQ = prog_data.groupby('SNR_C')[curr_col].quantile(
                    q=0.99, interpolation='nearest').rename(f'{curr_col}_HQ')

                labeltext = prog_data.groupby('SNR_C')['P_name'].last()

                Q = pd.merge(pd.merge(LQ, HQ, left_index=True, right_index=True, how='outer'),
                                       ref, left_index=True, right_index=True, how='inner')
                Q = pd.merge(Q, labeltext, left_index=True, right_index=True, how='inner').reset_index()
                Q["SNR_C"] = x_tex

                program_sources[prog] = ColumnDataSource(prog_data)
                program_agg_sources[prog] = ColumnDataSource(Q)
                program_x_tex[prog] = x_tex

        axis_sources[axis_name] = {
            'program_sources': program_sources,
            'program_agg_sources': program_agg_sources,
            'program_x_tex': program_x_tex,
            'config': config
        }

    # 能量数据源
    energy_source = ColumnDataSource(energy_full) if not energy_full.empty else ColumnDataSource(pd.DataFrame())

    # ============ 创建控件 ============
    from bokeh.models import Div

    program_select = Select(
        title="程序:",
        value=default_program,
        options=programs,
        width=200
    )

    axis_select = Select(
        title="轴:",
        value=default_axis,
        options=list(AXIS_CONFIG.keys()),
        width=120
    )

    # ============ 创建图表 ============
    # 创建代理数据源，使用固定的列名，这样渲染器不需要修改列引用
    # 当切换轴或程序时，我们只需要更新这些代理列的数据

    # 从默认轴和程序获取初始数据
    default_axis_data = axis_sources[default_axis]
    default_config = default_axis_data['config']
    default_source_data = default_axis_data['program_sources'][default_program].data
    default_agg_data = default_axis_data['program_agg_sources'][default_program].data

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

    x_tex = default_axis_data['program_x_tex'][default_program]

    # Hover工具定义 - 使用动态列名显示
    hover = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('电流', '@curr_value'),
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
        ('扭矩', '@torque_value'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover_fol = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('跟随误差', '@fol_value'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover_speed = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('速度', '@speed_value'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover_axisp = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('位置', '@axisp_value'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    # 创建图表 - 使用固定的代理列名
    # 创建共享的y_range，让聚合分析和电流分析图联动
    #shared_y_range = Range1d(start=0, end=100, bounds='auto')

    p_curr = figure(
        title=f'{default_axis} - 电流分析',
        sizing_mode="stretch_width",
        width=2100,
        height=220,
        x_axis_label='运动时间',
        y_axis_label='电流百分比 %',
       #y_range=shared_y_range,
        tools=[hover, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10)
    )
    p_curr.step(x='sort', y='min_curr_value', source=proxy_source, line_width=2, mode="center", color='red', legend_label='最小电流')
    p_curr.step(x='sort', y='max_curr_value', source=proxy_source, line_width=2, mode="center", color='red', legend_label='最大电流')
    p_curr.scatter(x='sort', y='curr_value', source=proxy_source, size=2, alpha=0.6, color='navy', legend_label='实时电流')
    p_curr.legend.location = 'top_right'
    p_curr.legend.click_policy = "hide"
    p_curr.xaxis.visible = False

    p_temp = figure(
        x_range=p_curr.x_range,
        y_range=(15, 100),
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='运动时间',
        y_axis_label='温度 (°C)',
        tools=[hover_temp, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10)
    )
    p_temp.scatter(x='sort', y='Tem_1', source=proxy_source, size=2, color='orange', legend_label='温度')
    p_temp.legend.location = 'top_right'
    p_temp.legend.click_policy = "hide"
    p_temp.xaxis.visible = False

    p_pos = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='运动时间',
        y_axis_label='轴位置',
        tools=[hover_axisp, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10)
    )
    p_pos.scatter(x='sort', y='axisp_value', source=proxy_source, size=2, color='green', legend_label='位置')
    p_pos.legend.location = 'top_right'
    p_pos.legend.click_policy = "hide"
    p_pos.xaxis.visible = False

    p_speed = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='运动时间',
        y_axis_label='电机速度',
        tools=[hover_speed, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10)
    )
    p_speed.scatter(x='sort', y='speed_value', source=proxy_source, size=2, color='blue', legend_label='速度')
    p_speed.legend.location = 'top_right'
    p_speed.legend.click_policy = "hide"
    p_speed.xaxis.visible = False

    p_fol = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='运动时间',
        y_axis_label='跟随误差',
        tools=[hover_fol, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10)
    )
    p_fol.scatter(x='sort', y='fol_value', source=proxy_source, size=2, color='lime', legend_label='跟随误差')
    p_fol.legend.location = 'top_right'
    p_fol.legend.click_policy = "hide"
    p_fol.xaxis.visible = False

    p_torque = figure(
        x_range=p_curr.x_range,
        sizing_mode="stretch_width",
        width=2100,
        height=180,
        x_axis_label='运动时间',
        y_axis_label='扭矩',
        tools=[hover_torque, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
        min_border_left=40,
        min_border_right=10,
        min_border_top=20,
        min_border_bottom=10,
        margin=(5, 10, 5, 10)
    )
    p_torque.scatter(x='sort', y='torque_value', source=proxy_source, size=2, color='sienna', legend_label='扭矩')
    p_torque.legend.location = 'top_right'
    p_torque.legend.click_policy = "hide"
    p_torque.xaxis.visible = False

    # 聚合分析图 - 使用代理数据源和固定列名
    # 使用与电流分析图共享的y_range，实现纵轴联动
    line_plot = figure(
        title=f"聚合分析 - {default_program}",
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
        margin=(5, 10, 5, 10)
    )

    hover_line = HoverTool(
        tooltips=[
            ("SNR_C", "@SNR_C"),
            ("P_name", "@P_name"),
            ("1%分位", "@lq_value"),
            ("99%分位", "@hq_value"),
        ]
    )
    line_plot.add_tools(hover_line)

    line_plot.line(x="SNR_C", y="lq_value", source=proxy_agg_source, line_color="blue",
                    line_width=2, legend_label="1%分位", alpha=1)
    line_plot.line(x="SNR_C", y="hq_value", source=proxy_agg_source, line_color="orange",
                    line_width=2, legend_label="99%分位", alpha=1)
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
            title='能耗分析',
            sizing_mode="stretch_width",
            width=280,
            height=300,
            x_axis_label='时间',
            y_axis_label='能量',
            tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save'],
            min_border_left=40,
            min_border_right=10,
            min_border_top=20,
            min_border_bottom=40
        )
        EnergyP.line(x="TimeStamp2", y="ENERGY", source=energy_source,
                     line_color="orange", line_width=2, legend_label="能耗", alpha=1)
        EnergyP.line(x="TimeStamp2", y="LOSTENERGY", source=energy_source,
                     line_color="yellow", line_width=2, legend_label="损耗能耗", alpha=1)
        EnergyP.legend.location = 'top_left'
        EnergyP.legend.background_fill_alpha = 0.7

    # ============ 添加程序和轴切换的 JavaScript 回调 ============
    # 使用代理数据源方法：复制数据到固定列名，无需修改渲染器属性

    linkage_callback = CustomJS(args=dict(
        program_select=program_select,
        axis_select=axis_select,
        axis_sources=axis_sources,
        proxy_source=proxy_source,
        proxy_agg_source=proxy_agg_source,
        curr_plot=p_curr,
        line_plot=line_plot,
        axis_config_json=json.dumps(AXIS_CONFIG)
    ), code="""
    // 解析 AXIS_CONFIG
    const AXIS_CONFIG = JSON.parse(axis_config_json);

    // 获取当前选择的轴和程序
    const axis = axis_select.value;
    const program = program_select.value;

    // 获取当前轴的数据源和配置
    const axisData = axis_sources[axis];
    const config = AXIS_CONFIG[axis];
    const source = axisData.program_sources[program];
    const aggSource = axisData.program_agg_sources[program];
    const xTex = axisData.program_x_tex[program];

    // 获取列名
    const currCol = config.curr;
    const maxCurrCol = config.max_curr;
    const minCurrCol = config.min_curr;
    const torqueCol = config.torque;
    const speedCol = config.speed;
    const folCol = config.fol;
    const axispCol = config.axisp;

    // 更新图表标题
    curr_plot.title.text = axis + " - 电流分析";
    line_plot.title.text = "聚合分析 - " + program;

    // 更新聚合分析图的 x_range
    line_plot.x_range.factors = xTex;

    // === 更新代理数据源 - 从实际列复制数据到固定列名 ===
    // 时间序列数据
    proxy_source.data['sort'] = source.data['sort'];
    proxy_source.data['Timestamp'] = source.data['Timestamp'];
    proxy_source.data['SNR_C'] = source.data['SNR_C'];
    proxy_source.data['P_name'] = source.data['P_name'];
    proxy_source.data['Time'] = source.data['Time'];
    proxy_source.data['Tem_1'] = source.data['Tem_1'];

    // 复制轴相关数据到固定列名
    proxy_source.data['curr_value'] = source.data[currCol];
    proxy_source.data['max_curr_value'] = source.data[maxCurrCol];
    proxy_source.data['min_curr_value'] = source.data[minCurrCol];
    proxy_source.data['torque_value'] = source.data[torqueCol];
    proxy_source.data['speed_value'] = source.data[speedCol];
    proxy_source.data['fol_value'] = source.data[folCol];
    proxy_source.data['axisp_value'] = source.data[axispCol];

    // 聚合数据
    proxy_agg_source.data['SNR_C'] = aggSource.data['SNR_C'];
    proxy_agg_source.data['P_name'] = aggSource.data['P_name'];
    proxy_agg_source.data['max_curr_value'] = aggSource.data[maxCurrCol];
    proxy_agg_source.data['min_curr_value'] = aggSource.data[minCurrCol];

    // 查找并复制 LQ 和 HQ 数据
    let lqCol = null, hqCol = null;
    for (let col in aggSource.data) {
        if (col.includes('_LQ')) lqCol = col;
        if (col.includes('_HQ')) hqCol = col;
    }
    proxy_agg_source.data['lq_value'] = aggSource.data[lqCol] || [];
    proxy_agg_source.data['hq_value'] = aggSource.data[hqCol] || [];

    // 触发更新
    proxy_source.change.emit();
    proxy_agg_source.change.emit();
    """)

    program_select.js_on_change('value', linkage_callback)
    axis_select.js_on_change('value', linkage_callback)

    # ============ 创建布局 ============
    from bokeh.layouts import row, column

    # 能量分析图脚本和div（用于模态框）
    energy_script_content = ''
    energy_div_content = ''
    energy_modal_id = f"energy_modal_{uuid.uuid4().hex[:8]}"

    if EnergyP:
        energy_script_content, energy_div_content = components(EnergyP)

    # 能耗模态框HTML（包含样式、模态框、脚本）
    energy_modal_html = f'''
    <style>
    .energy-modal-bg-{energy_modal_id} {{
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 9999;
    }}
    .energy-modal-bg-{energy_modal_id}.show {{
        display: block;
    }}
    .energy-modal-content-{energy_modal_id} {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border-radius: 12px;
        padding: 20px;
        max-width: 90%;
        max-height: 90%;
        overflow: auto;
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
        z-index: 10000;
    }}
    </style>
    <div id="{energy_modal_id}" class="energy-modal-bg-{energy_modal_id}"></div>
    <div id="{energy_modal_id}_content" class="energy-modal-content-{energy_modal_id}" style="display: none;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h2 style="margin: 0; font-size: 18px; font-weight: 600;">能耗分析</h2>
            <button onclick="closeEnergyModal_{energy_modal_id}()"
                style="padding: 6px 12px; background: #ef4444; color: white; border: none;
                       border-radius: 6px; cursor: pointer; font-size: 14px;">关闭</button>
        </div>
        <div id="{energy_modal_id}_chart">{energy_div_content}</div>
    </div>
    <script>
    function showEnergyModal_{energy_modal_id}() {{
        document.getElementById('{energy_modal_id}').classList.add('show');
        document.getElementById('{energy_modal_id}_content').style.display = 'block';
    }}
    function closeEnergyModal_{energy_modal_id}() {{
        document.getElementById('{energy_modal_id}').classList.remove('show');
        document.getElementById('{energy_modal_id}_content').style.display = 'none';
    }}
    // 点击背景关闭
    document.getElementById('{energy_modal_id}').addEventListener('click', function(e) {{
        if (e.target === this) {{
            closeEnergyModal_{energy_modal_id}();
        }}
    }});
    </script>
    {energy_script_content}
    '''

    # 能耗按钮
    energy_button_div = None
    if EnergyP:
        button_html = f'''
        <div style="padding: 4px 8px;">
            <button onclick="showEnergyModal_{energy_modal_id}()"
                style="padding: 6px 16px; background: linear-gradient(135deg, #f59e0b, #d97706);
                       color: white; border: none; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">
                能耗分析
            </button>
        </div>
        '''
        energy_button_div = Div(text=button_html, width=100, sizing_mode="fixed")

    # 顶部控件栏 - 使用左右spacer实现居中
    # 计算spacer宽度：(总宽度 - 控件宽度) / 2
    # 控件总宽度约: 200 + 120 + 100 = 420
    spacer_width = int((2100 - 420) / 2)

    top_controls = row(
        Div(text='', width=spacer_width, sizing_mode="fixed"),  # 左侧spacer
        program_select,
        Div(text='', width=20, sizing_mode="fixed"),            # 控件间距
        axis_select,
        Div(text='', width=20, sizing_mode="fixed"),            # 控件间距
        energy_button_div if energy_button_div else Div(text='', width=0, sizing_mode="fixed"),
        Div(text='', width=spacer_width, sizing_mode="fixed"),  # 右侧spacer
        sizing_mode="fixed",
        width=2100
    )

    # 能耗模态框（放在顶部，使用绝对定位，高度为0不影响布局）
    energy_modal_div = Div(text=energy_modal_html, sizing_mode="fixed", width=2100, height=0)

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

    # 主布局 - 垂直排列：模态框 + 顶部控件 + 图表区域
    main_layout = column(energy_modal_div, top_controls, charts_column, sizing_mode="stretch_width", width=2100)

    # 使用components生成图表脚本和div
    script, div = components(main_layout)

    return script, div, {
        'table_name': table_name,
        'program_name': default_program,
        'data_count': len(df_full),
        'energy_count': len(energy_full),
        'programs': programs,
        'date_range': f"{start_time.strftime('%Y-%m-%d')} 至 {end_time.strftime('%Y-%m-%d')}",
    }
