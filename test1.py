


data = pd.read_csv(error_rate_path +'/'+ row.robot + '-error-rate-trend.csv')
data = data.loc[data['count'] >= data['count'].mean() / 2]
ref = data['reference'].iloc[-1]
data = data[data['reference'] == ref]
data['Timestamp'] = pd.to_datetime(data['Timestamp'])


def drow_pic(n,data,robot):
    fig = plt.figure(figsize=(10, 15))
    gs = fig.add_gridspec(7, 1, height_ratios=[1, 1, 1, 1, 1,1,1])

    # 创建子图，注意我们不共享x轴，但通过布局和对齐来模拟共享效果
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])
    ax4 = fig.add_subplot(gs[3])
    ax5 = fig.add_subplot(gs[4])
    ax6 = fig.add_subplot(gs[5])
    ax7 = fig.add_subplot(gs[6])


    if n==1:
        data=data[['Timestamp','error1_c1', 'tem1_m', 'A1_e_rate', 'A1_Rms',  'Q1','Curr_A1_max','Curr_A1_min']]
        ax1.scatter(data['Timestamp'], data['Q1'], c='tab:blue', s=5,alpha=1)
        ax1.xaxis.set_visible(False)
        ax1.set_ylabel('Q1')
        #ax1.legend()

        ax2.scatter(data['Timestamp'], data['A1_e_rate'], c='tab:orange',s=5, alpha=1)
        ax2.set_ylabel('A1_e_rate')
        ax2.xaxis.set_visible(False)

        ax3.scatter(data['Timestamp'], data['A1_Rms'], c='tab:green', s=5,alpha=1)
        ax3.set_ylabel('A1_Rms')
        ax3.xaxis.set_visible(False)

        ax4.scatter(data['Timestamp'], data['Curr_A1_min'], c='tab:pink', s=5,alpha=1)
        #ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax4.set_ylabel('Min')
        ax4.xaxis.set_visible(False)

        ax5.scatter(data['Timestamp'], data['Curr_A1_max'], c='yellow', s=5,alpha=1)
        #ax5.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax5.set_ylabel('Max')
        ax5.xaxis.set_visible(False)

        ax6.scatter(data['Timestamp'], data['tem1_m'], c='tab:red', s=5,alpha=1)
        #ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax6.set_ylabel('T1')
        ax6.xaxis.set_visible(False)

        ax7.scatter(data['Timestamp'], data['error1_c1'], c='tab:blue', s=5,alpha=1)
        ax7.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax7.set_ylabel('error')



    if n == 2:
        data = data[['Timestamp', 'error1_c1', 'tem2_m', 'A2_e_rate', 'A2_Rms', 'Q2','Curr_A2_max','Curr_A2_min']]
        ax1.scatter(data['Timestamp'], data['Q2'], c='tab:blue', s=5, alpha=1)
        ax1.xaxis.set_visible(False)
        ax1.set_ylabel('Q2')
        # ax1.legend()

        ax2.scatter(data['Timestamp'], data['A2_e_rate'], c='tab:orange', s=5, alpha=1)
        ax2.set_ylabel('A2_e_rate')
        ax2.xaxis.set_visible(False)

        ax3.scatter(data['Timestamp'], data['A2_Rms'], c='tab:green', s=5, alpha=1)
        ax3.set_ylabel('A2_Rms')
        ax3.xaxis.set_visible(False)

        ax4.scatter(data['Timestamp'], data['Curr_A2_min'], c='tab:pink', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax4.set_ylabel('Min')
        ax4.xaxis.set_visible(False)

        ax5.scatter(data['Timestamp'], data['Curr_A2_max'], c='yellow', s=5, alpha=1)
        # ax5.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax5.set_ylabel('Max')
        ax5.xaxis.set_visible(False)


        ax6.scatter(data['Timestamp'], data['tem2_m'], c='tab:red', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax6.set_ylabel('T2')
        ax6.xaxis.set_visible(False)

        ax7.scatter(data['Timestamp'], data['error1_c1'], c='tab:red', s=5, alpha=1)
        ax7.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax7.set_ylabel('error')

    if n == 3:
        data = data[['Timestamp', 'error1_c1', 'tem3_m', 'A3_e_rate', 'A3_Rms', 'Q3','Curr_A3_max','Curr_A3_min']]

        ax1.scatter(data['Timestamp'], data['Q3'], c='tab:blue', s=5, alpha=1)
        ax1.xaxis.set_visible(False)
        ax1.set_ylabel('Q3')
        # ax1.legend()

        ax2.scatter(data['Timestamp'], data['A3_e_rate'], c='tab:orange', s=5, alpha=1)
        ax2.set_ylabel('A3_e_rate')
        ax2.xaxis.set_visible(False)

        ax3.scatter(data['Timestamp'], data['A3_Rms'], c='tab:green', s=5, alpha=1)
        ax3.set_ylabel('A3_Rms')
        ax3.xaxis.set_visible(False)

        ax4.scatter(data['Timestamp'], data['Curr_A3_min'], c='tab:pink', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax4.set_ylabel('Min')
        ax4.xaxis.set_visible(False)

        ax5.scatter(data['Timestamp'], data['Curr_A3_max'], c='yellow', s=5, alpha=1)
        # ax5.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax5.set_ylabel('Max')
        ax5.xaxis.set_visible(False)

        ax6.scatter(data['Timestamp'], data['tem3_m'], c='tab:red', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax6.set_ylabel('T3')
        ax6.xaxis.set_visible(False)

        ax7.scatter(data['Timestamp'], data['error1_c1'], c='tab:red', s=5, alpha=1)
        ax7.set_xlabel('Timestamp')  # 仅在最后一个子图上显示x轴标签
        ax7.set_ylabel('error')

    if n == 4:
        data = data[['Timestamp', 'error1_c1', 'tem4_m', 'A4_e_rate', 'A4_Rms', 'Q4','Curr_A4_max','Curr_A4_min']]
        ax1.scatter(data['Timestamp'], data['Q4'], c='tab:blue', s=5, alpha=1)
        ax1.xaxis.set_visible(False)
        ax1.set_ylabel('Q4')
        # ax1.legend()

        ax2.scatter(data['Timestamp'], data['A4_e_rate'], c='tab:orange', s=5, alpha=1)
        ax2.set_ylabel('A4_e_rate')
        ax2.xaxis.set_visible(False)

        ax3.scatter(data['Timestamp'], data['A4_Rms'], c='tab:green', s=5, alpha=1)
        ax3.set_ylabel('A4_Rms')
        ax3.xaxis.set_visible(False)

        ax4.scatter(data['Timestamp'], data['Curr_A4_min'], c='tab:pink', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax4.set_ylabel('Min')
        ax4.xaxis.set_visible(False)

        ax5.scatter(data['Timestamp'], data['Curr_A4_max'], c='yellow', s=5, alpha=1)
        # ax5.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax5.set_ylabel('Max')
        ax5.xaxis.set_visible(False)

        ax6.scatter(data['Timestamp'], data['tem4_m'], c='tab:red', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax6.set_ylabel('T4')
        ax6.xaxis.set_visible(False)

        ax7.scatter(data['Timestamp'], data['error1_c1'], c='tab:red', s=5, alpha=1)
        ax7.set_xlabel('Timestamp')  # 仅在最后一个子图上显示x轴标签
        ax7.set_ylabel('error')

    if n == 5:
        data = data[['Timestamp', 'error1_c1', 'tem5_m', 'A5_e_rate', 'A5_Rms', 'Q5','Curr_A5_max','Curr_A5_min']]
        ax1.scatter(data['Timestamp'], data['Q5'], c='tab:blue', s=5, alpha=1)
        ax1.xaxis.set_visible(False)
        ax1.set_ylabel('Q5')
        # ax1.legend()

        ax2.scatter(data['Timestamp'], data['A5_e_rate'], c='tab:orange', s=5, alpha=1)
        ax2.set_ylabel('A5_e_rate')
        ax2.xaxis.set_visible(False)

        ax3.scatter(data['Timestamp'], data['A5_Rms'], c='tab:green', s=5, alpha=1)
        ax3.set_ylabel('A5_Rms')
        ax3.xaxis.set_visible(False)

        ax4.scatter(data['Timestamp'], data['Curr_A5_min'], c='tab:pink', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax4.set_ylabel('Min')
        ax4.xaxis.set_visible(False)

        ax5.scatter(data['Timestamp'], data['Curr_A5_max'], c='yellow', s=5, alpha=1)
        # ax5.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax5.set_ylabel('Max')
        ax5.xaxis.set_visible(False)

        ax6.scatter(data['Timestamp'], data['tem5_m'], c='tab:red', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax6.set_ylabel('T5')
        ax6.xaxis.set_visible(False)

        ax7.scatter(data['Timestamp'], data['error1_c1'], c='tab:red', s=5, alpha=1)
        ax7.set_xlabel('Timestamp')  # 仅在最后一个子图上显示x轴标签
        ax7.set_ylabel('error')
    if n == 6:
        data = data[['Timestamp', 'error1_c1', 'tem6_m', 'A6_e_rate', 'A6_Rms', 'Q6','Curr_A6_max','Curr_A6_min']]
        ax1.scatter(data['Timestamp'], data['Q6'], c='tab:blue', s=5, alpha=1)
        ax1.xaxis.set_visible(False)
        ax1.set_ylabel('Q6')
        # ax1.legend()

        ax2.scatter(data['Timestamp'], data['A6_e_rate'], c='tab:orange', s=5, alpha=1)
        ax2.set_ylabel('A6_e_rate')
        ax2.xaxis.set_visible(False)

        ax3.scatter(data['Timestamp'], data['A6_Rms'], c='tab:green', s=5, alpha=1)
        ax3.set_ylabel('A6_Rms')
        ax3.xaxis.set_visible(False)

        ax4.scatter(data['Timestamp'], data['Curr_A6_min'], c='tab:pink', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax4.set_ylabel('Min')
        ax4.xaxis.set_visible(False)

        ax5.scatter(data['Timestamp'], data['Curr_A6_max'], c='yellow', s=5, alpha=1)
        # ax5.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax5.set_ylabel('Max')
        ax5.xaxis.set_visible(False)

        ax6.scatter(data['Timestamp'], data['tem6_m'], c='tab:red', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax6.set_ylabel('T6')
        ax6.xaxis.set_visible(False)

        ax7.scatter(data['Timestamp'], data['error1_c1'], c='tab:red', s=5, alpha=na ge1)
        ax7.set_xlabel('Timestamp')  # 仅在最后一个子图上显示x轴标签
        ax7.set_ylabel('error')

    if n == 7:

        data = data[['Timestamp', 'error1_c1', 'tem7_m', 'A7_e_rate', 'A7_Rms', 'Q7','Curr_A7_max','Curr_A7_min']]
        ax1.scatter(data['Timestamp'], data['Q7'], c='tab:blue', s=5, alpha=1)
        ax1.xaxis.set_visible(False)
        ax1.set_ylabel('Q7')
        # ax1.legend()

        ax2.scatter(data['Timestamp'], data['A7_e_rate'], c='tab:orange', s=5, alpha=1)
        ax2.set_ylabel('A7_e_rate')
        ax2.xaxis.set_visible(False)

        ax3.scatter(data['Timestamp'], data['A7_Rms'], c='tab:green', s=5, alpha=1)
        ax3.set_ylabel('A7_Rms')
        ax3.xaxis.set_visible(False)

        ax4.scatter(data['Timestamp'], data['Curr_A7_min'], c='tab:pink', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax4.set_ylabel('Min')
        ax4.xaxis.set_visible(False)

        ax5.scatter(data['Timestamp'], data['Curr_A7_max'], c='yellow', s=5, alpha=1)
        # ax5.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax5.set_ylabel('Max')
        ax5.xaxis.set_visible(False)

        ax6.scatter(data['Timestamp'], data['tem7_m'], c='tab:red', s=5, alpha=1)
        # ax4.set_xlabel('date')  # 仅在最后一个子图上显示x轴标签
        ax6.set_ylabel('T7')
        ax6.xaxis.set_visible(False)

        ax7.scatter(data['Timestamp'], data['error1_c1'], c='tab:red', s=5, alpha=1)
        ax7.set_xlabel('Timestamp')  # 仅在最后一个子图上显示x轴标签
        ax7.set_ylabel('error')


    # 调整子图之间的间距
    fig.subplots_adjust(hspace=0)  # 设置子图之间的垂直间距为0
    plt.xticks(rotation='vertical')
    savefig_p='P:/PIC/'+robot+'_'+str(n)+'_trend.png'
    # 保存图像
    fig.savefig(savefig_p, dpi=80, bbox_inches='tight')
    plt.close()
    return savefig_p