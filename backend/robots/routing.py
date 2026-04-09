from django.urls import re_path

from . import consumers


websocket_urlpatterns = [
    re_path(r"ws/robots/gripper-check/(?P<task_id>[0-9A-Za-z_-]+)/$", consumers.GripperCheckConsumer.as_asgi()),
]
