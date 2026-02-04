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
    包含所有详细字段
    """
    try:
        from .weekly_result_service import import_robot_components_csv

        logger.info("开始自动同步机器人数据...")
        result = import_robot_components_csv()

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


@shared_task
def sync_from_weeklyresult():
    """
    从 WeeklyResult 表同步数据到 RobotComponent 表
    用于定时任务
    """
    try:
        from .weekly_result_service import sync_weeklyresult_to_robotcomponent

        logger.info("开始从 WeeklyResult 同步数据...")
        result = sync_weeklyresult_to_robotcomponent()

        if result.get('success'):
            logger.info(
                f"同步成功！新增 {result.get('records_created', 0)} 条，"
                f"更新 {result.get('records_updated', 0)} 条"
            )
        else:
            logger.error(f"同步失败: {result.get('error', '未知错误')}")

        return result
    except Exception as e:
        logger.error(f"同步数据时发生错误: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
