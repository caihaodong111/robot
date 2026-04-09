from monitoring.routing import websocket_urlpatterns as monitoring_websocket_urlpatterns
from robots.routing import websocket_urlpatterns as robots_websocket_urlpatterns


websocket_urlpatterns = [
    *monitoring_websocket_urlpatterns,
    *robots_websocket_urlpatterns,
]
