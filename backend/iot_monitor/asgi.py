"""
ASGI config for iot_monitor project.
"""

import os

# 首先设置环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iot_monitor.settings")

# 导入get_asgi_application
from django.core.asgi import get_asgi_application

# 初始化Django应用，确保应用已完全初始化
django_asgi_app = get_asgi_application()

# 延迟导入channels相关模块和路由
from channels.routing import ProtocolTypeRouter
from channels.auth import AuthMiddlewareStack

# 定义一个简单的ASGI应用，避免在初始化时导入模型
class LazyWebSocketApp:
    def __init__(self):
        self.websocket_application = None
    
    async def __call__(self, scope, receive, send):
        if self.websocket_application is None:
            # 只在第一次请求时才导入路由和URLRouter
            from channels.routing import URLRouter
            from monitoring.routing import websocket_urlpatterns
            
            # 创建WebSocket应用
            self.websocket_application = AuthMiddlewareStack(
                URLRouter(
                    websocket_urlpatterns
                )
            )
        
        # 处理请求
        return await self.websocket_application(scope, receive, send)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # 使用懒加载应用处理WebSocket请求
    "websocket": LazyWebSocketApp(),
})
