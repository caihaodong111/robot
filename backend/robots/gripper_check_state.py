from django.core.cache import cache
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

GRIPPER_CHECK_STATUS_PREFIX = "gripper_check_status"
GRIPPER_CHECK_LATEST_PREFIX = "gripper_check_latest"
GRIPPER_CHECK_CANCEL_PREFIX = "gripper_check_cancel"
GRIPPER_CHECK_ACTIVE_TASK_KEY = "gripper_check_active_task_id"
GRIPPER_CHECK_LAST_TASK_KEY = "gripper_check_last_task_id"
GRIPPER_CHECK_STATUS_TTL = 60 * 60
GRIPPER_CHECK_LATEST_TTL = 60 * 60
GRIPPER_CHECK_CANCEL_TTL = 60 * 60

ACTIVE_STATUSES = {"queued", "running", "exporting", "cancelling"}
TERMINAL_STATUSES = {"idle", "failed", "cancelled"}


def _group_name(task_id):
    task_id = (task_id or "").strip()
    if not task_id:
        return None
    return f"gripper_check_{task_id}"


def _broadcast_event(task_id, event_type, payload):
    group_name = _group_name(task_id)
    if not group_name:
        return
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": f"gripper_{event_type}",
                "data": payload,
            },
        )
    except Exception:
        return


def _task_key(prefix, task_id):
    task_id = (task_id or "").strip()
    if not task_id:
        return prefix
    return f"{prefix}:{task_id}"


def set_gripper_check_status(status_value, error=None, task_id=None, **extra_fields):
    payload = {
        "status": status_value,
        "updated_at": timezone.now().isoformat(),
    }
    if task_id:
        payload["task_id"] = task_id
    if error:
        payload["error"] = error
    if extra_fields:
        payload.update({key: value for key, value in extra_fields.items() if value is not None})

    cache.set(_task_key(GRIPPER_CHECK_STATUS_PREFIX, task_id), payload, timeout=GRIPPER_CHECK_STATUS_TTL)

    if not task_id:
        return payload

    cache.set(GRIPPER_CHECK_LAST_TASK_KEY, task_id, timeout=GRIPPER_CHECK_STATUS_TTL)
    if status_value in ACTIVE_STATUSES:
        cache.set(GRIPPER_CHECK_ACTIVE_TASK_KEY, task_id, timeout=GRIPPER_CHECK_STATUS_TTL)
    elif status_value in TERMINAL_STATUSES:
        active_task_id = get_gripper_check_active_task_id()
        if active_task_id == task_id:
            cache.delete(GRIPPER_CHECK_ACTIVE_TASK_KEY)
        clear_gripper_check_cancel(task_id)

    _broadcast_event(task_id, "status", payload)
    return payload


def set_gripper_check_latest(result, task_id=None):
    resolved_task_id = (task_id or result.get("task_id") or "").strip()
    payload = dict(result)
    if resolved_task_id:
        payload["task_id"] = resolved_task_id
    cache.set(_task_key(GRIPPER_CHECK_LATEST_PREFIX, resolved_task_id), payload, timeout=GRIPPER_CHECK_LATEST_TTL)
    if resolved_task_id:
        cache.set(GRIPPER_CHECK_LAST_TASK_KEY, resolved_task_id, timeout=GRIPPER_CHECK_LATEST_TTL)
        _broadcast_event(resolved_task_id, "result", payload)
    return payload


def get_gripper_check_status(task_id=None):
    resolved_task_id = (task_id or get_gripper_check_active_task_id() or get_gripper_check_last_task_id() or "").strip()
    if not resolved_task_id:
        return None
    return cache.get(_task_key(GRIPPER_CHECK_STATUS_PREFIX, resolved_task_id))


def get_gripper_check_latest(task_id=None):
    resolved_task_id = (task_id or get_gripper_check_last_task_id() or "").strip()
    if not resolved_task_id:
        return None
    return cache.get(_task_key(GRIPPER_CHECK_LATEST_PREFIX, resolved_task_id))


def request_gripper_check_cancel(task_id):
    task_id = (task_id or "").strip()
    if not task_id:
        return False
    cache.set(_task_key(GRIPPER_CHECK_CANCEL_PREFIX, task_id), True, timeout=GRIPPER_CHECK_CANCEL_TTL)
    return True


def is_gripper_check_cancelled(task_id):
    task_id = (task_id or "").strip()
    if not task_id:
        return False
    return bool(cache.get(_task_key(GRIPPER_CHECK_CANCEL_PREFIX, task_id)))


def clear_gripper_check_cancel(task_id):
    task_id = (task_id or "").strip()
    if not task_id:
        return
    cache.delete(_task_key(GRIPPER_CHECK_CANCEL_PREFIX, task_id))


def get_gripper_check_active_task_id():
    return cache.get(GRIPPER_CHECK_ACTIVE_TASK_KEY)


def get_gripper_check_last_task_id():
    return cache.get(GRIPPER_CHECK_LAST_TASK_KEY)
