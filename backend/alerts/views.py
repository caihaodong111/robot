from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Q
from .models import AlertRule, AlertRecord, NotificationConfig
from .serializers import (
    AlertRuleSerializer, AlertRecordSerializer,
    AlertRecordUpdateSerializer, NotificationConfigSerializer
)


class AlertRuleViewSet(viewsets.ModelViewSet):
    """报警规则视图集"""
    serializer_class = AlertRuleSerializer

    def get_queryset(self):
        return AlertRule.objects.filter(device__owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """启用/禁用报警规则"""
        rule = self.get_object()
        rule.enabled = not rule.enabled
        rule.save()
        return Response({'enabled': rule.enabled})


class AlertRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """报警记录视图集"""
    serializer_class = AlertRecordSerializer

    def get_queryset(self):
        queryset = AlertRecord.objects.filter(
            device__owner=self.request.user
        ).select_related('device', 'rule', 'acknowledged_by', 'resolved_by')

        # 过滤条件
        status_filter = self.request.query_params.get('status')
        severity = self.request.query_params.get('severity')
        device_id = self.request.query_params.get('device_id')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if severity:
            queryset = queryset.filter(severity=severity)
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        return queryset.order_by('-triggered_at')

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """获取待处理的报警"""
        pending_alerts = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(pending_alerts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取报警统计"""
        queryset = AlertRecord.objects.filter(device__owner=self.request.user)

        stats = queryset.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            acknowledged=Count('id', filter=Q(status='acknowledged')),
            resolved=Count('id', filter=Q(status='resolved')),
        )

        # 按严重程度统计
        severity_stats = {}
        for severity in ['low', 'medium', 'high', 'critical']:
            severity_stats[severity] = queryset.filter(severity=severity).count()

        return Response({
            'summary': stats,
            'by_severity': severity_stats
        })


class AlertAcknowledgeView(APIView):
    """报警确认视图"""

    def post(self, request, pk):
        """确认报警"""
        try:
            alert = AlertRecord.objects.get(
                pk=pk,
                device__owner=request.user,
                status='pending'
            )
        except AlertRecord.DoesNotExist:
            return Response({'error': '报警不存在或已处理'}, status=status.HTTP_404_NOT_FOUND)

        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.notes = request.data.get('notes', '')
        alert.save()

        return Response({'message': '报警已确认'})


class AlertResolveView(APIView):
    """报警解决视图"""

    def post(self, request, pk):
        """解决报警"""
        try:
            alert = AlertRecord.objects.get(
                pk=pk,
                device__owner=request.user
            )
        except AlertRecord.DoesNotExist:
            return Response({'error': '报警不存在'}, status=status.HTTP_404_NOT_FOUND)

        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.notes = request.data.get('notes', '')
        alert.save()

        return Response({'message': '报警已解决'})


class AlertStatisticsView(APIView):
    """报警统计视图"""

    def get(self, request):
        """获取报警统计数据"""
        user = request.user
        time_range = request.query_params.get('range', '7d')

        from datetime import timedelta
        if time_range == '24h':
            start_time = timezone.now() - timedelta(hours=24)
        elif time_range == '7d':
            start_time = timezone.now() - timedelta(days=7)
        elif time_range == '30d':
            start_time = timezone.now() - timedelta(days=30)
        else:
            start_time = timezone.now() - timedelta(days=7)

        queryset = AlertRecord.objects.filter(
            device__owner=user,
            triggered_at__gte=start_time
        )

        # 总体统计
        total_stats = queryset.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            resolved=Count('id', filter=Q(status='resolved')),
        )

        # 按设备统计
        device_stats = queryset.values('device__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # 按严重程度统计
        severity_stats = {}
        for severity in ['low', 'medium', 'high', 'critical']:
            severity_stats[severity] = queryset.filter(severity=severity).count()

        # 获取最近的报警记录
        recent_alerts = queryset.order_by('-triggered_at')[:10]
        recent_alerts_data = []
        for alert in recent_alerts:
            recent_alerts_data.append({
                'id': alert.id,
                'message': alert.message,
                'severity': alert.severity,
                'device_name': alert.device.name,
                'current_value': alert.current_value,
                'status': alert.status,
                'triggered_at': alert.triggered_at.isoformat()
            })

        return Response({
            'time_range': time_range,
            'total_stats': total_stats,
            'device_stats': list(device_stats),
            'severity_stats': severity_stats,
            'recent_alerts': recent_alerts_data
        })
