"""
Bokeh BI可视化应用 - 可嵌入Django的版本
运行命令: bokeh serve --port 5006 --allow-websocket-origin=localhost:8000 bokeh_bi_app.py
"""
from bokeh.plotting import figure
import pandas as pd
from bokeh.models import (
    ColumnDataSource, TextInput, Button, HoverTool, Select,
    DateRangePicker, CustomJS, LabelSet, BoxAnnotation,
    LassoSelectTool, Band
)
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from bokeh.layouts import row, column


def fetch_data_from_mysql(table_name, start_time, end_time, time_column, engine):
    """从MySQL获取数据"""
    query = f"SELECT * FROM `{table_name}` WHERE `{time_column}` BETWEEN '{start_time}' AND '{end_time}';"
    df = pd.read_sql(query, engine)
    return df


def bkapp(doc):
    """Bokeh应用主函数"""

    # 数据库连接参数
    user = 'root'
    password = '123456'
    host = '172.19.106.123'
    port = '3306'
    database = 'showdata'

    # 默认参数
    table_name = 'HC21_050RB_300'
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now()
    time_column = 'Timestamp'

    # 创建数据库连接
    engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

    # 获取主数据
    df = fetch_data_from_mysql(table_name, start_time, end_time, time_column, engine)
    print(f"数据条数: {len(df)}")

    # 获取能量数据
    energy_query = f"SELECT TimeStamp2,ENERGY,LOSTENERGY FROM energy WHERE RobotName= '{table_name}' and TimeStamp2 BETWEEN '{start_time}' AND '{end_time}';"
    energy = pd.read_sql(energy_query, engine)

    # ============ 数据处理 ============
    # 能量数据处理
    energy['TimeStamp2'] = pd.to_datetime(energy['TimeStamp2']) + timedelta(hours=8)
    energy['ENERGY'] = energy['ENERGY'].astype(float)
    energy['LOSTENERGY'] = energy['LOSTENERGY'].astype(float)
    energy = energy.sort_values(by='TimeStamp2', ascending=True)
    source3 = ColumnDataSource(energy)

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
        title='A1',
        sizing_mode="stretch_width",
        width=1400,
        height=190,
        x_axis_label='motion_time',
        y_axis_label='Current1 Percentage %',
        output_backend='webgl'
    )
    p.xaxis.visible = False
    g11 = p.step(x='sort', y='MinCurr_A1', source=source, line_width=2, mode="center", color='red')
    g12 = p.step(x='sort', y='MAXCurr_A1', source=source, line_width=2, mode="center", color='red')
    g13 = p.scatter(x='sort', y='Curr_A1', source=source, size=3, alpha=0.7)
    p.add_tools(hover)
    p.add_tools(LassoSelectTool())

    # 温度图
    p2 = figure(
        x_range=p.x_range,
        y_range=(15, 100),
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='Temperature',
        output_backend='webgl'
    )
    g2 = p2.scatter(x='sort', y='Tem_1', source=source, size=3, color='orange')
    p2.xaxis.visible = False
    p2.add_tools(hover1)

    # 位置图
    p1 = figure(
        x_range=p.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='Axis_position',
        output_backend='webgl'
    )
    g3 = p1.scatter(x='sort', y='AxisP1', source=source, size=3, color='green')
    p1.xaxis.visible = False
    p1.add_tools(hover5)

    # 速度图
    p3 = figure(
        x_range=p.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='mortor speed',
        output_backend='webgl'
    )
    g4 = p3.scatter(x='sort', y='Speed1', source=source, size=3, color='blue')
    p3.xaxis.visible = False
    p3.add_tools(hover4)

    # 跟随误差图
    p4 = figure(
        x_range=p.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='Following error',
        output_backend='webgl'
    )
    g5 = p4.scatter(x='sort', y='Fol1', source=source, size=3, color='lime')
    p4.xaxis.visible = False
    p4.add_tools(hover3)

    # 扭矩图
    p5 = figure(
        x_range=p.x_range,
        sizing_mode="stretch_width",
        width=1400,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='Torque',
        output_backend='webgl'
    )
    g6 = p5.scatter(x='sort', y='Torque1', source=source, size=3, color='sienna')
    p5.xaxis.visible = False
    p5.add_tools(hover2)

    # 聚合分析图
    line_plot = figure(
        title=deft['Name_C'].iloc[0] if len(deft) > 0 else 'N/A',
        sizing_mode="stretch_width",
        width=1400,
        height=200,
        x_range=x_tex,
        y_range=p.y_range
    )

    l3 = line_plot.line(x="SNR_C", y="Curr_A1_LQ", source=source1, line_color="blue",
                        line_width=2, legend_label="Curr_min", alpha=1)
    l4 = line_plot.line(x="SNR_C", y="Curr_A1_HQ", source=source1, line_color="orange",
                        line_width=2, legend_label="Curr_max", alpha=1)
    l1 = Band(base="SNR_C", lower="MinCurr_A1", upper="MAXCurr_A1", source=source1,
              fill_alpha=0.3, fill_color="green", line_color="red")
    line_plot.add_layout(l1)

    label_setmax = LabelSet(x="SNR_C", y='Curr_A1_HQ', text='P_name', level='glyph',
                            x_offset=3, y_offset=3, source=source1,
                            text_font_size='7pt', angle=0, text_font_style='bold')
    line_plot.add_layout(label_setmax, 'center')

    hover_line = HoverTool(
        tooltips=[
            ("SNR_C", "@SNR_C"),
            ("P_name", "@P_name")
        ],
        mode="vline"
    )
    line_plot.add_tools(hover_line)
    line_plot.legend.location = 'bottom'
    line_plot.legend.orientation = 'horizontal'
    line_plot.legend.label_text_font_size = '7pt'
    line_plot.xaxis.major_label_orientation = 1.5

    # 添加警告区域
    low_box = BoxAnnotation(top=-90, fill_alpha=0.2, fill_color='#D55E00')
    high_box = BoxAnnotation(bottom=90, fill_alpha=0.2, fill_color='#D55E00')
    line_plot.add_layout(low_box)
    line_plot.add_layout(high_box)

    # 能量图
    EnergyP = figure(
        x_axis_type="datetime",
        title='Energy',
        sizing_mode="stretch_both",
        width=500,
        height=700,
        x_axis_label='Time',
        y_axis_label='Energy (kWh)',
        output_backend='webgl'
    )
    EnergyP.line(x="TimeStamp2", y="ENERGY", source=source3,
                 line_color="orange", line_width=2, legend_label="Energy", alpha=1)
    EnergyP.line(x="TimeStamp2", y="LOSTENERGY", source=source3,
                 line_color="yellow", line_width=2, legend_label="Lost_Energy", alpha=1)
    EnergyP.legend.location = 'top_left'

    # ============ 控件 ============

    # 轴选择下拉菜单
    menu_options = [
        ("A1", "MinCurr_A1", 'MAXCurr_A1', 'Curr_A1', 'Tem_1', 'AxisP1',
         'MAXCurr_A1', 'MinCurr_A1', 'Curr_A1_LQ', 'Curr_A1_HQ', 'Speed1', 'Torque1', 'Fol1'),
        ("A2", "MinCurr_A2", 'MAXCurr_A2', 'Curr_A2', 'Tem_2', 'AxisP2',
         'MAXCurr_A2', 'MinCurr_A2', 'Curr_A2_LQ', 'Curr_A2_HQ', 'Speed2', 'Torque2', 'Fol2'),
        ("A3", "MinCurr_A3", 'MAXCurr_A3', 'Curr_A3', 'Tem_3', 'AxisP3',
         'MAXCurr_A3', 'MinCurr_A3', 'Curr_A3_LQ', 'Curr_A3_HQ', 'Speed3', 'Torque3', 'Fol3'),
        ("A4", "MinCurr_A4", 'MAXCurr_A4', 'Curr_A4', 'Tem_4', 'AxisP4',
         'MAXCurr_A4', 'MinCurr_A4', 'Curr_A4_LQ', 'Curr_A4_HQ', 'Speed4', 'Torque4', 'Fol4'),
        ("A5", "MinCurr_A5", 'MAXCurr_A5', 'Curr_A5', 'Tem_5', 'AxisP5',
         'MAXCurr_A5', 'MinCurr_A5', 'Curr_A5_LQ', 'Curr_A5_HQ', 'Speed5', 'Torque5', 'Fol5'),
        ("A6", "MinCurr_A6", 'MAXCurr_A6', 'Curr_A6', 'Tem_6', 'AxisP6',
         'MAXCurr_A6', 'MinCurr_A6', 'Curr_A6_LQ', 'Curr_A6_HQ', 'Speed6', 'Torque6', 'Fol6'),
        ("A7", "MinCurr_E1", 'MAXCurr_E1', 'Curr_E1', 'Tem_7', 'AxisP7',
         'MAXCurr_E1', 'MinCurr_E1', 'Curr_E1_LQ', 'Curr_E1_HQ', 'Speed7', 'Torque7', 'Fol7'),
    ]

    select = Select(title='Axis select', value='A1', options=['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7'], width=380)

    # JavaScript回调 - 轴切换
    code = """
    var data = source.data;
    var value = select.value;
    var field11 = null;
    var field12 = null;
    var field13 = null;
    var field2 = null;
    var field3 = null;
    var field51 = null;
    var field52 = null;
    var field53 = null;
    var field54 = null;
    var field4 = null;
    var field5 = null;
    var field6 = null;

    for (var i = 0; i < options.length; i++) {
        if (options[i][0] === value) {
            field11 = options[i][1];
            field12 = options[i][2];
            field13 = options[i][3];
            field2 = options[i][4];
            field3 = options[i][5];
            field51 = options[i][6];
            field52 = options[i][7];
            field53 = options[i][8];
            field54 = options[i][9];
            field4 = options[i][10];
            field5 = options[i][11];
            field6 = options[i][12];
            break;
        }
    }
    g11.glyph.y.field = field11;
    g12.glyph.y.field = field12;
    g13.glyph.y.field = field13;
    g2.glyph.y.field = field2;
    g3.glyph.y.field = field3;
    l1.upper.field = field51;
    l1.lower.field = field52;
    l3.glyph.y.field = field53;
    l4.glyph.y.field = field54;
    label_setmax.y.field = field54;
    g4.glyph.y.field = field4;
    g5.glyph.y.field = field6;
    g6.glyph.y.field = field5;

    p.title.text = value;
    source.change.emit();
    source1.change.emit();
    """

    callback = CustomJS(args=dict(g11=g11, g12=g12, g13=g13, g2=g2, g3=g3, g4=g4, g5=g5, g6=g6,
                                   l1=l1, l3=l3, l4=l4, source=source, source1=source1,
                                   select=select, options=menu_options, label_setmax=label_setmax, p=p),
                       code=code)
    select.js_on_change('value', callback)

    # 程序名称选择
    select2 = Select(title='program_name', value=c_opt[0], options=c_opt.tolist(), width=380)

    def selected_update(attr, old, new):
        print(f"选择程序: {select2.value}")
        nonlocal deft, x_tex
        deft = df[df['Name_C'] == select2.value].sort_values(by=['SNR_C', 'Time'])
        deft['sort'] = range(1, len(deft) + 1)

        source.data = deft
        line_plot.title.text = select2.value

        try:
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
            line_plot.x_range.factors = x_tex
            source1.data = Q
            print('更新完成')
        except Exception as e:
            print(f"错误: {e}")

    select2.on_change('value', selected_update)

    # 机器人名称输入
    table_input = TextInput(value=table_name, title="Enter Robot Name:", width=380)

    # 加载按钮
    load_button = Button(label="Load data", button_type="success", width=380)

    # 日期选择器
    date_range_picker = DateRangePicker(
        title="Select date range",
        value=((datetime.now().date() - timedelta(days=8)), datetime.now().date()),
        min_date=datetime.now().date() - timedelta(days=400),
        max_date=datetime.now().date() + timedelta(days=1),
        width=380,
    )

    def update():
        print('更新数据...')
        nonlocal df, deft, x_tex
        table_name_input = table_input.value
        start_time_input = date_range_picker.value[0]
        end_time_input = date_range_picker.value[1] + ' 23:59:59'

        try:
            query = f"SELECT TimeStamp2,ENERGY,LOSTENERGY FROM energy WHERE RobotName= '{table_name_input}' and TimeStamp2 BETWEEN '{start_time_input}' AND '{end_time_input}';"
            energy_new = pd.read_sql(query, engine)
            energy_new['TimeStamp2'] = pd.to_datetime(energy_new['TimeStamp2']) + timedelta(hours=8)
            energy_new['ENERGY'] = energy_new['ENERGY'].astype(float)
            energy_new['LOSTENERGY'] = energy_new['LOSTENERGY'].astype(float)
            energy_new = energy_new.sort_values(by='TimeStamp2', ascending=True)
            source3.data = energy_new
        except Exception as e:
            print(f"能量数据错误: {e}")
            source3.data = pd.DataFrame()

        try:
            p.title.text = database + '_' + table_name_input
            df_new = fetch_data_from_mysql(table_name_input, start_time_input, end_time_input, time_column, engine)

            columns_to_drop = ['A1_marker', 'A2_marker', 'A3_marker', 'A4_marker',
                               'A5_marker', 'A6_marker', 'A7_marker', 'SUB']
            for col in columns_to_drop:
                if col in df_new.columns:
                    del df_new[col]

            df_new['Time'] = pd.to_datetime(df_new['Timestamp']) + timedelta(hours=8)
            df_new['Timestamp'] = df_new['Time'].astype(str)
            df_new['SNR_C'] = df_new['SNR_C'].astype(int)
            for i in range(1, 8):
                col = f'AxisP{i}' if i < 7 else 'AxisP7'
                if col in df_new.columns:
                    df_new[col] = df_new[col].astype(float)

            c_opt_new = df_new['Name_C'].unique()
            select2.options = c_opt_new.tolist()

            df = df_new
            deft = df[df['Name_C'] == c_opt_new[0]].sort_values(by=['SNR_C', 'Time'])
            deft['sort'] = range(1, len(deft) + 1)

            line_plot.title.text = deft['Name_C'].iloc[0]
            source.data = deft

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
            line_plot.x_range.factors = x_tex
            source1.data = Q
            print('加载完成')
        except Exception as e:
            print(f"错误: {e}")

    load_button.on_click(update)

    # 布局
    widgets1 = column(table_input, date_range_picker, load_button, select2, select, EnergyP,
                      sizing_mode="stretch_height", height=1000, width=400)
    widgets2 = column(line_plot, p, p2, p1, p3, p4, p5, sizing_mode="stretch_both", height=1000, width=1400)

    doc.add_root(row(widgets2, widgets1, sizing_mode="stretch_both"))


# 为bokeh serve创建入口
def main():
    from bokeh.server.server import Server

    server = Server({'/': bkapp}, port=5006)
    server.start()
    print('Bokeh服务已启动: http://localhost:5006/')
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()


if __name__ == '__main__':
    main()
