from bokeh.plotting import figure, show
import pandas as pd
from bokeh.transform import factor_cmap
from bokeh.models import ColumnDataSource, TextInput, Button, DataTable, TableColumn,HoverTool,Select, DateRangePicker,CustomJS,LabelSet,BoxAnnotation,LassoSelectTool,Band
#from bokeh.client import push_session
from datetime import datetime,timedelta
from sqlalchemy import create_engine
from bokeh.io import curdoc
from bokeh.layouts import layout,row,column
from bokeh.server.server import Server
#from bokeh.util.browser import get_browser WebBrowser
#from
def fetch_data_from_mysql(table_name, start_time, end_time, time_column):
        # 创建数据库连接
       
        
        # 编写SQL查询
    query = f"SELECT * FROM `{table_name}` WHERE `{time_column}` BETWEEN '{start_time}' AND '{end_time}';"
        
        # 使用pandas读取数据
    df = pd.read_sql(query, engine)
        
    return df


def bkapp(doc):
    global database
    global engine
    global df
    global deft,x_tex
    global energy
    #########################################################数据下载##########################################################
    # 定义一个函数，连接数据库，获取数据，并使用Bokeh生成图表

    # 数据库连接参数
    user =
    password =
    host =
    port =
    database =

    # 初始化数据源
    #source = ColumnDataSource(data=dict())

    table_name = 'HC21_050RB_300'
    start_time = datetime.now()-timedelta(days=7)
    end_time = datetime.now()
    #start_time = '2024-12-16 00:00:00'
    #end_time = '2024-12-20 00:00:00'
    time_column = 'Timestamp'
    #value_column = 'your_value_column'
    engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

    df= fetch_data_from_mysql(table_name, start_time, end_time, time_column)
    print(start_time)
    print(end_time)
    ###########################energy 数据获取##########################
    query = f"SELECT TimeStamp2,ENERGY,LOSTENERGY FROM energy WHERE RobotName= '{table_name}'and TimeStamp2 BETWEEN '{start_time}' AND '{end_time}';"
    energy =pd.read_sql(query, engine)



    ###########################################数据处理################################################################################
    #################################energy数据###############################
    energy['TimeStamp2']=pd.to_datetime(energy['TimeStamp2'])+timedelta(hours=8)
    energy['ENERGY']=energy['ENERGY'].astype(float)
    energy['LOSTENERGY']=energy['LOSTENERGY'].astype(float)
    energy=energy.sort_values(by='TimeStamp2', ascending=True)
    source3= ColumnDataSource(energy)

    ###################################其它##################################

    del df['A1_marker'],df['A2_marker'],df['A3_marker'],df['A4_marker'],df['A5_marker'],df['A6_marker'],df['A7_marker'],df['SUB']
    #数据去重
    df=df.drop_duplicates()
    
    df['Time']=pd.to_datetime(df['Timestamp'])+timedelta(hours=8)
    df['Timestamp']=df['Time'].astype(str)
    df['SNR_C']=df['SNR_C'].astype(int)
    df['AxisP1']=df['AxisP1'].astype(float)
    df['AxisP2']=df['AxisP2'].astype(float)
    df['AxisP3']=df['AxisP3'].astype(float)
    df['AxisP4']=df['AxisP4'].astype(float)
    df['AxisP5']=df['AxisP5'].astype(float)
    df['AxisP6']=df['AxisP6'].astype(float)
    df['AxisP7']=df['AxisP7'].astype(float)
    #df['AxisP4']=df['AxisP4'].astype(float)
    #print(df.dtypes)
    print(len(df))
    #select 
    c_opt=df['Name_C'].unique()
    #select2=Select(title='program_name',value=c_opt[0],options=c_opt.tolist())

    #strat with
    deft=df[df['Name_C']==c_opt[0]]
    deft=deft.sort_values(by=['SNR_C','Time'])
    deft['sort']=range(1,len(deft)+1)
    source=ColumnDataSource(deft)

    #创建数据源source1
    ref = deft.groupby('SNR_C')[['MAXCurr_A1','MAXCurr_A2','MAXCurr_A3','MAXCurr_A4','MAXCurr_A5','MAXCurr_A6','MAXCurr_E1',
                'MinCurr_A1','MinCurr_A2', 'MinCurr_A3','MinCurr_A4','MinCurr_A5','MinCurr_A6','MinCurr_E1']].last()
    #print(ref)
    x_tex = deft["SNR_C"].sort_values(ascending=True).unique().astype(str)
    #Q2=df.groupby('SNR_C').quantile(q=0.02,interpolation='nearest')
    LQ = deft.groupby('SNR_C')[['Curr_A1','Curr_A2','Curr_A3','Curr_A4','Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.01, interpolation='nearest').rename(
            columns={'Curr_A1': 'Curr_A1_LQ', 'Curr_A2': 'Curr_A2_LQ', 'Curr_A3': 'Curr_A3_LQ', 'Curr_A4': 'Curr_A4_LQ',
                     'Curr_A5': 'Curr_A5_LQ', 'Curr_A6': 'Curr_A6_LQ', 'Curr_E1': 'Curr_E1_LQ'})
    HQ = deft.groupby('SNR_C')[['Curr_A1','Curr_A2','Curr_A3','Curr_A4','Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.99, interpolation='nearest').rename(
             columns={'Curr_A1': 'Curr_A1_HQ', 'Curr_A2': 'Curr_A2_HQ', 'Curr_A3': 'Curr_A3_HQ', 'Curr_A4': 'Curr_A4_HQ',
                     'Curr_A5': 'Curr_A5_HQ', 'Curr_A6': 'Curr_A6_HQ', 'Curr_E1': 'Curr_E1_HQ'})

    labeltext = deft.groupby('SNR_C')['P_name'].last()

    Q = pd.merge(pd.merge(pd.merge(LQ, HQ,left_on=['SNR_C'],right_index=True,how='outer'),ref,left_on=['SNR_C'],right_index=True,how='inner'),labeltext,left_on=['SNR_C'],right_index=True,how='inner').reset_index()
    Q["SNR_C"]=x_tex
    source1 = ColumnDataSource(Q)
    ##########################################################画图###################################################################################

    hover=HoverTool(tooltips=[
                             ('Timestamp','@Timestamp'),
                             ('Curr_A1','@Curr_A1'),
                             ('SNR_C','@SNR_C'),
                             ('P_name','@P_name')
                             ],
                    #mode="vline"
                  )
    hover1=HoverTool(tooltips=[
                             ('Timestamp','@Timestamp'),
                             ('Tem_1','@Tem_1'),
                             ('SNR_C','@SNR_C'),
                             ('P_name','@P_name')
                             ],
                    #mode="vline"
                  )
    hover2=HoverTool(tooltips=[
                             ('Timestamp','@Timestamp'),
                             ('Torque1','@Torque1'),
                             ('SNR_C','@SNR_C'),
                             ('P_name','@P_name')
                             ],
                    #mode="vline"
                  )
    hover3=HoverTool(tooltips=[
                             ('Timestamp','@Timestamp'),
                             ('Fol1','@Fol1'),
                             ('SNR_C','@SNR_C'),
                             ('P_name','@P_name')
                             ],
                    #mode="vline"
                  )
    hover4=HoverTool(tooltips=[
                             ('Timestamp','@Timestamp'),
                             ('Speed1','@Speed1'),
                             ('SNR_C','@SNR_C'),
                             ('P_name','@P_name')
                             ],
                    #mode="vline"
                  )
    hover5=HoverTool(tooltips=[
                             ('Timestamp','@Timestamp'),
                             ('AxisP1','@AxisP1'),
                             ('SNR_C','@SNR_C'),
                             ('P_name','@P_name')
                             ],
                    #mode="vline"
                  )
    ###############################三联图################################    

    p = figure(
        #x_range=group,
        #x_axis_type="datetime",
        #x_range=FactorRange(factors=deft['x_lables'].unique()),
        #y_range=(-102,102),
        title='A1',
        #sizing_mode="stretch_both",
        sizing_mode="stretch_width",
        width=1400,
        #max_width=1000,
        height=190,
        x_axis_label='motion_time',
        y_axis_label='Current1 Percentage %',
        output_backend='webgl'
        #tools=[hover]
    )
    p.xaxis.visible=False
    g11=p.step(x='sort', y='MinCurr_A1', source=source,line_width=2, mode="center",color='red')
    g12=p.step(x='sort', y='MAXCurr_A1', source=source,line_width=2, mode="center",color='red')
    #p.line(x='sort',y='Curr_A1', source=source,line_width=2,line_color=index_cmap )

    g13=p.scatter(x='sort',y='Curr_A1', source=source,size=3,alpha=0.7)#,fill_color=index_cmap)
    #p.xaxis.major_label_orientation = 1
    p.add_tools(hover)
    p.add_tools(LassoSelectTool())

    p2=figure(
        x_range=p.x_range,
        #x_axis_type="datetime",
        #x_range=FactorRange(factors=deft['x_lables'].unique()),
        y_range=(15,100),
        #title="Axis_position",
        #sizing_mode="stretch_both",
        sizing_mode="stretch_width",
        width=1400,
        #max_width=1000,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='Temperature',
        output_backend='webgl'
        #tools=[hover]
    )
    g2=p2.scatter(x='sort',y='Tem_1', source=source,size=3,color='orange')#line_width=2)
    p2.xaxis.visible=False
    p2.add_tools(hover1)

    p1=figure(
        x_range=p.x_range,
        #x_range=group,
        #x_axis_type="datetime",
        #x_range=FactorRange(factors=deft['x_lables'].unique()),
        #y_range=source.data['AxisP1'],
        #title="Axis_position",
        sizing_mode="stretch_width",
        #sizing_mode="stretch_both",
        width=1400,
        #max_width=1000,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='Axis_position',
        output_backend='webgl'

        #tools=[hover]
    )
    g3=p1.scatter(x='sort',y='AxisP1', source=source,size=3,color='green')
    p1.xaxis.visible=False
    p1.add_tools(hover5)

    p3=figure(
        x_range=p.x_range,
        #x_range=group,
        #x_axis_type="datetime",
        #x_range=FactorRange(factors=deft['x_lables'].unique()),
        #y_range=source.data['AxisP1'],
        #title="Axis_position",
        sizing_mode="stretch_width",
        #sizing_mode="stretch_both",
        width=1400,
        #max_width=1000,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='mortor speed',
        output_backend='webgl'

        #tools=[hover4]
    )
    g4=p3.scatter(x='sort',y='Speed1', source=source,size=3,color='blue')
    p3.xaxis.visible=False
    p3.add_tools(hover4)

    p4=figure(
        x_range=p.x_range,
        #sizing_mode="stretch_both",
        #x_range=group,
        #x_axis_type="datetime",
        #x_range=FactorRange(factors=deft['x_lables'].unique()),
        #y_range=source.data['AxisP1'],
        #title="Axis_position",
        sizing_mode="stretch_width",
        width=1400,
        #max_width=1000,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='Following error',
        output_backend='webgl'

        #tools=[hover]
    )
    g5=p4.scatter(x='sort',y='Fol1', source=source,size=3,color='lime')
    p4.xaxis.visible=False
    p4.add_tools(hover3)

    p5=figure(
        x_range=p.x_range,
        #x_range=group,
        #x_axis_type="datetime",
        #x_range=FactorRange(factors=deft['x_lables'].unique()),
        #y_range=source.data['AxisP1'],
        #title="Axis_position",
        sizing_mode="stretch_width",
        #sizing_mode="stretch_both",
        width=1400,
        #max_width=1000,
        height=110,
        x_axis_label='motion_time',
        y_axis_label='Torque',
        output_backend='webgl'

        #tools=[hover]
    )
    g6=p5.scatter(x='sort',y='Torque1', source=source,size=3,color='sienna')
    p5.xaxis.visible=False   
    p5.add_tools(hover2)

    #######################################聚合图#######################################

    line_plot = figure(title=source.data['Name_C'][0], sizing_mode="stretch_width",width=1400, height=200,x_range=x_tex,y_range=p.y_range)
    # 最大值
    #l1=line_plot.line(x="SNR_C", y='MAXCurr_A1', source=source1, line_color="red", line_width=2)


    #lmax = line_plot.scatter(x="x1", y="y1", source=line_source, size=8, color="blue", alpha=0.6)
    # 添加鼠标悬停工具到折线图
    #l2=line_plot.line(x="SNR_C", y="MinCurr_A1", source=source1, line_color="red", line_width=2, legend_label="Curr_ref")

    l3=line_plot.line(x="SNR_C", y="Curr_A1_LQ", source=source1, line_color="blue", line_width=2, legend_label="Curr_min",alpha=1)
    l4=line_plot.line(x="SNR_C", y="Curr_A1_HQ", source=source1, line_color="orange", line_width=2, legend_label="Curr_max",alpha=1)
    l1 = Band(base="SNR_C", lower="MinCurr_A1", upper="MAXCurr_A1", source=source1,
                fill_alpha=0.3, fill_color="green", line_color="red")
    line_plot.add_layout(l1)

    label_setmax = LabelSet(x="SNR_C", y='Curr_A1_HQ', text='P_name', level='glyph', x_offset=3, y_offset=3, source=source1,text_font_size='7pt',angle=0,text_font_style='bold')
    line_plot.add_layout(label_setmax, 'center')

    hover_line = HoverTool(
       tooltips=[
           ("SNR_C", "@SNR_C"),
           #("MAXCurr_A1", "@MAXCurr_A1"),
           ("P_name", "@P_name")
       ],
       mode="vline",  # 悬停时显示垂直线上的点信息,
       #renderers=[lmax]
    )
    line_plot.add_tools(hover_line)
    line_plot.legend.location='bottom'
    line_plot.legend.orientation='horizontal'
    line_plot.legend.label_text_font_size='7pt'
    line_plot.xaxis.major_label_orientation = 1.5

    ################################加box###########################################

    low_box = BoxAnnotation(top=-90, fill_alpha=0.2, fill_color='#D55E00')
    high_box = BoxAnnotation(bottom=90, fill_alpha=0.2, fill_color='#D55E00')
    #p.add_layout(low_box)
    #p.add_layout(high_box)
    line_plot.add_layout(low_box)
    line_plot.add_layout(high_box)

    ###############################Energy###############################################
    EnergyP=figure(
        #x_range=group,
        x_axis_type="datetime",
        #x_range=FactorRange(factors=deft['x_lables'].unique()),
        #y_range=(-102,102),
        title='Energy',
        sizing_mode="stretch_both",
        #sizing_mode="scale_both",
        width=500,
        #max_width=1000,
        height=700,
        x_axis_label='Time',
        y_axis_label='Energy (kWh)',
        output_backend='webgl'
        #tools=[hover]
    )
    E1=EnergyP.line(x="TimeStamp2", y="ENERGY", source=source3, line_color="orange", line_width=2, legend_label="Energy",alpha=1)
    E2=EnergyP.line(x="TimeStamp2", y="LOSTENERGY", source=source3, line_color="yellow", line_width=2, legend_label="Lost_Energy",alpha=1)
    EnergyP.legend.location = 'top_left'
    #print(energy)
#l3=line_plot.line(x="SNR_C", y="Curr_A1_LQ", source=source1, line_color="blue", line_width=2, legend_label="Curr_min",alpha=1)
    #################################小部件##############################################

    ############################JS_回调#######################
    # 创建下拉菜单选项与数据源列名的映射
    menu_options = [("A1", "MinCurr_A1",'MAXCurr_A1','Curr_A1','Tem_1','AxisP1','MAXCurr_A1','MinCurr_A1','Curr_A1_LQ','Curr_A1_HQ','Speed1','Torque1','Fol1'), 
                    ("A2", "MinCurr_A2",'MAXCurr_A2','Curr_A2','Tem_2','AxisP2','MAXCurr_A2','MinCurr_A2','Curr_A2_LQ','Curr_A2_HQ','Speed2','Torque2','Fol2'),
                    ("A3", "MinCurr_A3",'MAXCurr_A3','Curr_A3','Tem_3','AxisP3','MAXCurr_A3','MinCurr_A3','Curr_A3_LQ','Curr_A3_HQ','Speed3','Torque3','Fol3'), 
                    ("A4", "MinCurr_A4",'MAXCurr_A4','Curr_A4','Tem_4','AxisP4','MAXCurr_A4','MinCurr_A4','Curr_A4_LQ','Curr_A4_HQ','Speed4','Torque4','Fol4'),
                    ("A5", "MinCurr_A5",'MAXCurr_A5','Curr_A5','Tem_5','AxisP5','MAXCurr_A5','MinCurr_A5','Curr_A5_LQ','Curr_A5_HQ','Speed5','Torque5','Fol5'),
                    ("A6", "MinCurr_A6",'MAXCurr_A6','Curr_A6','Tem_6','AxisP6','MAXCurr_A6','MinCurr_A6','Curr_A6_LQ','Curr_A6_HQ','Speed6','Torque6','Fol6'), 
                    ("A7", "MinCurr_E1",'MAXCurr_E1','Curr_E1','Tem_7','AxisP7','MAXCurr_E1','MinCurr_E1','Curr_E1_LQ','Curr_E1_HQ','Speed7','Torque7','Fol7'),

                    ]

    # 创建下拉菜单
    #select = Select(title="Y-Axis Option:", value="Option 1", options=[item[0] for item in menu_options])
    select=Select(title='Axis select',value='A1',options=['A1','A2','A3','A4','A5','A6','A7'],width=380)
    #print(dir(p1))
    #select.js_link('value', P1.glyph,'y.field')
    # 定义回调函数
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
            field51=options[i][6];
            field52=options[i][7];
            field53=options[i][8];
            field54=options[i][9];
            field4= options[i][10];
            field5= options[i][11];
            field6= options[i][12];
            break;
        }
    }
    // 更新所有图表的y字段
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
    hover.tooltips=[['Timestamp','@Timestamp'],[field13,'@'+field13],['SNR_C','@SNR_C'],['P_name','@P_name']];
    hover1.tooltips=[['Timestamp','@Timestamp'],[field2,'@'+field2],['SNR_C','@SNR_C'],['P_name','@P_name']];
    hover2.tooltips=[['Timestamp','@Timestamp'],[field5,'@'+field5],['SNR_C','@SNR_C'],['P_name','@P_name']];
    hover3.tooltips=[['Timestamp','@Timestamp'],[field6,'@'+field6],['SNR_C','@SNR_C'],['P_name','@P_name']];
    hover4.tooltips=[['Timestamp','@Timestamp'],[field4,'@'+field4],['SNR_C','@SNR_C'],['P_name','@P_name']];
    hover5.tooltips=[['Timestamp','@Timestamp'],[field3,'@'+field3],['SNR_C','@SNR_C'],['P_name','@P_name']];   
    source.change.emit();
    source1.change.emit();
    """

    callback = CustomJS(args=dict(g11=g11, g12=g12,g13=g13,g2=g2,g3=g3,g4=g4,g5=g5,g6=g6,l1=l1,l3=l3,l4=l4,source=source,source1=source1, select=select, options=menu_options,hover=hover,
                        hover1=hover1,hover2=hover2,hover3=hover3,hover4=hover4,hover5=hover5,label_setmax=label_setmax,p=p), code=code)

    # 将下拉菜单的值改变事件与回调函数关联
    select.js_on_change('value', callback)

    #####################################serve 回调#######################################
    #select 

    select2=Select(title='program_name',value=c_opt[0],options=c_opt.tolist(),width=380)
    '''
    #数据库选择
    menu = {'MRA':"mra_show_data", 
            "MFA": "mfa_show_data",
            "AS": "as_show_data", 
            "ShunYi": "SY_show_data",
            "Engine": "pt_show_data"}
                    
    select1=Select(title='Plant',value='MRA',options=['MRA','MFA','AS','ShunYi','Engine'])
    '''

    def selected_update():
        global df
        global deft,x_tex
        print(select2.value)
        deft=df[df['Name_C']==select2.value]
        deft=deft.sort_values(by=['SNR_C','Time'])
        deft['sort']=range(1,len(deft)+1)
        #print(deft.dtypes)
        
        print(len(deft))
        #print(deft['Name_C'][0])
        source.data=deft
        line_plot.title.text = select2.value
        #line_plot.title.text = deft['Name_C'][0]
        
        try:
            #line_plot.title.text = deft['Name_C'][0]
            #source.data=deft

            #创建数据源source1
            ref = deft.groupby('SNR_C')[['MAXCurr_A1','MAXCurr_A2','MAXCurr_A3','MAXCurr_A4','MAXCurr_A5','MAXCurr_A6','MAXCurr_E1',
                        'MinCurr_A1','MinCurr_A2', 'MinCurr_A3','MinCurr_A4','MinCurr_A5','MinCurr_A6','MinCurr_E1']].last()
            #print(ref)
            x_tex = deft["SNR_C"].sort_values(ascending=True).unique().astype(str)
            #Q2=df.groupby('SNR_C').quantile(q=0.02,interpolation='nearest')
            LQ = deft.groupby('SNR_C')[['Curr_A1','Curr_A2','Curr_A3','Curr_A4','Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.01, interpolation='nearest').rename(
                    columns={'Curr_A1': 'Curr_A1_LQ', 'Curr_A2': 'Curr_A2_LQ', 'Curr_A3': 'Curr_A3_LQ', 'Curr_A4': 'Curr_A4_LQ',
                             'Curr_A5': 'Curr_A5_LQ', 'Curr_A6': 'Curr_A6_LQ', 'Curr_E1': 'Curr_E1_LQ'})
            HQ = deft.groupby('SNR_C')[['Curr_A1','Curr_A2','Curr_A3','Curr_A4','Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.99, interpolation='nearest').rename(
                     columns={'Curr_A1': 'Curr_A1_HQ', 'Curr_A2': 'Curr_A2_HQ', 'Curr_A3': 'Curr_A3_HQ', 'Curr_A4': 'Curr_A4_HQ',
                             'Curr_A5': 'Curr_A5_HQ', 'Curr_A6': 'Curr_A6_HQ', 'Curr_E1': 'Curr_E1_HQ'})

            labeltext = deft.groupby('SNR_C')['P_name'].last()

            Q = pd.merge(pd.merge(pd.merge(LQ, HQ,left_on=['SNR_C'],right_index=True,how='outer'),ref,left_on=['SNR_C'],right_index=True,how='inner'),labeltext,left_on=['SNR_C'],right_index=True,how='inner').reset_index()
            Q["SNR_C"]=x_tex
            #line_plot.title.text = 
            line_plot.x_range.factors=x_tex
            source1.data = Q
            curdoc().add_next_tick_callback(lambda:None)
            print('finish')
        except Exception as e:
            print(f"Error: {e}")

    select2.on_change('value', lambda attr, old, new: selected_update())





    # 创建文本输入部件
    table_input = TextInput(value=table_name, title="Enter Robot Name:",width=380)

    # 创建按钮
    load_button = Button(label="Load data", button_type="success",width=380)

    #时间选择
    date_range_picker = DateRangePicker(
        title="Select date range",
        value=((datetime.now().date()-timedelta(days=8)),datetime.now().date()),
        min_date=datetime.now().date()-timedelta(days=400),
        max_date=datetime.now().date()+timedelta(days=1),
        #sizing_mode="scale_both",
        width=380,
    )
                      

    # 更新函数，根据输入的表名更新数据源
    #def update(attrname, old, new):
    def update():
        print('up date now')
        global database
        global engine
        global df
        global deft,x_tex
        database = 'showdata'
        table_name = table_input.value
        #format_string = "%Y-%m-%d %H:%M:%S"
        start_time = date_range_picker.value[0]
        end_time = date_range_picker.value[1] +' 23:59:59'

        #end_time=datetime.strptime(end_time,format_string)
        time_column = 'Timestamp'

        try:    
            query = f"SELECT TimeStamp2,ENERGY,LOSTENERGY FROM energy WHERE RobotName= '{table_name}'and TimeStamp2 BETWEEN '{start_time}' AND '{end_time}';"
            energy =pd.read_sql(query, engine)
            energy['TimeStamp2']=pd.to_datetime(energy['TimeStamp2'])+timedelta(hours=8)
            energy['ENERGY']=energy['ENERGY'].astype(float)
            energy['LOSTENERGY']=energy['LOSTENERGY'].astype(float)
            energy=energy.sort_values(by='TimeStamp2', ascending=True)
            source3.data= energy
        except Exception as e:
            print(f"Error: {e}")
            source3.data=pd.DataFrame()
        
        try:
            # 从数据库读取数据
            p.title.text =database +'_'+ table_name
            engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')
            df= fetch_data_from_mysql(table_name, start_time, end_time, time_column)
            print(end_time)
            ##########数据处理##############
            del df['A1_marker'],df['A2_marker'],df['A3_marker'],df['A4_marker'],df['A5_marker'],df['A6_marker'],df['A7_marker'],df['SUB']
            df['Time']=pd.to_datetime(df['Timestamp'])+timedelta(hours=8)
            df['Timestamp']=df['Time'].astype(str)
            df['SNR_C']=df['SNR_C'].astype(int)
            df['AxisP1']=df['AxisP1'].astype(float)
            df['AxisP2']=df['AxisP2'].astype(float)
            df['AxisP3']=df['AxisP3'].astype(float)
            df['AxisP4']=df['AxisP4'].astype(float)
            df['AxisP5']=df['AxisP5'].astype(float)
            df['AxisP6']=df['AxisP6'].astype(float)
            df['AxisP7']=df['AxisP7'].astype(float)
            #df['AxisP4']=df['AxisP4'].astype(float)
            #print(df.dtypes)
            c_opt=df['Name_C'].unique()
            select2.options=c_opt.tolist()
            #strat with
            deft=df[df['Name_C']==c_opt[0]]
            deft=deft.sort_values(by=['SNR_C','Time'])
            deft['sort']=range(1,len(deft)+1)
            #source=ColumnDataSource(deft)
            #print(c_opt)
            line_plot.title.text = deft['Name_C'][0]
            source.data=deft

            #创建数据源source1
            ref = deft.groupby('SNR_C')[['MAXCurr_A1','MAXCurr_A2','MAXCurr_A3','MAXCurr_A4','MAXCurr_A5','MAXCurr_A6','MAXCurr_E1',
                        'MinCurr_A1','MinCurr_A2', 'MinCurr_A3','MinCurr_A4','MinCurr_A5','MinCurr_A6','MinCurr_E1']].last()
            #print(ref)
            x_tex = deft["SNR_C"].sort_values(ascending=True).unique().astype(str)
            #Q2=df.groupby('SNR_C').quantile(q=0.02,interpolation='nearest')
            LQ = deft.groupby('SNR_C')[['Curr_A1','Curr_A2','Curr_A3','Curr_A4','Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.01, interpolation='nearest').rename(
                    columns={'Curr_A1': 'Curr_A1_LQ', 'Curr_A2': 'Curr_A2_LQ', 'Curr_A3': 'Curr_A3_LQ', 'Curr_A4': 'Curr_A4_LQ',
                             'Curr_A5': 'Curr_A5_LQ', 'Curr_A6': 'Curr_A6_LQ', 'Curr_E1': 'Curr_E1_LQ'})
            HQ = deft.groupby('SNR_C')[['Curr_A1','Curr_A2','Curr_A3','Curr_A4','Curr_A5','Curr_A6','Curr_E1']].quantile(q=0.99, interpolation='nearest').rename(
                     columns={'Curr_A1': 'Curr_A1_HQ', 'Curr_A2': 'Curr_A2_HQ', 'Curr_A3': 'Curr_A3_HQ', 'Curr_A4': 'Curr_A4_HQ',
                             'Curr_A5': 'Curr_A5_HQ', 'Curr_A6': 'Curr_A6_HQ', 'Curr_E1': 'Curr_E1_HQ'})

            labeltext = deft.groupby('SNR_C')['P_name'].last()

            Q = pd.merge(pd.merge(pd.merge(LQ, HQ,left_on=['SNR_C'],right_index=True,how='outer'),ref,left_on=['SNR_C'],right_index=True,how='inner'),labeltext,left_on=['SNR_C'],right_index=True,how='inner').reset_index()
            Q["SNR_C"]=x_tex
            #line_plot.title.text = 
            line_plot.x_range.factors=x_tex
            source1.data = Q

            #source1.data["SNR_C"] = x_tex
            curdoc().add_next_tick_callback(lambda:None)
            print('finish')
        except Exception as e:
            print(f"Error: {e}")

    #table_input.on_change('value', update)
    # 将按钮点击事件与更新函数绑定
    load_button.on_click(update)
    # 创建布局
    #layout = layout([table_input, load_button,select], [p])
    #layout=layout([select1,table_input,date_range_picker, load_button,select2,select],[line_plot],[p],[p2],[p1])
    #layout=columns
    #show(layout)
    #layout = layout([select1,table_input,date_range_picker, load_button,select2], [p])
    #curdoc().add_root(layout)
    #doc.add_root(layout([select1,table_input,date_range_picker, load_button,select2,select],[line_plot],[p],[p2],[p1],[p3],[p4],[p5]))
    #widgets1 = column(table_input,date_range_picker, load_button,select2,select,sizing_mode="fixed", height=500, width=500)
    #widgets1_1=layout([None,widgets1],[EnergyP],sizing_mode="fixed", height=1000, width=500)
    widgets1 = column(table_input,date_range_picker, load_button,select2,select, EnergyP,sizing_mode="stretch_height", height=1000, width=400)
    #widgets1 = column(table_input,date_range_picker, load_button,select2,select, EnergyP,sizing_mode="scale_both", height=1000, width=500)
    widgets2=column(line_plot,p,p2,p1,p3,p4,p5,sizing_mode="stretch_both", height=1000, width=1400)

    doc.add_root(row(widgets2,widgets1,sizing_mode="stretch_both"))
    #doc.application_context.serve.allow_websocket_origin='*'

server = Server({'/': bkapp}, port=5008)
server.start()

if __name__ == '__main__':
    print('Opening Bokeh application on http://localhost:5008/')

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()