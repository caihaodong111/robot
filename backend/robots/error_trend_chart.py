"""
机器人关节错误率趋势图生成模块
从 CSV 文件读取数据并生成 matplotlib 图表
"""
import os
import matplotlib
matplotlib.use('Agg')  # 使用非 GUI 后端，避免多线程问题
import pandas as pd
import matplotlib.pyplot as plt
from django.conf import settings


# CSV 数据文件存储路径
ERROR_RATE_PATH = getattr(settings, 'ERROR_RATE_CSV_PATH', 'P:/')

# 图表保存路径
CHART_OUTPUT_PATH = getattr(settings, 'ERROR_RATE_CHART_PATH', 'P:/PIC/')


def generate_trend_chart(robot_part_no: str, axis_num: int) -> str:
    """
    生成机器人关节错误率趋势图

    Args:
        robot_part_no: 机器人部件编号 (如 as33_020rb_400)
        axis_num: 关节编号 (1-7)

    Returns:
        str: 生成的图片文件路径

    Raises:
        FileNotFoundError: CSV 文件不存在
        ValueError: 参数错误
    """
    if axis_num < 1 or axis_num > 7:
        raise ValueError(f"axis_num 必须在 1-7 之间，当前值: {axis_num}")

    # 构建 CSV 文件路径
    csv_filename = f'{robot_part_no}-error-rate-trend.csv'
    csv_path = os.path.join(ERROR_RATE_PATH, csv_filename)

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV 文件不存在: {csv_path}")

    # 读取并预处理数据
    data = pd.read_csv(csv_path)
    data = data.loc[data['count'] >= data['count'].mean() / 2]

    if 'reference' in data.columns:
        ref = data['reference'].iloc[-1]
        data = data[data['reference'] == ref]

    data['Timestamp'] = pd.to_datetime(data['Timestamp'])

    # 生成图表
    return _draw_chart(axis_num, data, robot_part_no)


def _draw_chart(n: int, data: pd.DataFrame, robot: str) -> str:
    """
    绘制单个关节的多参数趋势图

    Args:
        n: 关节编号 (1-7)
        data: 预处理后的数据
        robot: 机器人部件编号

    Returns:
        str: 保存的图片文件路径
    """
    # 关节数据映射配置
    axis_config = {
        1: {'q': 'Q1', 'e_rate': 'A1_e_rate', 'rms': 'A1_Rms',
            'curr_max': 'Curr_A1_max', 'curr_min': 'Curr_A1_min', 'temp': 'tem1_m'},
        2: {'q': 'Q2', 'e_rate': 'A2_e_rate', 'rms': 'A2_Rms',
            'curr_max': 'Curr_A2_max', 'curr_min': 'Curr_A2_min', 'temp': 'tem2_m'},
        3: {'q': 'Q3', 'e_rate': 'A3_e_rate', 'rms': 'A3_Rms',
            'curr_max': 'Curr_A3_max', 'curr_min': 'Curr_A3_min', 'temp': 'tem3_m'},
        4: {'q': 'Q4', 'e_rate': 'A4_e_rate', 'rms': 'A4_Rms',
            'curr_max': 'Curr_A4_max', 'curr_min': 'Curr_A4_min', 'temp': 'tem4_m'},
        5: {'q': 'Q5', 'e_rate': 'A5_e_rate', 'rms': 'A5_Rms',
            'curr_max': 'Curr_A5_max', 'curr_min': 'Curr_A5_min', 'temp': 'tem5_m'},
        6: {'q': 'Q6', 'e_rate': 'A6_e_rate', 'rms': 'A6_Rms',
            'curr_max': 'Curr_A6_max', 'curr_min': 'Curr_A6_min', 'temp': 'tem6_m'},
        7: {'q': 'Q7', 'e_rate': 'A7_e_rate', 'rms': 'A7_Rms',
            'curr_max': 'Curr_A7_max', 'curr_min': 'Curr_A7_min', 'temp': 'tem7_m'},
    }

    config = axis_config.get(n)
    if not config:
        raise ValueError(f"不支持的关节编号: {n}")

    # 选择需要的列
    columns = ['Timestamp', 'error1_c1',
               config['temp'], config['e_rate'], config['rms'], config['q'],
               config['curr_max'], config['curr_min']]
    plot_data = data[columns]

    # 创建图表
    fig = plt.figure(figsize=(10, 15))
    gs = fig.add_gridspec(7, 1, height_ratios=[1, 1, 1, 1, 1, 1, 1])

    axes = [fig.add_subplot(gs[i]) for i in range(7)]

    # 配置颜色和标签
    color_map = {
        'q': 'tab:blue',
        'e_rate': 'tab:orange',
        'rms': 'tab:green',
        'curr_min': 'tab:pink',
        'curr_max': 'yellow',
        'temp': 'tab:red',
        'error': 'tab:red'
    }

    label_map = {
        'q': config['q'],
        'e_rate': f'A{n}_e_rate',
        'rms': f'A{n}_Rms',
        'curr_min': 'Min',
        'curr_max': 'Max',
        'temp': f'T{n}',
        'error': 'error'
    }

    # 绘制各子图
    plot_configs = [
        (0, config['q'], 'q'),
        (1, config['e_rate'], 'e_rate'),
        (2, config['rms'], 'rms'),
        (3, config['curr_min'], 'curr_min'),
        (4, config['curr_max'], 'curr_max'),
        (5, config['temp'], 'temp'),
        (6, 'error1_c1', 'error'),
    ]

    for idx, (ax_idx, column, key) in enumerate(plot_configs):
        ax = axes[ax_idx]
        ax.scatter(plot_data['Timestamp'], plot_data[column],
                   c=color_map[key], s=5, alpha=1)

        if idx < 6:
            ax.xaxis.set_visible(False)

        if idx == 6:
            ax.set_xlabel('Timestamp')
        else:
            ax.set_ylabel(label_map[key])

    # 调整布局
    fig.subplots_adjust(hspace=0)
    plt.xticks(rotation='vertical')

    # 确保输出目录存在
    os.makedirs(CHART_OUTPUT_PATH, exist_ok=True)

    # 保存图片
    output_filename = f'{robot}_{n}_trend.png'
    output_path = os.path.join(CHART_OUTPUT_PATH, output_filename)
    fig.savefig(output_path, dpi=80, bbox_inches='tight')
    plt.close(fig)

    return output_path


def chart_exists(robot_part_no: str, axis_num: int) -> bool:
    """
    检查图表文件是否已存在

    Args:
        robot_part_no: 机器人部件编号
        axis_num: 关节编号 (1-7)

    Returns:
        bool: 图表是否存在
    """
    filename = f'{robot_part_no}_{axis_num}_trend.png'
    path = os.path.join(CHART_OUTPUT_PATH, filename)
    return os.path.exists(path)
