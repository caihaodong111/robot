"""
Celery 定时任务
用于自动同步机器人数据
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def auto_sync_robot_data():
    """
    自动同步机器人数据
    从最新的 CSV 文件导入数据到 RobotComponent 表

    快照逻辑：
    - 本次同步前，将上次记录的高风险机器人数据存入历史快照表
    - 本次同步后，记录当前的高风险机器人列表（供下次同步使用）
    """
    try:
        from .weekly_result_service import import_robot_components_csv, archive_high_risk_robots

        logger.info("开始自动同步机器人数据...")

        # 步骤1：将上次的高风险机器人数据存入历史快照表
        archive_result = archive_high_risk_robots()
        if archive_result.get('archived_count', 0) > 0:
            logger.info(f"已将 {archive_result['archived_count']} 条高风险数据存入历史快照表")

        # 步骤2：导入最新 CSV 数据（自动同步）
        result = import_robot_components_csv(source="auto")

        if result.get('success'):
            logger.info(
                f"自动同步成功！新增 {result.get('records_created', 0)} 条，"
                f"更新 {result.get('records_updated', 0)} 条"
            )
        else:
            logger.error(f"自动同步失败: {result.get('error', '未知错误')}")

        return result
    except Exception as e:
        logger.error(f"自动同步机器人数据时发生错误: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
