from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Device, DeviceConfig
from .serializers import DeviceSerializer, DeviceListSerializer, DeviceCreateSerializer, DeviceConfigSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    """设备视图集"""

    def get_queryset(self):
        return Device.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return DeviceListSerializer
        elif self.action == 'create':
            return DeviceCreateSerializer
        return DeviceSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def update_config(self, request, pk=None):
        """更新设备配置"""
        device = self.get_object()
        config = device.config
        serializer = DeviceConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def latest_data(self, request, pk=None):
        """获取设备最新数据"""
        from monitoring.models import SensorData
        device = self.get_object()
        latest_data = device.sensor_data.first()
        if latest_data:
            return Response({
                'device_id': device.device_id,
                'device_name': device.name,
                'temperature': latest_data.temperature,
                'humidity': latest_data.humidity,
                'light_intensity': latest_data.light_intensity,
                'pm25': latest_data.pm25,
                'co2': latest_data.co2,
                'timestamp': latest_data.timestamp,
            })
        return Response({'message': '暂无数据'}, status=status.HTTP_404_NOT_FOUND)


class DeviceToggleStatusView(APIView):
    """设备状态切换视图"""

    def post(self, request, pk):
        try:
            device = Device.objects.get(pk=pk, owner=request.user)
            new_status = request.data.get('status')
            if new_status in ['online', 'offline', 'maintenance']:
                device.status = new_status
                device.last_active = timezone.now()
                device.save()
                return Response({'message': f'设备状态已更新为{new_status}'})
            return Response({'error': '无效的状态值'}, status=status.HTTP_400_BAD_REQUEST)
        except Device.DoesNotExist:
            return Response({'error': '设备不存在'}, status=status.HTTP_404_NOT_FOUND)
