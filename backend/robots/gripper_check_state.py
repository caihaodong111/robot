from django.core.cache import cache
from django.utils import timezone

GRIPPER_CHECK_STATUS_KEY = "gripper_check_status"
GRIPPER_CHECK_STATUS_TTL = 60 * 60
GRIPPER_CHECK_LATEST_KEY = "gripper_check_latest"
GRIPPER_CHECK_LATEST_TTL = 60 * 60


def set_gripper_check_status(status_value, error=None, task_id=None):
    payload = {
        "status": status_value,
        "updated_at": timezone.now().isoformat(),
    }
    if task_id:
        payload["task_id"] = task_id
    if error:
        payload["error"] = error
    cache.set(GRIPPER_CHECK_STATUS_KEY, payload, timeout=GRIPPER_CHECK_STATUS_TTL)


def set_gripper_check_latest(result):
    cache.set(GRIPPER_CHECK_LATEST_KEY, result, timeout=GRIPPER_CHECK_LATEST_TTL)


def get_gripper_check_status():
    return cache.get(GRIPPER_CHECK_STATUS_KEY)


def get_gripper_check_latest():
    return cache.get(GRIPPER_CHECK_LATEST_KEY)

