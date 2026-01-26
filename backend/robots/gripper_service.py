"""
关键轨迹检查服务模块
集成到Django架构中，使用.env数据库配置
"""
import os
import csv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from django.conf import settings
from dotenv import load_dotenv
import traceback

# 加载环境变量
load_dotenv()


def get_db_engine():
    """
    从.env或Django settings获取数据库配置并创建SQLAlchemy引擎
    支持两种配置方式：
    1. Django settings (DATABASES)
    2. .env文件 (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    """
    # 优先使用Django settings
    if hasattr(settings, 'DATABASES') and 'default' in settings.DATABASES:
        db_config = settings.DATABASES['default']
        user = db_config.get('USER', os.getenv('DB_USER', 'root'))
        password = db_config.get('PASSWORD', os.getenv('DB_PASSWORD', ''))
        host = db_config.get('HOST', os.getenv('DB_HOST', 'localhost'))
        port = db_config.get('PORT', os.getenv('DB_PORT', '3306'))
        database = db_config.get('NAME', os.getenv('DB_NAME', 'showdata'))
    else:
        # 使用.env配置
        user = os.getenv('DB_USER', 'root')
        password = os.getenv('DB_PASSWORD', '')
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '3306')
        database = os.getenv('DB_NAME', 'showdata')

    engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')
    return engine


def fetch_data_from_mysql(table_name, start_time, end_time, time_column='Timestamp', engine=None):
    """
    从MySQL表获取数据

    Args:
        table_name: 表名
        start_time: 开始时间
        end_time: 结束时间
        time_column: 时间列名，默认'Timestamp'
        engine: SQLAlchemy引擎，如果为None则创建新引擎

    Returns:
        DataFrame: 查询结果
    """
    if engine is None:
        engine = get_db_engine()

    query = f"SELECT * FROM `{table_name}` WHERE `{time_column}` BETWEEN '{start_time}' AND '{end_time}';"
    df = pd.read_sql(query, engine)
    return df


def check_gripper(start_time, end_time, gripper_list, key_paths):
    """
    执行关键轨迹检查

    Args:
        start_time: 开始时间 datetime对象
        end_time: 结束时间 datetime对象
        gripper_list: 机器人表名列表
        key_paths: 关键路径关键字列表，如 ['R1/CO', 'R1/DO', 'R1/CN', 'R1/DN']

    Returns:
        DataFrame: 检查结果
    """
    engine = get_db_engine()
    time_column = 'Timestamp'
    GP = []  # 收集抓放点

    # 确保 key_paths 有4个元素，不足的填充为 None
    key1 = key_paths[0] if len(key_paths) > 0 else None
    key2 = key_paths[1] if len(key_paths) > 1 else None
    key3 = key_paths[2] if len(key_paths) > 2 else None
    key4 = key_paths[3] if len(key_paths) > 3 else None

    print(f"[DEBUG] check_gripper called with:")
    print(f"  start_time: {start_time}")
    print(f"  end_time: {end_time}")
    print(f"  gripper_list: {gripper_list}")
    print(f"  key_paths: {key_paths}")

    for rob in gripper_list:
        try:
            print(f"[DEBUG] Fetching data from table: {rob}")
            Detail = fetch_data_from_mysql(rob, start_time, end_time, time_column, engine)
            print(f"[DEBUG] Table {rob} returned {len(Detail)} rows")
        except Exception as e:
            print(f"[ERROR] Error fetching data from {rob}: {e}")
            traceback.print_exc()
            continue

        if Detail.empty:
            print(f"[DEBUG] Table {rob} is empty for the given time range")
            continue

        # 打印列名用于调试
        print(f"[DEBUG] Table {rob} columns: {Detail.columns.tolist()}")

        # 检查必需的列是否存在
        required_columns = ['Name_C', 'SNR_C', 'SUB', 'P_name',
                           'Curr_A1', 'Curr_A2', 'Curr_A3', 'Curr_A4', 'Curr_A5', 'Curr_A6', 'Curr_E1',
                           'MAXCurr_A1', 'MAXCurr_A2', 'MAXCurr_A3', 'MAXCurr_A4', 'MAXCurr_A5', 'MAXCurr_A6', 'MAXCurr_E1',
                           'MinCurr_A1', 'MinCurr_A2', 'MinCurr_A3', 'MinCurr_A4', 'MinCurr_A5', 'MinCurr_A6', 'MinCurr_E1']
        missing_columns = [col for col in required_columns if col not in Detail.columns]
        if missing_columns:
            print(f"[WARNING] Table {rob} missing columns: {missing_columns}")
            continue

        # 处理数据
        P = Detail[['Name_C', 'SNR_C', 'SUB', 'P_name']].copy()
        P = P.groupby(['Name_C', 'SNR_C']).first()
        P.reset_index(inplace=True)

        Detail_subset = Detail[['Name_C', 'SNR_C', 'Curr_A1', 'Curr_A2', 'Curr_A3', 'Curr_A4', 'Curr_A5', 'Curr_A6', 'Curr_E1',
                                'MAXCurr_A1', 'MAXCurr_A2', 'MAXCurr_A3', 'MAXCurr_A4', 'MAXCurr_A5', 'MAXCurr_A6', 'MAXCurr_E1',
                                'MinCurr_A1', 'MinCurr_A2', 'MinCurr_A3', 'MinCurr_A4', 'MinCurr_A5', 'MinCurr_A6', 'MinCurr_E1']].copy()

        Size = Detail_subset.groupby(['Name_C', 'SNR_C']).size().to_frame('size')

        LQ = Detail_subset.groupby(['Name_C', 'SNR_C']).min().rename(
            columns={'Curr_A1': 'Curr_A1_LQ', 'Curr_A2': 'Curr_A2_LQ', 'Curr_A3': 'Curr_A3_LQ', 'Curr_A4': 'Curr_A4_LQ',
                     'Curr_A5': 'Curr_A5_LQ', 'Curr_A6': 'Curr_A6_LQ', 'Curr_E1': 'Curr_E1_LQ'})

        Detail_curr = Detail_subset[['Name_C', 'SNR_C', 'Curr_A1', 'Curr_A2', 'Curr_A3', 'Curr_A4', 'Curr_A5', 'Curr_A6', 'Curr_E1']].copy()

        HQ = Detail_curr.groupby(['Name_C', 'SNR_C']).max().rename(
            columns={'Curr_A1': 'Curr_A1_HQ', 'Curr_A2': 'Curr_A2_HQ', 'Curr_A3': 'Curr_A3_HQ', 'Curr_A4': 'Curr_A4_HQ',
                     'Curr_A5': 'Curr_A5_HQ', 'Curr_A6': 'Curr_A6_HQ', 'Curr_E1': 'Curr_E1_HQ'})

        Q = pd.merge(pd.merge(LQ, HQ, left_on=['Name_C', 'SNR_C'], right_index=True, how='outer'),
                     Size, left_on=['Name_C', 'SNR_C'], right_index=True, how='inner')

        # 处理MAXCurr和MinCurr列
        max_curr_cols = ["MAXCurr_A1", 'MAXCurr_A2', 'MAXCurr_A3', "MAXCurr_A4", 'MAXCurr_A5', 'MAXCurr_A6', 'MAXCurr_E1']
        min_curr_cols = ['MinCurr_A1', 'MinCurr_A2', 'MinCurr_A3', 'MinCurr_A4', 'MinCurr_A5', 'MinCurr_A6', 'MinCurr_E1']

        # 从Detail_subset中获取这些列
        for col in max_curr_cols + min_curr_cols:
            if col in Detail_subset.columns:
                # 获取每个(Name_C, SNR_C)组合的第一个值
                first_values = Detail_subset.groupby(['Name_C', 'SNR_C'])[col].first()
                Q[col] = Q.index.map(lambda x: first_values.get(x, np.nan))

        Q[max_curr_cols] = Q[max_curr_cols].astype(float)
        Q[min_curr_cols] = Q[min_curr_cols].astype(float)
        Q[max_curr_cols] = Q[max_curr_cols].fillna(0.1)
        Q[min_curr_cols] = Q[min_curr_cols].fillna(-0.1)

        # 处理负值和零值
        for col in max_curr_cols:
            Q.loc[Q[col] <= 0, col] = 0.1
        for col in min_curr_cols:
            Q.loc[Q[col] >= 0, col] = -0.1

        # 计算各轴的QH和QL值
        for i, axis in enumerate(['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'E1'], 1):
            axis_idx = str(i) if i <= 6 else '7'
            Q.loc[:, f"QH{axis_idx}"] = Q[f'Curr_{axis}_HQ'] - Q[f'MAXCurr_{axis}']
            Q.loc[:, f"QL{axis_idx}"] = Q[f'MinCurr_{axis}'] - Q[f"Curr_{axis}_LQ"]
            Q.loc[Q[f"QH{axis_idx}"] < 0, f"QH{axis_idx}"] = 0
            Q.loc[Q[f"QL{axis_idx}"] < 0, f"QL{axis_idx}"] = 0

        Q.drop(max_curr_cols + min_curr_cols, axis=1, inplace=True)

        data = pd.merge(P, Q, left_on=['Name_C', 'SNR_C'], right_index=True, how='inner')
        del Q, P
        data = data.fillna('N')
        data.insert(0, 'robot', rob)
        print(f"[DEBUG] Processed {rob}: {len(data)} unique (Name_C, SNR_C) groups")

        # 打印P_name列的唯一值用于调试
        unique_p_names = data['P_name'].dropna().unique()
        print(f"[DEBUG] Table {rob} unique P_name values: {unique_p_names[:10]}")  # 只显示前10个

        # 根据关键路径筛选数据
        matched_count = 0
        for key in [key1, key2, key3, key4]:
            if key is not None and key == key:  # 检查不是NaN
                try:
                    indices = data[data['P_name'].astype(str).str.contains(key, case=False, na=False)].index
                    print(f"[DEBUG] Key '{key}' matched {len(indices)} rows in table {rob}")
                    matched_count += len(indices)
                    for idx in indices:
                        # 使用 to_frame().T 转换为行格式
                        GP.append(data.iloc[idx:idx+1, :])
                except Exception as e:
                    print(f"[ERROR] Error filtering by key path '{key}': {e}")
                    traceback.print_exc()
                    continue

        print(f"[DEBUG] Table {rob} total matched: {matched_count} rows")

    print(f"[DEBUG] Total GP items collected: {len(GP)}")

    if GP:
        # 使用 axis=0 按行连接
        gr_check = pd.concat(GP, axis=0, ignore_index=True)
        print(f"[DEBUG] Check completed successfully! Total rows: {len(gr_check)}")
        return gr_check
    else:
        print("[DEBUG] No data found matching the criteria.")
        return pd.DataFrame()


def check_gripper_from_config(config_data):
    """
    从配置字典执行检查

    Args:
        config_data: 包含以下键的字典:
            - start_time: 开始时间 (ISO格式字符串或datetime对象)
            - end_time: 结束时间 (ISO格式字符串或datetime对象)
            - gripper_list: 机器人表名列表
            - key_paths: 关键路径关键字列表

    Returns:
        dict: 包含结果DataFrame和元数据的字典
    """
    try:
        # 解析时间
        if isinstance(config_data['start_time'], str):
            start_time = datetime.fromisoformat(config_data['start_time'].replace('Z', '+00:00'))
        else:
            start_time = config_data['start_time']

        if isinstance(config_data['end_time'], str):
            end_time = datetime.fromisoformat(config_data['end_time'].replace('Z', '+00:00'))
        else:
            end_time = config_data['end_time']

        # 执行检查
        result_df = check_gripper(
            start_time=start_time,
            end_time=end_time,
            gripper_list=config_data['gripper_list'],
            key_paths=config_data.get('key_paths', [])
        )

        # 转换为字典返回
        return {
            'success': True,
            'count': len(result_df),
            'data': result_df.to_dict('records') if not result_df.empty else [],
            'columns': result_df.columns.tolist() if not result_df.empty else []
        }
    except Exception as e:
        print(f"Error in check_gripper_from_config: {e}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'count': 0,
            'data': [],
            'columns': []
        }


def check_gripper_from_csv(csv_content, robot_list_csv_content=None):
    """
    从CSV配置文件内容执行检查（兼容原有逻辑）

    Args:
        csv_content: keypath配置CSV内容
        robot_list_csv_content: 机器人列表CSV内容（可选）

    Returns:
        dict: 检查结果
    """
    import io

    # 读取配置
    configure = pd.read_csv(io.StringIO(csv_content), encoding='gbk')
    name_list = list(configure['name'])
    para_list = list(configure['parameter'])

    config_dict = {}
    for index, name in enumerate(name_list):
        config_dict[name] = para_list[index]

    # 读取机器人列表
    if robot_list_csv_content:
        griper_list_df = pd.read_csv(io.StringIO(robot_list_csv_content), encoding='gbk')
    else:
        # 如果没有提供机器人列表，使用默认的robotfile路径
        robotfile = config_dict.get('robotfile', '')
        if robotfile and os.path.exists(robotfile):
            griper_list_df = pd.read_csv(robotfile, encoding='gbk')
        else:
            return {'success': False, 'error': 'Robot list not found'}

    griper = griper_list_df['robot'].tolist()

    # 解析时间
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now() - timedelta(hours=8)

    # 获取关键路径
    key_paths = []
    for i in range(1, 5):
        key = config_dict.get(f'keyPath{i}')
        if key and pd.notna(key):
            key_paths.append(key)

    return check_gripper_from_config({
        'start_time': start_time,
        'end_time': end_time,
        'gripper_list': griper,
        'key_paths': key_paths
    })
