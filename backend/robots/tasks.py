"""
Celery 定时任务
用于自动同步机器人数据
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def _refresh_reference_dict():
    from django.conf import settings
    from django.utils import timezone
    from django.db import transaction
    from pathlib import Path
    import csv

    from .models import RobotReferenceDict, RefreshLog

    csv_path = Path(settings.BASE_DIR).parent / "dic information .csv"
    logger.info("Reference dict refresh started: file=%s", csv_path)

    if not csv_path.exists():
        logger.warning("Reference dict refresh failed: missing file=%s", csv_path)
        RefreshLog.objects.create(
            source="manual",
            status="failed",
            source_file=str(csv_path),
            error_message=f"CSV文件不存在: {csv_path}",
            total_records=0,
        )
        return {"success": False, "error": f"CSV文件不存在: {csv_path}"}

    try:
        rows = []
        skipped = 0
        now = timezone.now()
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file_obj:
            reader = csv.reader(file_obj)
            for row in reader:
                if not row or len(row) < 3:
                    skipped += 1
                    continue
                robot = row[0].strip()
                reference = row[1].strip()
                number_raw = row[2].strip()
                if not robot or not reference:
                    skipped += 1
                    continue
                try:
                    number = float(number_raw) if number_raw != "" else None
                except ValueError:
                    skipped += 1
                    continue
                rows.append((robot, reference, number))

        if not rows:
            logger.info(
                "Reference dict refresh finished: empty file=%s skipped=%s",
                csv_path,
                skipped,
            )
            RefreshLog.objects.create(
                source="manual",
                status="success",
                source_file=str(csv_path),
                total_records=0,
                error_message=f"skipped_rows={skipped}",
            )
            return {
                "success": True,
                "file": str(csv_path),
                "records_created": 0,
                "records_updated": 0,
                "records_skipped": skipped,
            }

        existing_keys = set(
            RobotReferenceDict.objects.values_list("robot", "reference")
        )

        to_create = []
        to_update = []
        for robot, reference, number in rows:
            if (robot, reference) in existing_keys:
                to_update.append((robot, reference, number))
            else:
                to_create.append((robot, reference, number))

        created = 0
        updated = 0

        if to_create:
            create_objs = [
                RobotReferenceDict(
                    robot=robot,
                    reference=reference,
                    number=number,
                    updated_at=now,
                )
                for robot, reference, number in to_create
            ]
            created = len(
                RobotReferenceDict.objects.bulk_create(
                    create_objs, ignore_conflicts=True
                )
            )

        BATCH_SIZE = 500
        for i in range(0, len(to_update), BATCH_SIZE):
            batch = to_update[i:i + BATCH_SIZE]
            with transaction.atomic():
                for robot, reference, number in batch:
                    RobotReferenceDict.objects.filter(
                        robot=robot,
                        reference=reference,
                    ).update(number=number, updated_at=now)
            updated += len(batch)

        RefreshLog.objects.create(
            source="manual",
            status="success",
            source_file=str(csv_path),
            records_created=created,
            records_updated=updated,
            records_deleted=0,
            total_records=len(rows),
            error_message=f"skipped_rows={skipped}",
        )

        logger.info(
            "Reference dict refresh finished: file=%s total=%s created=%s updated=%s skipped=%s",
            csv_path,
            len(rows),
            created,
            updated,
            skipped,
        )

        return {
            "success": True,
            "file": str(csv_path),
            "records_created": created,
            "records_updated": updated,
            "records_skipped": skipped,
        }
    except Exception as exc:
        logger.exception("Reference dict refresh failed: file=%s", csv_path)
        RefreshLog.objects.create(
            source="manual",
            status="failed",
            source_file=str(csv_path),
            error_message=str(exc),
            total_records=0,
        )
        return {"success": False, "error": str(exc)}


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
        from .models import EditSessionVersion

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
            # 步骤3：增加会话版本号，使所有编辑会话失效
            new_version = EditSessionVersion.increment_version(updated_by="scheduled_sync")
            logger.info(f"会话版本已更新至 {new_version}，所有编辑会话需要重新登录")
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
def refresh_reference_dict_task():
    return _refresh_reference_dict()
