"""
机器人组件编辑认证视图

提供基于数据库的用户名/密码验证接口，用于保护编辑功能
"""
import logging
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_edit_credentials(request):
    """
    验证编辑权限的凭据（从数据库验证）

    请求体:
    {
        "username": "Keyuser",
        "password": "keyuser123"
    }

    返回:
    {
        "success": true,
        "message": "验证成功",
        "sessionVersion": 1  // 会话版本号
    }
    """
    from .models import EditAuthUser, EditSessionVersion

    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response({
            'success': False,
            'error': '用户名和密码不能为空'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 从数据库验证凭据
    user = EditAuthUser.verify_credentials(username, password)

    if user:
        logger.info(f"Edit authentication success for user: {username}")
        # 获取当前会话版本
        session_version = EditSessionVersion.get_current_version()
        return Response({
            'success': True,
            'message': '验证成功',
            'sessionVersion': session_version,
            'user': {
                'username': user.username,
                'last_login': user.last_login_at.isoformat() if user.last_login_at else None
            }
        })

    logger.warning(f"Edit authentication failed for user: {username}")
    return Response({
        'success': False,
        'error': '用户名或密码错误'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_edit_auth_status(request):
    """
    获取编辑认证状态（前端用于检查是否需要重新登录）

    查询参数:
        version: 客户端存储的会话版本号

    返回:
    {
        "required": true,  // 是否需要认证
        "valid": false     // 会话是否有效
    }
    """
    from .models import EditSessionVersion

    client_version = request.query_params.get('version')
    is_valid = EditSessionVersion.check_version(client_version)

    return Response({
        'required': True,
        'valid': is_valid,
        'currentVersion': EditSessionVersion.get_current_version()
    })


@api_view(['POST'])
def increment_edit_session_version(request):
    """
    增加编辑会话版本号（使所有现有会话失效）

    通常在定时任务数据刷新后调用

    请求体:
    {
        "reason": "scheduled refresh"  // 可选：刷新原因
    }

    返回:
    {
        "success": true,
        "newVersion": 2
    }
    """
    from .models import EditSessionVersion

    reason = request.data.get('reason', 'manual')[:64]
    new_version = EditSessionVersion.increment_version(updated_by=reason)

    logger.info(f"Edit session version incremented to {new_version} by: {reason}")
    return Response({
        'success': True,
        'newVersion': new_version,
        'message': '所有编辑会话已失效，用户需要重新登录'
    })


@api_view(['GET'])
def list_edit_users(request):
    """
    获取所有编辑认证用户列表

    返回:
    [
        {
            "username": "Keyuser",
            "is_active": true,
            "created_at": "2026-02-06T10:00:00Z",
            "last_login_at": "2026-02-06T12:30:00Z"
        }
    ]
    """
    from .models import EditAuthUser

    users = EditAuthUser.objects.all()
    data = [
        {
            'username': user.username,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
        }
        for user in users
    ]

    return Response(data)


@api_view(['POST'])
def change_edit_password(request):
    """
    修改编辑认证用户的密码

    请求体:
    {
        "username": "Keyuser",
        "old_password": "keyuser123",  // 可选，如果不提供则不验证旧密码
        "new_password": "newpassword123"
    }

    返回:
    {
        "success": true,
        "message": "密码修改成功"
    }
    """
    from .models import EditAuthUser

    username = request.data.get('username', '').strip()
    old_password = request.data.get('old_password', '')
    new_password = request.data.get('new_password', '')

    if not username or not new_password:
        return Response({
            'success': False,
            'error': '用户名和新密码不能为空'
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) < 6:
        return Response({
            'success': False,
            'error': '新密码长度至少为 6 位'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = EditAuthUser.objects.get(username=username)
    except EditAuthUser.DoesNotExist:
        return Response({
            'success': False,
            'error': '用户不存在'
        }, status=status.HTTP_404_NOT_FOUND)

    # 如果提供了旧密码，先验证旧密码
    if old_password and not user.check_password(old_password):
        logger.warning(f"Password change failed for user {username}: old password incorrect")
        return Response({
            'success': False,
            'error': '原密码错误'
        }, status=status.HTTP_401_UNAUTHORIZED)

    user.set_password(new_password)
    user.save()

    logger.info(f"Password changed successfully for user: {username}")
    return Response({
        'success': True,
        'message': '密码修改成功'
    })


@api_view(['POST'])
def create_edit_user(request):
    """
    创建新的编辑认证用户

    请求体:
    {
        "username": "operator",
        "password": "password123"
    }

    返回:
    {
        "success": true,
        "message": "用户创建成功"
    }
    """
    from .models import EditAuthUser

    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response({
            'success': False,
            'error': '用户名和密码不能为空'
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 6:
        return Response({
            'success': False,
            'error': '密码长度至少为 6 位'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = EditAuthUser(username=username, is_active=True)
        user.set_password(password)
        user.save()

        logger.info(f"New edit user created: {username}")
        return Response({
            'success': True,
            'message': '用户创建成功',
            'user': {
                'username': user.username,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        if 'unique constraint' in str(e).lower() or 'duplicate' in str(e).lower():
            return Response({
                'success': False,
                'error': '用户名已存在'
            }, status=status.HTTP_400_BAD_REQUEST)
        raise
