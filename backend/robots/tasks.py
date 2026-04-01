"""
Celery 定时任务
用于自动同步机器人数据
"""
from pathlib import Path

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def _split_reference_dict_paths(value) -> list:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    parts = []
    for raw in str(value).replace("\n", ";").split(";"):
        parts.extend(raw.split(","))
    return [item.strip() for item in parts if item.strip()]


def _format_source_file(paths, max_len: int) -> str:
    joined = ";".join([str(p) for p in paths])
    if len(joined) <= max_len:
        return joined
    from pathlib import Path

    names = ";".join([Path(str(p)).name for p in paths])
    if len(names) <= max_len:
        return names
    if max_len <= 3:
        return names[:max_len]
    return f"{names[:max_len - 3]}..."


def _refresh_reference_dict():
    from django.conf import settings
    from django.utils import timezone
    from django.db import transaction
    from pathlib import Path
    import csv

    from .models import RobotReferenceDict, RefreshLog, PathConfig

    default_path = Path(
        getattr(
            settings,
            "REFERENCE_DICT_CSV",
            str(Path(settings.BASE_DIR).parent / "dic information .csv"),
        )
    )
    try:
        csv_config = PathConfig.get_path("reference_dict_csv", str(default_path))
    except Exception:
        csv_config = default_path
    configured_paths = _split_reference_dict_paths(csv_config)
    if not configured_paths:
        configured_paths = [str(default_path)]

    csv_paths = [Path(path) for path in configured_paths]
    logger.info("Reference dict refresh started: paths=%s", csv_paths)
    source_file_max_len = RefreshLog._meta.get_field("source_file").max_length
    source_file_value = _format_source_file(csv_paths, source_file_max_len)

    try:
        rows = []
        skipped = 0
        now = timezone.now()
        missing_paths = []
        for folder in csv_paths:
            csv_path = folder / "dic information .csv"
            if not csv_path.exists():
                missing_paths.append(str(csv_path))
                continue
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

        if missing_paths:
            logger.warning("Reference dict missing files: %s", missing_paths)

        if not rows:
            logger.info(
                "Reference dict refresh finished: empty file=%s skipped=%s",
                csv_path,
                skipped,
            )
            RefreshLog.objects.create(
                source="manual",
                trigger="manual",
                status="success",
                source_file=source_file_value,
                total_records=0,
                error_message=f"skipped_rows={skipped};missing_files={missing_paths}",
            )
            return {
                "success": True,
                "file": [str(p) for p in csv_paths],
                "records_created": 0,
                "records_updated": 0,
                "records_skipped": skipped,
            }

        deduped = {}
        for robot, reference, number in rows:
            deduped[(robot, reference)] = number

        create_objs = [
            RobotReferenceDict(
                robot=robot,
                reference=reference,
                number=number,
                updated_at=now,
            )
            for (robot, reference), number in deduped.items()
        ]

        with transaction.atomic():
            RobotReferenceDict.objects.all().delete()
            if create_objs:
                RobotReferenceDict.objects.bulk_create(create_objs)

        created = len(create_objs)
        updated = 0

        RefreshLog.objects.create(
            source="manual",
            trigger="manual",
            status="success",
            source_file=source_file_value,
            records_created=created,
            records_updated=updated,
            records_deleted=0,
            total_records=len(rows),
            error_message=f"skipped_rows={skipped};missing_files={missing_paths}",
        )

        logger.info(
            "Reference dict refresh finished: paths=%s total=%s created=%s updated=%s skipped=%s missing=%s",
            csv_paths,
            len(rows),
            created,
            updated,
            skipped,
            len(missing_paths),
        )

        return {
            "success": True,
            "file": [str(p) for p in csv_paths],
            "records_created": created,
            "records_updated": updated,
            "records_skipped": skipped,
        }
    except Exception as exc:
        logger.exception("Reference dict refresh failed: paths=%s", csv_paths)
        RefreshLog.objects.create(
            source="manual",
            trigger="manual",
            status="failed",
            source_file=source_file_value,
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


@shared_task
def import_robot_components_csv_task(file_path=None, folder_path=None, project=None, use_mysql_load_data=None):
    from .weekly_result_service import import_robot_components_csv

    return import_robot_components_csv(
        file_path=file_path,
        folder_path=folder_path,
        project=project,
        source="manual",
        use_mysql_load_data=use_mysql_load_data,
    )


def _raise_if_gripper_check_cancelled(task_id):
    from .gripper_check_state import is_gripper_check_cancelled
    from .gripper_service import GripperCheckCancelledError

    if is_gripper_check_cancelled(task_id):
        raise GripperCheckCancelledError("任务已取消")


def _run_gripper_check_task(config_data, task_id, export_csv=False):
    from django.conf import settings

    from .gripper_check_state import set_gripper_check_latest, set_gripper_check_status
    from .gripper_service import (
        GripperCheckCancelledError,
        check_gripper_df_from_config,
        check_gripper_from_config,
    )

    task_id = (task_id or "").strip()
    cancel_check = lambda: _raise_if_gripper_check_cancelled(task_id)
    server_path = None
    total_robots = len(config_data.get("gripper_list") or [])

    def progress_callback(current, total, robot):
        progress_text = f"{current}/{total}" if total else f"{current}"
        logger.info("Gripper task %s progress (%s) robot=%s", task_id, progress_text, robot)
        set_gripper_check_status(
            "running",
            task_id=task_id,
            progress_current=current,
            progress_total=total,
            progress_text=progress_text,
            current_robot=robot,
            robot_count=total_robots,
        )

    set_gripper_check_status("running", task_id=task_id, robot_count=total_robots)

    try:
        if export_csv:
            export_dir = Path(getattr(settings, "BASE_DIR", ".")) / "exports" / "gripper_check"
            export_dir.mkdir(parents=True, exist_ok=True)
            file_stamp = timezone.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"trajectory_report_{file_stamp}_{task_id[:8]}.csv"
            server_path = export_dir / filename

            df = check_gripper_df_from_config(
                config_data,
                cancel_check=cancel_check,
                progress_callback=progress_callback,
            )
            cancel_check()
            set_gripper_check_status("exporting", task_id=task_id)
            logger.info("Gripper CSV task %s exporting rows=%s path=%s", task_id, df.shape[0], server_path)
            df.to_csv(server_path, index=False, encoding="utf-8-sig")

            latest = {
                "success": True,
                "count": int(df.shape[0]),
                "filename": filename,
                "server_path": str(server_path),
                "task_id": task_id,
                "updated_at": timezone.now().isoformat(),
            }
        else:
            latest = dict(
                check_gripper_from_config(
                    config_data,
                    cancel_check=cancel_check,
                    progress_callback=progress_callback,
                )
            )
            latest["task_id"] = task_id
            latest["updated_at"] = timezone.now().isoformat()

        set_gripper_check_latest(latest, task_id=task_id)
        set_gripper_check_status("idle", task_id=task_id)
        return latest
    except GripperCheckCancelledError as exc:
        if server_path and server_path.exists():
            try:
                server_path.unlink()
            except OSError:
                logger.warning("Failed to remove cancelled CSV %s", server_path)

        latest = {
            "success": False,
            "cancelled": True,
            "error": str(exc),
            "count": 0,
            "data": [],
            "columns": [],
            "filename": "",
            "server_path": "",
            "task_id": task_id,
            "updated_at": timezone.now().isoformat(),
        }
        set_gripper_check_latest(latest, task_id=task_id)
        set_gripper_check_status("cancelled", error=str(exc), task_id=task_id)
        return latest
    except Exception as exc:
        latest = {
            "success": False,
            "error": str(exc),
            "count": 0,
            "data": [],
            "columns": [],
            "filename": "",
            "server_path": "",
            "task_id": task_id,
            "updated_at": timezone.now().isoformat(),
        }
        set_gripper_check_latest(latest, task_id=task_id)
        set_gripper_check_status("failed", error=str(exc), task_id=task_id)
        return latest


@shared_task(bind=True)
def gripper_check_task(self, config_data):
    """
    后台执行关键轨迹检查（TRAJECTORY CHECK）

    Args:
        config_data: dict，建议传 ISO 字符串时间（start_time/end_time）
    """
    task_id = getattr(self.request, "id", None)
    return _run_gripper_check_task(config_data, task_id=task_id, export_csv=False)


@shared_task(bind=True)
def gripper_check_csv_task(self, config_data):
    """后台执行关键轨迹检查并生成 CSV。"""
    task_id = getattr(self.request, "id", None)
    return _run_gripper_check_task(config_data, task_id=task_id, export_csv=True)
