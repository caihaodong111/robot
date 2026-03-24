import threading


class BiCancelledError(Exception):
    """Raised when a BI generation job is cancelled."""


class BiJobRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs = {}  # job_id -> threading.Event

    def register(self, job_id: str) -> threading.Event:
        if not job_id:
            raise ValueError("job_id is required")
        with self._lock:
            evt = self._jobs.get(job_id)
            if evt is None:
                evt = threading.Event()
                self._jobs[job_id] = evt
            return evt

    def unregister(self, job_id: str) -> None:
        if not job_id:
            return
        with self._lock:
            self._jobs.pop(job_id, None)

    def cancel(self, job_id: str) -> bool:
        if not job_id:
            return False
        with self._lock:
            evt = self._jobs.get(job_id)
            if evt is None:
                return False
            evt.set()
            return True

    def is_cancelled(self, job_id: str) -> bool:
        if not job_id:
            return False
        with self._lock:
            evt = self._jobs.get(job_id)
        return bool(evt and evt.is_set())


bi_job_registry = BiJobRegistry()

