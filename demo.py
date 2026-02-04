folder_path = 'P:/error rate trend/'
#project='V214&254'
project='reuse'
#project='engine-robot'
#project='v206'
target_files = []
#csv_files = glob.glob('P:/reuse/*weeklyresult.csv')
csv_files = glob.glob('P:/'+ project+'/*weeklyresult.csv')

# 遍历文件夹并筛选文件
for files in csv_files:
    print(files)

    target_files.append((files, os.path.getctime(files)))

if target_files:
    # 按修改时间降序排序
    sorted_files = sorted(target_files, key=lambda x: x[1], reverse=True)
    latest_file = sorted_files[0][0]
    print(latest_file)
else:
    print("未找到以'check_result'结尾的CSV文件")
    exit()