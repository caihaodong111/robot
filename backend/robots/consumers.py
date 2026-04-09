import json
import re

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .gripper_check_state import get_gripper_check_latest, get_gripper_check_status


TASK_ID_RE = re.compile(r"^[0-9A-Za-z_-]{1,128}$")


class GripperCheckConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        task_id = (self.scope.get("url_route", {}).get("kwargs", {}).get("task_id") or "").strip()
        if not TASK_ID_RE.match(task_id):
            await self.close(code=4400)
            return

        self.task_id = task_id
        self.group_name = f"gripper_check_{task_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._send_snapshot()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return
        if payload.get("type") == "subscribe":
            await self._send_snapshot()

    async def gripper_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "status",
            "data": event["data"],
        }, ensure_ascii=False))

    async def gripper_result(self, event):
        await self.send(text_data=json.dumps({
            "type": "result",
            "data": event["data"],
        }, ensure_ascii=False))

    async def _send_snapshot(self):
        status_payload, latest_payload = await self._load_snapshot(self.task_id)
        if status_payload:
            await self.send(text_data=json.dumps({
                "type": "status",
                "data": status_payload,
            }, ensure_ascii=False))
        if latest_payload:
            await self.send(text_data=json.dumps({
                "type": "result",
                "data": latest_payload,
            }, ensure_ascii=False))

    @database_sync_to_async
    def _load_snapshot(self, task_id):
        return get_gripper_check_status(task_id=task_id), get_gripper_check_latest(task_id=task_id)
