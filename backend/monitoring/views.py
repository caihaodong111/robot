from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, Max, Min, Count
from django.db.models.functions import TruncHour, TruncDay
from django.utils import timezone
from datetime import datetime, timedelta
from .models import SensorData, DataSummary
from .serializers import SensorDataSerializer, SensorDataCreateSerializer, DataSummarySerializer, DataQuerySerializer
from devices.models import Device

import pandas as pd
from openpyxl import Workbook
from django.http import HttpResponse
import json


class SensorDataViewSet(viewsets.ReadOnlyModelViewSet):
    """传感器数据视图集"""
    serializer_class = SensorDataSerializer

    def get_queryset(self):
        device_id = self.request.query_params.get('device_id')
        limit = self.request.query_params.get('limit', 100)

        queryset = SensorData.objects.filter(
            device__owner=self.request.user
        ).select_related('device')

        if device_id:
            queryset = queryset.filter(device_id=device_id)

        return queryset[:int(limit)]

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """获取所有设备的最新数据"""
        devices = Device.objects.filter(owner=request.user)
        result = []

        for device in devices:
            latest = device.sensor_data.first()
            if latest:
                result.append({
                    'device_id': device.device_id,
                    'device_name': device.name,
                    'device_type': device.device_type,
                    'location': device.location,
                    'status': device.status,
                    'temperature': latest.temperature,
                    'humidity': latest.humidity,
                    'light_intensity': latest.light_intensity,
                    'pm25': latest.pm25,
                    'co2': latest.co2,
                    'timestamp': latest.timestamp,
                })

        return Response(result)


class DataUploadView(APIView):
    """数据上报视图"""

    def post(self, request):
        """接收设备上报的数据"""
        serializer = SensorDataCreateSerializer(data=request.data)
        if serializer.is_valid():
            sensor_data = serializer.save()

            # 检查报警规则
            from alerts.tasks import check_alert_rules
            check_alert_rules.delay(sensor_data.id)

            # 更新设备最后活跃时间
            device = sensor_data.device
            device.last_active = timezone.now()
            device.status = 'online'
            device.save()

            return Response({
                'message': '数据上报成功',
                'data_id': sensor_data.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataQueryView(APIView):
    """数据查询视图"""

    def get(self, request):
        """查询历史数据"""
        serializer = DataQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        device_id = serializer.validated_data['device_id']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']

        try:
            device = Device.objects.get(id=device_id, owner=request.user)
        except Device.DoesNotExist:
            return Response({'error': '设备不存在'}, status=status.HTTP_404_NOT_FOUND)

        queryset = SensorData.objects.filter(
            device=device,
            timestamp__range=[start_time, end_time],
            is_valid=True
        ).order_by('-timestamp')

        # 分页
        page = self.request.query_params.get('page', 1)
        page_size = self.request.query_params.get('page_size', 50)

        start = (int(page) - 1) * int(page_size)
        end = start + int(page_size)

        data = queryset[start:end]
        total = queryset.count()

        return Response({
            'total': total,
            'page': int(page),
            'page_size': int(page_size),
            'data': SensorDataSerializer(data, many=True).data
        })


class DataExportView(APIView):
    """数据导出视图"""

    def get(self, request):
        """导出数据为Excel"""
        device_id = request.query_params.get('device_id')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        export_type = request.query_params.get('type', 'excel')

        if not all([device_id, start_time, end_time]):
            return Response({'error': '缺少必要参数'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = Device.objects.get(id=device_id, owner=request.user)
        except Device.DoesNotExist:
            return Response({'error': '设备不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 解析时间
        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        queryset = SensorData.objects.filter(
            device=device,
            timestamp__range=[start_time, end_time],
            is_valid=True
        ).order_by('timestamp')

        if export_type == 'excel':
            return self._export_excel(queryset, device)
        else:
            return self._export_csv(queryset, device)

    def _export_excel(self, queryset, device):
        """导出为Excel"""
        data = list(queryset.values(
            'timestamp', 'temperature', 'humidity',
            'light_intensity', 'pm25', 'co2'
        ))

        df = pd.DataFrame(data)
        output = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        output['Content-Disposition'] = f'attachment; filename="{device.device_id}_{timezone.now().strftime("%Y%m%d")}.xlsx"'

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='传感器数据', index=False)

        return output

    def _export_csv(self, queryset, device):
        """导出为CSV"""
        import csv
        output = HttpResponse(content_type='text/csv')
        output['Content-Disposition'] = f'attachment; filename="{device.device_id}_{timezone.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(output)
        writer.writerow(['时间', '温度', '湿度', '光照强度', 'PM2.5', 'CO2'])

        for data in queryset:
            writer.writerow([
                data.timestamp,
                data.temperature,
                data.humidity,
                data.light_intensity,
                data.pm25,
                data.co2
            ])

        return output


class RealTimeDataView(APIView):
    """实时数据视图"""

    def get(self, request, device_id):
        """获取指定设备的实时数据"""
        try:
            device = Device.objects.get(id=device_id, owner=request.user)
        except Device.DoesNotExist:
            return Response({'error': '设备不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 获取最近的数据点
        recent_data = device.sensor_data.all()[:100]
        serializer = SensorDataSerializer(recent_data, many=True)

        return Response({
            'device': {
                'id': device.id,
                'name': device.name,
                'device_id': device.device_id,
                'type': device.device_type,
                'location': device.location,
                'status': device.status,
            },
            'data': serializer.data
        })


class DataStatisticsView(APIView):
    """数据统计视图"""

    def get(self, request, device_id):
        """获取设备数据统计"""
        try:
            device = Device.objects.get(id=device_id, owner=request.user)
        except Device.DoesNotExist:
            return Response({'error': '设备不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 时间范围
        time_range = request.query_params.get('range', '24h')  # 24h, 7d, 30d
        now = timezone.now()

        if time_range == '24h':
            start_time = now - timedelta(hours=24)
        elif time_range == '7d':
            start_time = now - timedelta(days=7)
        elif time_range == '30d':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)

        queryset = SensorData.objects.filter(
            device=device,
            timestamp__gte=start_time,
            is_valid=True
        )

        stats = queryset.aggregate(
            avg_temp=Avg('temperature'),
            max_temp=Max('temperature'),
            min_temp=Min('temperature'),
            avg_humidity=Avg('humidity'),
            max_humidity=Max('humidity'),
            min_humidity=Min('humidity'),
            avg_pm25=Avg('pm25'),
            max_pm25=Max('pm25'),
            avg_co2=Avg('co2'),
            max_co2=Max('co2'),
            data_count=Count('id')
        )

        # 按小时统计
        hourly_stats = queryset.annotate(
            hour=TruncHour('timestamp')
        ).values('hour').annotate(
            avg_temp=Avg('temperature'),
            avg_humidity=Avg('humidity'),
            avg_pm25=Avg('pm25'),
        ).order_by('hour')

        return Response({
            'summary': stats,
            'hourly': list(hourly_stats),
            'time_range': time_range
        })
