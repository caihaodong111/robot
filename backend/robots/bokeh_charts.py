"""
Bokeh图表生成模块 - 静态嵌入Django使用
"""
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource, HoverTool, Select,
    CustomJS, LabelSet, BoxAnnotation, Band
)
from bokeh.embed import components
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)


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


def fetch_data_from_mysql(table_name, start_time, end_time, time_column, engine):
    """从MySQL获取数据"""
    query = f"SELECT * FROM `{table_name}` WHERE `{time_column}` BETWEEN '{start_time}' AND '{end_time}';"
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        return pd.DataFrame()


def create_bi_charts(table_name='as33_020rb_400', days=30):
    """创建BI可视化图表"""

    # 从Django配置获取数据库连接参数
    db_config = get_db_engine()
    user = db_config['user']
    password = db_config['password']
    host = db_config['host']
    port = db_config['port']
    database = db_config['database']

    # 时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    time_column = 'Timestamp'

    logger.info(f"开始生成图表: 表={table_name}, 天数={days}, 时间范围={start_time} 到 {end_time}")

    # 创建数据库连接
    try:
        engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')
        logger.info(f"数据库连接: {host}:{port}/{database}")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None, None, None

    # 获取主数据
    df = fetch_data_from_mysql(table_name, start_time, end_time, time_column, engine)
    if df.empty:
        logger.warning(f"表 {table_name} 在 {start_time} 到 {end_time} 之间没有数据")
        return None, None, None

    logger.info(f"加载数据条数: {len(df)}, 列数: {len(df.columns)}")

    # 获取能量数据
    energy_query = f"SELECT TimeStamp2,ENERGY,LOSTENERGY FROM energy WHERE RobotName= '{table_name}' and TimeStamp2 BETWEEN '{start_time}' AND '{end_time}';"
    try:
        energy = pd.read_sql(energy_query, engine)
        logger.info(f"能量数据条数: {len(energy)}")
    except Exception as e:
        logger.warning(f"能量数据获取失败: {e}")
        energy = pd.DataFrame()

    # ============ 数据处理 ============
    # 能量数据处理
    if not energy.empty:
        energy['TimeStamp2'] = pd.to_datetime(energy['TimeStamp2']) + timedelta(hours=8)
        energy['ENERGY'] = energy['ENERGY'].astype(float)
        energy['LOSTENERGY'] = energy['LOSTENERGY'].astype(float)
        energy = energy.sort_values(by='TimeStamp2', ascending=True)
        source3 = ColumnDataSource(energy)
    else:
        source3 = ColumnDataSource(pd.DataFrame())

    # 主数据处理
    columns_to_drop = ['A1_marker', 'A2_marker', 'A3_marker', 'A4_marker',
                       'A5_marker', 'A6_marker', 'A7_marker', 'SUB']
    for col in columns_to_drop:
        if col in df.columns:
            del df[col]

    df = df.drop_duplicates()
    df['Time'] = pd.to_datetime(df['Timestamp']) + timedelta(hours=8)
    df['Timestamp'] = df['Time'].astype(str)
    df['SNR_C'] = df['SNR_C'].astype(int)
    for i in range(1, 8):
        col = f'AxisP{i}' if i < 7 else 'AxisP7'
        if col in df.columns:
            df[col] = df[col].astype(float)

    # 获取程序选项
    c_opt = df['Name_C'].unique()

    # 默认选择第一个程序
    deft = df[df['Name_C'] == c_opt[0]].sort_values(by=['SNR_C', 'Time'])
    deft['sort'] = range(1, len(deft) + 1)
    source = ColumnDataSource(deft)

    # 创建聚合数据源
    ref = deft.groupby('SNR_C')[['MAXCurr_A1', 'MAXCurr_A2', 'MAXCurr_A3', 'MAXCurr_A4',
                                  'MAXCurr_A5', 'MAXCurr_A6', 'MAXCurr_E1',
                                  'MinCurr_A1', 'MinCurr_A2', 'MinCurr_A3', 'MinCurr_A4',
                                  'MinCurr_A5', 'MinCurr_A6', 'MinCurr_E1']].last()

    x_tex = deft["SNR_C"].sort_values(ascending=True).unique().astype(str)

    LQ = deft.groupby('SNR_C')[['Curr_A1', 'Curr_A2', 'Curr_A3', 'Curr_A4',
                                 'Curr_A5', 'Curr_A6', 'Curr_E1']].quantile(
        q=0.01, interpolation='nearest').rename(
        columns={'Curr_A1': 'Curr_A1_LQ', 'Curr_A2': 'Curr_A2_LQ',
                 'Curr_A3': 'Curr_A3_LQ', 'Curr_A4': 'Curr_A4_LQ',
                 'Curr_A5': 'Curr_A5_LQ', 'Curr_A6': 'Curr_A6_LQ',
                 'Curr_E1': 'Curr_E1_LQ'})

    HQ = deft.groupby('SNR_C')[['Curr_A1', 'Curr_A2', 'Curr_A3', 'Curr_A4',
                                 'Curr_A5', 'Curr_A6', 'Curr_E1']].quantile(
        q=0.99, interpolation='nearest').rename(
        columns={'Curr_A1': 'Curr_A1_HQ', 'Curr_A2': 'Curr_A2_HQ',
                 'Curr_A3': 'Curr_A3_HQ', 'Curr_A4': 'Curr_A4_HQ',
                 'Curr_A5': 'Curr_A5_HQ', 'Curr_A6': 'Curr_A6_HQ',
                 'Curr_E1': 'Curr_E1_HQ'})

    labeltext = deft.groupby('SNR_C')['P_name'].last()

    Q = pd.merge(pd.merge(pd.merge(LQ, HQ, left_on=['SNR_C'], right_index=True, how='outer'),
                                   ref, left_on=['SNR_C'], right_index=True, how='inner'),
                          labeltext, left_on=['SNR_C'], right_index=True, how='inner').reset_index()
    Q["SNR_C"] = x_tex
    source1 = ColumnDataSource(Q)

    # ============ 创建图表 ============

    # Hover工具定义
    hover = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Curr_A1', '@Curr_A1'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover1 = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Tem_1', '@Tem_1'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover2 = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Torque1', '@Torque1'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover3 = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Fol1', '@Fol1'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover4 = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('Speed1', '@Speed1'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    hover5 = HoverTool(tooltips=[
        ('Timestamp', '@Timestamp'),
        ('AxisP1', '@AxisP1'),
        ('SNR_C', '@SNR_C'),
        ('P_name', '@P_name')
    ])

    # 主电流图
    p = figure(
        title='A1 - 电流分析',
        sizing_mode="stretch_width",
        width=1400,
        height=200,
        x_axis_label='运动时间',
        y_axis_label='电流百分比 %',
        tools=[hover, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save']
    )
    p.step(x='sort', y='MinCurr_A1', source=source, line_width=2, mode="center", color='red', legend_label='最小电流')
    p.step(x='sort', y='MAXCurr_A1', source=source, line_width=2, mode="center", color='red', legend_label='最大电流')
    p.scatter(x='sort', y='Curr_A1', source=source, size=4, alpha=0.6, color='navy', legend_label='实时电流')
    p.legend.location = 'top_right'

    # 温度图
    p2 = figure(
        x_range=p.x_range,
        y_range=(15, 100),
        sizing_mode="stretch_width",
        width=1400,
        height=150,
        x_axis_label='运动时间',
        y_axis_label='温度 (°C)',
        tools=[hover1, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save']
    )
    p2.scatter(x='sort', y='Tem_1', source=source, size=4, color='orange', legend_label='温度')
    p2.legend.location = 'top_right'

    # 位置图
    p1 = figure(
        x_range=p.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=150,
        x_axis_label='运动时间',
        y_axis_label='轴位置',
        tools=[hover5, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save']
    )
    p1.scatter(x='sort', y='AxisP1', source=source, size=4, color='green', legend_label='位置')
    p1.legend.location = 'top_right'

    # 速度图
    p3 = figure(
        x_range=p.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=150,
        x_axis_label='运动时间',
        y_axis_label='电机速度',
        tools=[hover4, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save']
    )
    p3.scatter(x='sort', y='Speed1', source=source, size=4, color='blue', legend_label='速度')
    p3.legend.location = 'top_right'

    # 跟随误差图
    p4 = figure(
        x_range=p.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=150,
        x_axis_label='运动时间',
        y_axis_label='跟随误差',
        tools=[hover3, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save']
    )
    p4.scatter(x='sort', y='Fol1', source=source, size=4, color='lime', legend_label='跟随误差')
    p4.legend.location = 'top_right'

    # 扭矩图
    p5 = figure(
        x_range=p.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=150,
        x_axis_label='运动时间',
        y_axis_label='扭矩',
        tools=[hover2, 'pan', 'wheel_zoom', 'box_zoom', 'reset', 'save']
    )
    p5.scatter(x='sort', y='Torque1', source=source, size=4, color='sienna', legend_label='扭矩')
    p5.legend.location = 'top_right'

    # 聚合分析图
    line_plot = figure(
        title=f"聚合分析 - {deft['Name_C'].iloc[0] if len(deft) > 0 else 'N/A'}",
        sizing_mode="stretch_width",
        width=1400,
        height=250,
        x_range=x_tex,
        tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save']
    )

    hover_line = HoverTool(
        tooltips=[
            ("SNR_C", "@SNR_C"),
            ("P_name", "@P_name"),
            ("Curr_A1_LQ", "@Curr_A1_LQ"),
            ("Curr_A1_HQ", "@Curr_A1_HQ"),
        ]
    )
    line_plot.add_tools(hover_line)

    line_plot.line(x="SNR_C", y="Curr_A1_LQ", source=source1, line_color="blue",
                    line_width=2, legend_label="1%分位", alpha=1)
    line_plot.line(x="SNR_C", y="Curr_A1_HQ", source=source1, line_color="orange",
                    line_width=2, legend_label="99%分位", alpha=1)
    l1 = Band(base="SNR_C", lower="MinCurr_A1", upper="MAXCurr_A1", source=source1,
              fill_alpha=0.3, fill_color="green", line_color="red")
    line_plot.add_layout(l1)

    label_setmax = LabelSet(x="SNR_C", y='Curr_A1_HQ', text='P_name', level='glyph',
                            x_offset=3, y_offset=3, source=source1,
                            text_font_size='7pt', angle=0, text_font_style='bold')
    line_plot.add_layout(label_setmax)

    # 添加警告区域
    low_box = BoxAnnotation(top=-90, fill_alpha=0.2, fill_color='#D55E00')
    high_box = BoxAnnotation(bottom=90, fill_alpha=0.2, fill_color='#D55E00')
    line_plot.add_layout(low_box)
    line_plot.add_layout(high_box)

    line_plot.legend.location = 'bottom'
    line_plot.legend.orientation = 'horizontal'
    line_plot.legend.label_text_font_size = '8pt'
    line_plot.xaxis.major_label_orientation = 1.5

    # 添加警告区域
    low_box = BoxAnnotation(top=-90, fill_alpha=0.2, fill_color='#D55E00')
    high_box = BoxAnnotation(bottom=90, fill_alpha=0.2, fill_color='#D55E00')
    line_plot.add_layout(low_box)
    line_plot.add_layout(high_box)

    # 能量图
    EnergyP = None
    if not energy.empty:
        EnergyP = figure(
            x_axis_type="datetime",
            title='能耗分析',
            sizing_mode="stretch_width",
            width=400,
            height=300,
            x_axis_label='时间',
            y_axis_label='能量(kWh)',
            tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save']
        )
        EnergyP.line(x="TimeStamp2", y="ENERGY", source=source3,
                     line_color="orange", line_width=2, legend_label="能耗", alpha=1)
        EnergyP.line(x="TimeStamp2", y="LOSTENERGY", source=source3,
                     line_color="yellow", line_width=2, legend_label="损耗能耗", alpha=1)
        EnergyP.legend.location = 'top_left'
        EnergyP.legend.background_fill_alpha = 0.7

    # 创建布局 - 和原版一样的左右布局
    from bokeh.layouts import row, column

    # 左侧控制面板
    if EnergyP:
        widgets1 = column(
            EnergyP,
            sizing_mode="stretch_height",
            height=1000,
            width=400
        )
    else:
        # 如果没有能量图，显示提示
        from bokeh.models import Div
        placeholder = Div(text='<div style="padding:20px;text-align:center;color:#999;">暂无能耗数据</div>')
        widgets1 = column(
            placeholder,
            sizing_mode="stretch_height",
            height=1000,
            width=400
        )

    # 右侧图表区域 - 按原始顺序排列
    widgets2 = column(
        line_plot,   # 聚合分析图
        p,           # 电流图
        p2,          # 温度图
        p1,          # 位置图
        p3,          # 速度图
        p4,          # 跟随误差图
        p5,          # 扭矩图
        sizing_mode="stretch_both",
        height=1000,
        width=1400
    )

    # 主布局 - 左右排列
    main_layout = row(widgets2, widgets1, sizing_mode="stretch_both", width=1800)

    # 使用components生成图表脚本和div（只返回一个整体布局）
    script, div = components(main_layout)

    return script, div, {
        'table_name': table_name,
        'program_name': deft['Name_C'].iloc[0] if len(deft) > 0 else 'N/A',
        'data_count': len(df),
        'energy_count': len(energy),
        'programs': c_opt.tolist(),
        'date_range': f"{start_time.strftime('%Y-%m-%d')} 至 {end_time.strftime('%Y-%m-%d')}",
    }
