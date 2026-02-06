"""
初始化编辑认证管理员的 Django 管理命令

用法:
    python manage.py init_edit_auth
    python manage.py init_edit_auth --username admin --password admin123
"""
from django.core.management.base import BaseCommand, CommandError
from robots.models import EditAuthUser


class Command(BaseCommand):
    help = '初始化编辑认证管理员账号'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='管理员用户名（默认: admin）',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='管理员密码（默认: admin123）',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='如果用户已存在，重置密码',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        reset = options['reset']

        try:
            user, created = EditAuthUser.objects.get_or_create(
                username=username,
                defaults={'is_active': True}
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ 成功创建编辑认证管理员账号\n'
                        f'  用户名: {username}\n'
                        f'  密码: {password}'
                    )
                )
            elif reset:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ 成功重置编辑认证管理员密码\n'
                        f'  用户名: {username}\n'
                        f'  新密码: {password}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'! 用户 "{username}" 已存在，如需重置密码请使用 --reset 参数'
                    )
                )
                self.stdout.write(
                    f'  当前状态: {"启用" if user.is_active else "禁用"}\n'
                    f'  创建时间: {user.created_at.strftime("%Y-%m-%d %H:%M:%S")}\n'
                    f'  最后登录: {user.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if user.last_login_at else "从未登录"}'
                )

        except Exception as e:
            raise CommandError(f'创建/更新管理员账号失败: {e}')
