"""
关键轨迹检查服务模块
完全基于 check_gripper_withmax.py 的核心逻辑实现
使用 .env 的 PROGRAM CYCLE SYNC 数据库配置
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv
import traceback

load_dotenv()


def get_db_engine():
    """
    从 .env 获取 PROGRAM CYCLE SYNC 数据库配置
    """
    user = os.getenv('SG_DB_USER', 'root')
    password = os.getenv('SG_DB_PASSWORD', '123456')
    host = os.getenv('SG_DB_HOST', '172.19.106.123')
    port = os.getenv('SG_DB_PORT', '3306')
    database = os.getenv('SG_DB_NAME', 'showdata')

    engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')
    return engine


def fetch_data_from_mysql(table_name, start_time, end_time, time_column, engine):
    """
    从MySQL数据库获取数据（完全复制 check_gripper_withmax.py 的逻辑）

    Args:
        table_name: 数据库表名
        start_time: 开始时间
        end_time: 结束时间
        time_column: 时间列名
        engine: SQLAlchemy引擎

    Returns:
        DataFrame: 查询结果
    """
    query = f"SELECT * FROM `{table_name}` WHERE `{time_column}` BETWEEN '{start_time}' AND '{end_time}';"
    df = pd.read_sql(query, engine)
    return df


def check_gripper(save_path, start_time, end_time, griper, savename, key1, key2, key3, key4):
    """
    执行关键轨迹检查（完全基于 check_gripper_withmax.py 的 check_gripper 函数）

    Args:
        save_path: 结果保存路径（可选，用于CSV导出）
        start_time: 开始时间
        end_time: 结束时间
        griper: 机器人表名列表
        savename: 保存文件名
        key1, key2, key3, key4: 关键路径筛选关键字

    Returns:
        DataFrame: 检查结果
    """
    time_column = 'Timestamp'
    engine = get_db_engine()

    GP = []  # 收集抓放点

    for rob in griper:
        normal = 0  # 文件夹里是否有文件的标志位
        try:
            Detail = fetch_data_from_mysql(rob, start_time, end_time, time_column, engine)
        except Exception as e:
            print(f"[ERROR] {rob}: {e}")
            traceback.print_exc()
            continue
        else:
            if Detail.empty == False:
                P = Detail[['Name_C', 'SNR_C', 'SUB', 'P_name']]
                P = P.groupby(['Name_C', 'SNR_C']).first()
                P.reset_index(inplace=True)

                Detail = Detail[['Name_C', 'SNR_C',
                                'Curr_A1', 'Curr_A2', 'Curr_A3', 'Curr_A4', 'Curr_A5', 'Curr_A6', 'Curr_E1',
                                'MAXCurr_A1', 'MAXCurr_A2', 'MAXCurr_A3', 'MAXCurr_A4', 'MAXCurr_A5', 'MAXCurr_A6', 'MAXCurr_E1',
                                'MinCurr_A1', 'MinCurr_A2', 'MinCurr_A3', 'MinCurr_A4', 'MinCurr_A5', 'MinCurr_A6', 'MinCurr_E1']]

                Size = Detail.groupby(['Name_C', 'SNR_C']).size().to_frame('size')

                LQ = Detail.groupby(['Name_C', 'SNR_C']).min().rename(
                    columns={'Curr_A1': 'Curr_A1_LQ', 'Curr_A2': 'Curr_A2_LQ', 'Curr_A3': 'Curr_A3_LQ', 'Curr_A4': 'Curr_A4_LQ',
                             'Curr_A5': 'Curr_A5_LQ', 'Curr_A6': 'Curr_A6_LQ', 'Curr_E1': 'Curr_E1_LQ'})

                Detail_curr = Detail[['Name_C', 'SNR_C', 'Curr_A1', 'Curr_A2', 'Curr_A3', 'Curr_A4', 'Curr_A5', 'Curr_A6', 'Curr_E1']]

                HQ = Detail_curr.groupby(['Name_C', 'SNR_C']).max().rename(
                    columns={'Curr_A1': 'Curr_A1_HQ', 'Curr_A2': 'Curr_A2_HQ', 'Curr_A3': 'Curr_A3_HQ', 'Curr_A4': 'Curr_A4_HQ',
                             'Curr_A5': 'Curr_A5_HQ', 'Curr_A6': 'Curr_A6_HQ', 'Curr_E1': 'Curr_E1_HQ'})

                Q = pd.merge(pd.merge(LQ, HQ, left_on=['Name_C', 'SNR_C'], right_index=True, how='outer'),
                             Size, left_on=['Name_C', 'SNR_C'], right_index=True, how='inner')

                # 处理 MAXCurr 和 MinCurr 列
                Q[["MAXCurr_A1", 'MAXCurr_A2', 'MAXCurr_A3', "MAXCurr_A4", 'MAXCurr_A5', 'MAXCurr_A6', 'MAXCurr_E1']] = Q[
                    ["MAXCurr_A1", 'MAXCurr_A2', 'MAXCurr_A3', "MAXCurr_A4", 'MAXCurr_A5', 'MAXCurr_A6', 'MAXCurr_E1']].astype(float)
                Q[['MinCurr_A1', 'MinCurr_A2', 'MinCurr_A3', 'MinCurr_A4', 'MinCurr_A5', 'MinCurr_A6', 'MinCurr_E1']] = Q[
                    ['MinCurr_A1', 'MinCurr_A2', 'MinCurr_A3', 'MinCurr_A4', 'MinCurr_A5', 'MinCurr_A6', 'MinCurr_E1']].astype(float)

                # 将 <=0 的值设为 0.1，>=0 的值设为 -0.1
                Q[Q[["MAXCurr_A1", 'MAXCurr_A2', 'MAXCurr_A3', "MAXCurr_A4", 'MAXCurr_A5', 'MAXCurr_A6', 'MAXCurr_E1']] <= 0] = 0.1
                Q[Q[['MinCurr_A1', 'MinCurr_A2', 'MinCurr_A3', 'MinCurr_A4', 'MinCurr_A5', 'MinCurr_A6', 'MinCurr_E1']] >= 0] = -0.1

                # 计算 QH1~QH7 和 QL1~QL7
                Q.loc[:, "QH1"] = Q['Curr_A1_HQ'] - Q['MAXCurr_A1']
                Q.loc[:, "QL1"] = Q['MinCurr_A1'] - Q["Curr_A1_LQ"]
                Q.loc[Q["QH1"] < 0, "QH1"] = 0
                Q.loc[Q["QL1"] < 0, "QL1"] = 0

                Q.loc[:, "QH2"] = Q['Curr_A2_HQ'] - Q['MAXCurr_A2']
                Q.loc[:, "QL2"] = Q['MinCurr_A2'] - Q["Curr_A2_LQ"]
                Q.loc[Q["QH2"] < 0, "QH2"] = 0
                Q.loc[Q["QL2"] < 0, "QL2"] = 0

                Q.loc[:, "QH3"] = Q['Curr_A3_HQ'] - Q['MAXCurr_A3']
                Q.loc[:, "QL3"] = Q['MinCurr_A3'] - Q["Curr_A3_LQ"]
                Q.loc[Q["QH3"] < 0, "QH3"] = 0
                Q.loc[Q["QL3"] < 0, "QL3"] = 0

                Q.loc[:, "QH4"] = Q['Curr_A4_HQ'] - Q['MAXCurr_A4']
                Q.loc[:, "QL4"] = Q['MinCurr_A4'] - Q["Curr_A4_LQ"]
                Q.loc[Q["QH4"] < 0, "QH4"] = 0
                Q.loc[Q["QL4"] < 0, "QL4"] = 0

                Q.loc[:, "QH5"] = Q['Curr_A5_HQ'] - Q['MAXCurr_A5']
                Q.loc[:, "QL5"] = Q['MinCurr_A5'] - Q["Curr_A5_LQ"]
                Q.loc[Q["QH5"] < 0, "QH5"] = 0
                Q.loc[Q["QL5"] < 0, "QL5"] = 0

                Q.loc[:, "QH6"] = Q['Curr_A6_HQ'] - Q['MAXCurr_A6']
                Q.loc[:, "QL6"] = Q['MinCurr_A6'] - Q["Curr_A6_LQ"]
                Q.loc[Q["QH6"] < 0, "QH6"] = 0
                Q.loc[Q["QL6"] < 0, "QL6"] = 0

                Q.loc[:, "QH7"] = Q['Curr_E1_HQ'] - Q['MAXCurr_E1']
                Q.loc[:, "QL7"] = Q['MinCurr_E1'] - Q["Curr_E1_LQ"]
                Q.loc[Q["QH7"] < 0, "QH7"] = 0
                Q.loc[Q["QL7"] < 0, "QL7"] = 0

                Q.drop(["MAXCurr_A1", 'MAXCurr_A2', 'MAXCurr_A3', "MAXCurr_A4", 'MAXCurr_A5', 'MAXCurr_A6', 'MAXCurr_E1',
                        'MinCurr_A1', 'MinCurr_A2', 'MinCurr_A3', 'MinCurr_A4', 'MinCurr_A5', 'MinCurr_A6', 'MinCurr_E1'],
                       axis=1, inplace=True)

                data = pd.merge(P, Q, left_on=['Name_C', 'SNR_C'], right_index=True, how='inner')
                del Q, P

                data = data.fillna('N')
                data.insert(0, 'robot', rob)
                print(rob)

                # 按关键字筛选抓放点（完全复制原脚本逻辑）
                if key1 == key1:  # NAN 与任何值都不相等，包括自身
                    a = data[data['P_name'].str.contains(key1, case=False)].index
                    for i in a:
                        GP.append(data.iloc[i, :])
                        if i < data.shape[0] - 1:
                            GP.append(data.iloc[i + 1, :])

                if key2 == key2:
                    b = data[data['P_name'].str.contains(key2, case=False)].index
                    for i in b:
                        GP.append(data.iloc[i, :])
                        if i < data.shape[0] - 1:
                            GP.append(data.iloc[i + 1, :])

                if key3 == key3:
                    c = data[data['P_name'].str.contains(key3, case=False)].index
                    for i in c:
                        GP.append(data.iloc[i, :])
                        if i < data.shape[0] - 1:
                            GP.append(data.iloc[i + 1, :])

                if key4 == key4:
                    d = data[data['P_name'].str.contains(key4, case=False)].index
                    for i in d:
                        GP.append(data.iloc[i, :])
                        if i < data.shape[0] - 1:
                            GP.append(data.iloc[i + 1, :])

    # 合并结果
    if GP:
        gr_check = pd.concat(GP, axis=1)
        gr_check = gr_check.T
        gr_check.reset_index(drop=True, inplace=True)
        print("finish!")

        # 可选：保存CSV（如果提供了save_path和savename）
        if save_path and savename:
            pd.DataFrame(gr_check).to_csv(save_path + savename + '.csv', encoding='gbk')

        return gr_check
    else:
        print("No matching data found")
        return pd.DataFrame()


def check_gripper_from_config(config_data):
    """
    从配置字典执行检查（适配Django接口）

    Args:
        config_data: 包含以下键的字典:
            - start_time: 开始时间 (ISO格式字符串或datetime对象)
            - end_time: 结束时间 (ISO格式字符串或datetime对象)
            - gripper_list: 机器人表名列表（从robot_components表查询得到）
            - key_paths: 关键路径关键字列表
            - save_path: 可选的保存路径

    Returns:
        dict: 包含结果DataFrame和元数据的字典
    """
    try:
        result_df = check_gripper_df_from_config(config_data)

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


def check_gripper_df_from_config(config_data):
    """
    从配置字典执行检查并返回 DataFrame（用于大数据量 CSV 导出，避免 to_dict 占用大量内存）
    """
    # 解析时间
    if isinstance(config_data["start_time"], str):
        start_time = datetime.fromisoformat(config_data["start_time"].replace("Z", "+00:00"))
    else:
        start_time = config_data["start_time"]

    if isinstance(config_data["end_time"], str):
        end_time = datetime.fromisoformat(config_data["end_time"].replace("Z", "+00:00"))
    else:
        end_time = config_data["end_time"]

    griper = config_data["gripper_list"]
    key_paths = config_data.get("key_paths", [])
    save_path = config_data.get("save_path", "")
    savename = config_data.get("savename", "result")

    key1 = key_paths[0] if len(key_paths) > 0 else np.nan
    key2 = key_paths[1] if len(key_paths) > 1 else np.nan
    key3 = key_paths[2] if len(key_paths) > 2 else np.nan
    key4 = key_paths[3] if len(key_paths) > 3 else np.nan

    return check_gripper(
        save_path=save_path,
        start_time=start_time,
        end_time=end_time,
        griper=griper,
        savename=savename,
        key1=key1,
        key2=key2,
        key3=key3,
        key4=key4,
    )
