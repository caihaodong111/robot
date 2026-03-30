import json
import os
import csv
import pandas as pd

import numpy as np
from datetime import datetime,timedelta
from sqlalchemy import create_engine
#filename1="c:\Users\zhangyan4\Desktop\suanfa\response1.json"
def fetch_data_from_mysql(table_name, start_time, end_time, time_column,engine):
        # 创建数据库连接
       
        
        # 编写SQL查询
    query = f"SELECT * FROM `{table_name}` WHERE `{time_column}` BETWEEN '{start_time}' AND '{end_time}';"
        
        # 使用pandas读取数据
    df = pd.read_sql(query, engine)
        
    return df

def check_gripper(save_path,start_time,end_time,griper,savename,key1,key2,key3,key4):

    user = 'root'
    password = '123456'
    host = '172.19.106.123'
    port = '3306'
    database = 'showdata' #'mra_show_data' #
    time_column = 'Timestamp'
    #griper_list=pd.read_csv('gripper_list.csv')
    engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

    #dirs=os.listdir(save_path)
    GP=[] # 收集抓放点
    for rob in griper:
        #print(rob)
        normal=0 # 文件夹里是否有文件的标志位
        try:
            Detail= fetch_data_from_mysql(rob, start_time, end_time, time_column,engine)
            
        except Exception as e:
            print(e)
        else:
        #print(files)
            if Detail.empty == False:
                P=Detail[['Name_C','SNR_C','SUB','P_name']]
                P= P.groupby(['Name_C','SNR_C']).first()
                P.reset_index(inplace=True) 
                Detail=Detail[['Name_C','SNR_C','Curr_A1','Curr_A2','Curr_A3','Curr_A4','Curr_A5','Curr_A6','Curr_E1',\
                'MAXCurr_A1','MAXCurr_A2','MAXCurr_A3','MAXCurr_A4','MAXCurr_A5','MAXCurr_A6','MAXCurr_E1',\
                'MinCurr_A1','MinCurr_A2','MinCurr_A3','MinCurr_A4','MinCurr_A5','MinCurr_A6','MinCurr_E1']]
               

                Size=Detail.groupby([ 'Name_C', 'SNR_C']).size().to_frame('size')
                #print(Size)

                LQ = Detail.groupby([ 'Name_C', 'SNR_C']).min().rename(
                        columns={'Curr_A1': 'Curr_A1_LQ', 'Curr_A2': 'Curr_A2_LQ', 'Curr_A3': 'Curr_A3_LQ', 'Curr_A4': 'Curr_A4_LQ',
                                 'Curr_A5': 'Curr_A5_LQ', 'Curr_A6': 'Curr_A6_LQ', 'Curr_E1': 'Curr_E1_LQ'})
                Detail=Detail[['Name_C','SNR_C','Curr_A1','Curr_A2','Curr_A3','Curr_A4','Curr_A5','Curr_A6','Curr_E1']]

                HQ = Detail.groupby([ 'Name_C', 'SNR_C']).max().rename(
                        columns={'Curr_A1': 'Curr_A1_HQ', 'Curr_A2': 'Curr_A2_HQ', 'Curr_A3': 'Curr_A3_HQ', 'Curr_A4': 'Curr_A4_HQ',
                                 'Curr_A5': 'Curr_A5_HQ', 'Curr_A6': 'Curr_A6_HQ', 'Curr_E1': 'Curr_E1_HQ'})

                Q = pd.merge(pd.merge(LQ, HQ,left_on=[ 'Name_C', 'SNR_C'],right_index=True,how='outer'),Size,left_on=[ 'Name_C', 'SNR_C'],right_index=True,how='inner')

                #Q=Q1.copy()
                
                Q[["MAXCurr_A1",'MAXCurr_A2','MAXCurr_A3',"MAXCurr_A4",'MAXCurr_A5','MAXCurr_A6','MAXCurr_E1']]=Q[["MAXCurr_A1",'MAXCurr_A2','MAXCurr_A3',"MAXCurr_A4",'MAXCurr_A5','MAXCurr_A6','MAXCurr_E1']].astype(float)
                Q[['MinCurr_A1','MinCurr_A2','MinCurr_A3','MinCurr_A4','MinCurr_A5','MinCurr_A6','MinCurr_E1']]= Q[['MinCurr_A1','MinCurr_A2','MinCurr_A3','MinCurr_A4','MinCurr_A5','MinCurr_A6','MinCurr_E1']].astype(float)
                Q[Q[["MAXCurr_A1",'MAXCurr_A2','MAXCurr_A3',"MAXCurr_A4",'MAXCurr_A5','MAXCurr_A6','MAXCurr_E1']]<=0]=0.1
                Q[Q[['MinCurr_A1','MinCurr_A2','MinCurr_A3','MinCurr_A4','MinCurr_A5','MinCurr_A6','MinCurr_E1']]>=0]=-0.1

                Q.loc[:,"QH1"]=Q['Curr_A1_HQ']-Q['MAXCurr_A1']
                Q.loc[:,"QL1"]=Q['MinCurr_A1']-Q["Curr_A1_LQ"]
                #Q.drop(['Curr_A1_HQ',"Curr_A1_LQ"],axis=1, inplace=True)
                Q.loc[Q["QH1"] < 0, "QH1"] = 0
                Q.loc[Q["QL1"] < 0, "QL1"] = 0
                Q.loc[:,"QH2"]=Q['Curr_A2_HQ']-Q['MAXCurr_A2']
                Q.loc[:,"QL2"]=Q['MinCurr_A2']-Q["Curr_A2_LQ"]
                #Q.drop(['Curr_A2_HQ',"Curr_A2_LQ"],axis=1, inplace=True)
                Q.loc[Q["QH2"] < 0, "QH2"] = 0
                Q.loc[Q["QL2"] < 0, "QL2"] = 0
                Q.loc[:,"QH3"]=Q['Curr_A3_HQ']-Q['MAXCurr_A3']
                Q.loc[:,"QL3"]=Q['MinCurr_A3']-Q["Curr_A3_LQ"]
                #Q.drop(['Curr_A3_HQ',"Curr_A3_LQ"],axis=1, inplace=True)
                Q.loc[Q["QH3"] < 0, "QH3"] = 0
                Q.loc[Q["QL3"] < 0, "QL3"] = 0
                #Q["QH3"][Q["QH3"]<0]=0
                #Q["QL3"][Q["QL3"]<0]=0                                
                Q.loc[:,"QH4"]=Q['Curr_A4_HQ']-Q['MAXCurr_A4']
                Q.loc[:,"QL4"]=Q['MinCurr_A4']-Q["Curr_A4_LQ"]
                #Q.drop(['Curr_A4_HQ',"Curr_A4_LQ"],axis=1, inplace=True)
                Q.loc[Q["QH4"] < 0, "QH4"] = 0
                Q.loc[Q["QL4"] < 0, "QL4"] = 0
                #Q["QH4"][Q["QH4"]<0]=0
                #Q["QL4"][Q["QL4"]<0]=0  
                Q.loc[:,"QH5"]=Q['Curr_A5_HQ']-Q['MAXCurr_A5']
                Q.loc[:,"QL5"]=Q['MinCurr_A5']-Q["Curr_A5_LQ"]
                #Q.drop(['Curr_A5_HQ',"Curr_A5_LQ"],axis=1, inplace=True)
                Q.loc[Q["QH5"] < 0, "QH5"] = 0
                Q.loc[Q["QL5"] < 0, "QL5"] = 0
                #Q["QH5"][Q["QH5"]<0]=0
                #Q["QL5"][Q["QL5"]<0]=0                        
                Q.loc[:,"QH6"]=Q['Curr_A6_HQ']-Q['MAXCurr_A6']
                Q.loc[:,"QL6"]=Q['MinCurr_A6']-Q["Curr_A6_LQ"]
                #Q.drop(['Curr_A6_HQ',"Curr_A6_LQ"],axis=1, inplace=True)
                Q.loc[Q["QH6"] < 0, "QH6"] = 0
                Q.loc[Q["QL6"] < 0, "QL6"] = 0
                #Q["QH6"][Q["QH6"]<0]=0
                #Q["QL6"][Q["QL6"]<0]=0 
                Q.loc[:,"QH7"]=Q['Curr_E1_HQ']-Q['MAXCurr_E1']
                Q.loc[:,"QL7"]=Q['MinCurr_E1']-Q["Curr_E1_LQ"]
                #Q.drop(['Curr_E1_HQ',"Curr_E1_LQ"],axis=1, inplace=True)
                Q.loc[Q["QH7"] < 0, "QH7"] = 0
                Q.loc[Q["QL7"] < 0, "QL7"] = 0
                #Q["QH7"][Q["QH7"]<0]=0
                #Q["QL7"][Q["QL7"]<0]=0 
                Q.drop(["MAXCurr_A1",'MAXCurr_A2','MAXCurr_A3',"MAXCurr_A4",'MAXCurr_A5','MAXCurr_A6','MAXCurr_E1','MinCurr_A1','MinCurr_A2','MinCurr_A3','MinCurr_A4','MinCurr_A5','MinCurr_A6','MinCurr_E1'],axis=1, inplace=True)
                data = pd.merge(P,Q,left_on=[ 'Name_C', 'SNR_C'],right_index=True,how='inner')
                del Q,P
                #data=pd.read_csv(save_path+'\\'+rob+'\\'+filename)
                data=data.fillna('N')
                data.insert(0,'robot',rob)
                print(rob)
                #data_co=data[data['Name_C'].str.contains('R1/CO',case=False)]
                #data_do=data[data['Name_C'].str.contains('R1/DO',case=False)]
                #a=data_co[data_co['P_name'].str.contains('CO',case=False)].index
                #b=data_do[data_do['P_name'].str.contains('DO',case=False)].index
                if key1== key1: #NAN 与任何值都不相等，包括自身
                    a=data[data['P_name'].str.contains(key1,case=False)].index
                    for i in a:
                        GP.append(data.iloc[i,:])
                        if i < data.shape[0]-1:
                            GP.append(data.iloc[i+1,:])
                if key2 == key2:    
                    b=data[data['P_name'].str.contains(key2,case=False)].index
                    for i in b:
                        GP.append(data.iloc[i,:])
                        if i < data.shape[0]-1:
                            GP.append(data.iloc[i+1,:])
                if key3 == key3:
                    #print(key3)
                    c=data[data['P_name'].str.contains(key3,case=False)].index
                    for i in c:
                        GP.append(data.iloc[i,:])
                        if i < data.shape[0]-1:
                            GP.append(data.iloc[i+1,:])
                if key4== key4:
                    d=data[data['P_name'].str.contains(key4,case=False)].index
                    for i in d:
                        GP.append(data.iloc[i,:])
                        if i < data.shape[0]-1:
                            GP.append(data.iloc[i+1,:])
        #print(type(GP[1])) 
    gr_check=pd.concat(GP,axis=1,)
    gr_check=gr_check.T
    gr_check.reset_index(drop=True, inplace=True)
    print("finish!")
    pd.DataFrame(gr_check).to_csv(save_path+savename+'.csv',encoding='gbk')        



def check_path(csv_dir,save_path,start_time,end_time):

    configure=pd.read_csv(csv_dir,encoding='gbk')
    name_list= list(configure['name'])
    para_list = list(configure['parameter'])
    for index,name in enumerate(name_list):
        if name == 'keyPath1':
            key1 = para_list[index]
        if name == 'keyPath2':
            key2 = para_list[index]
        if name == 'keyPath3':
            key3 = para_list[index]
        if name == 'keyPath4':
            key4 = para_list[index]
        if name == 'robotfile':
            robotfile = para_list[index]
        if name == 'savename':
            savename = para_list[index]

    griper_list=pd.read_csv(robotfile,encoding='gbk')
    
    griper = griper_list['robot']          
    check_gripper(save_path,start_time,end_time, griper, savename, key1, key2, key3, key4)



if __name__=="__main__":
    start_time = datetime.now()-timedelta(days=7)#hours=14)
    end_time = datetime.now()-timedelta(hours=8)

    check_path(csv_dir='keypath_configure.csv',save_path="",start_time=start_time,end_time=end_time)
    #os.chdir('P:/v206/config')
    #save_path=r'P:/v206/test_result-2023-08-25-2023-09-01'
    #save_path=r'P:\V214&254\test_result-2024-01-12-2024-01-19'
    #griper_list=pd.read_csv('gripper_list.csv')
    #griper = griper_list['robot']
    #csv_dir=r'C:\Users\zhangyan4\OneDrive - 北京奔驰汽车有限公司\桌面\robot predictive maintenance\pyqt5界面\path check\keypath_configure.csv'
    #check_path(csv_dir,save_path)