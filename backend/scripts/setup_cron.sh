#!/bin/bash
# 定时任务配置脚本
# 用于设置每24小时自动导入 weeklyresult.csv 的 cron 任务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Django 项目路径
PROJECT_DIR="/Users/caihd/Desktop/sg/backend"
PYTHON_PATH="/usr/bin/python3"

# 配置参数
DEFAULT_PROJECT="reuse"
DEFAULT_FOLDER_PATH="P:/error rate trend/"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}机器人状态定时任务配置脚本${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查项目目录是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}错误: 项目目录不存在: $PROJECT_DIR${NC}"
    echo "请修改脚本中的 PROJECT_DIR 变量"
    exit 1
fi

# 显示当前配置
echo -e "${YELLOW}当前配置:${NC}"
echo "  项目目录: $PROJECT_DIR"
echo "  项目名称: $DEFAULT_PROJECT"
echo "  文件夹路径: $DEFAULT_FOLDER_PATH"
echo ""

# 询问用户是否修改配置
read -p "是否修改配置? (y/N): " modify_config
if [ "$modify_config" = "y" ] || [ "$modify_config" = "Y" ]; then
    read -p "请输入项目名称 (默认: $DEFAULT_PROJECT): " project_input
    PROJECT_NAME=${project_input:-$DEFAULT_PROJECT}

    read -p "请输入CSV文件夹路径 (默认: $DEFAULT_FOLDER_PATH): " folder_input
    FOLDER_PATH=${folder_input:-$DEFAULT_FOLDER_PATH}
else
    PROJECT_NAME=$DEFAULT_PROJECT
    FOLDER_PATH=$DEFAULT_FOLDER_PATH
fi

# 构建 cron 命令
CRON_JOB="0 0 * * * cd $PROJECT_DIR && $PYTHON_PATH manage.py import_weekly_results --project=$PROJECT_NAME --folder-path='$FOLDER_PATH' >> $PROJECT_DIR/logs/cron_import.log 2>&1"

echo ""
echo -e "${YELLOW}即将添加的定时任务:${NC}"
echo -e "${GREEN}$CRON_JOB${NC}"
echo ""

# 确认
read -p "确认添加定时任务? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

# 检查是否已存在相同的定时任务
if crontab -l 2>/dev/null | grep -q "import_weekly_results"; then
    echo -e "${YELLOW}检测到已存在的定时任务，正在替换...${NC}"
    # 删除旧的定时任务
    crontab -l 2>/dev/null | grep -v "import_weekly_results" | crontab -
fi

# 添加新的定时任务
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo -e "${GREEN}定时任务已成功添加!${NC}"
echo ""
echo -e "${YELLOW}定时任务详情:${NC}"
echo "  执行时间: 每天 00:00 (每24小时)"
echo "  项目: $PROJECT_NAME"
echo "  日志文件: $PROJECT_DIR/logs/cron_import.log"
echo ""
echo -e "${YELLOW}查看当前所有定时任务:${NC}"
echo "  crontab -l"
echo ""
echo -e "${YELLOW}查看定时任务日志:${NC}"
echo "  tail -f $PROJECT_DIR/logs/cron_import.log"
echo ""
echo -e "${YELLOW}手动测试导入命令:${NC}"
echo "  cd $PROJECT_DIR"
echo "  $PYTHON_PATH manage.py import_weekly_results --project=$PROJECT_NAME"
echo ""
