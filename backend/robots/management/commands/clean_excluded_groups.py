"""
清理被排除的车间数据

删除以下车间及其相关的机器人组件数据：
- 空车间 (key='')
- MRA1 BS
- 未分配
"""
from django.core.management.base import BaseCommand
from django.db.models import Count


class Command(BaseCommand):
    help = '清理被排除的车间数据（空、MRA1 BS、未分配）'

    # 排除的车间 key 列表
    EXCLUDED_GROUP_KEYS = ['', '(空)', 'MRA1 BS', '未分配']

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='只显示将要删除的数据，不实际执行删除',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='强制执行删除，不需要确认',
        )

    def handle(self, *args, **options):
        from robots.models import RobotGroup, RobotComponent, RiskEvent

        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        self.stdout.write(self.style.WARNING('开始清理被排除的车间数据...'))
        self.stdout.write(f'排除的车间 key: {self.EXCLUDED_GROUP_KEYS}')
        self.stdout.write('')

        # 获取要删除的车间
        groups_to_delete = RobotGroup.objects.filter(key__in=self.EXCLUDED_GROUP_KEYS)

        if not groups_to_delete.exists():
            self.stdout.write(self.style.SUCCESS('没有找到需要删除的车间'))
            return

        # 统计信息
        total_groups = groups_to_delete.count()
        total_components = RobotComponent.objects.filter(group__key__in=self.EXCLUDED_GROUP_KEYS).count()
        total_risk_events = RiskEvent.objects.filter(group__key__in=self.EXCLUDED_GROUP_KEYS).count()

        # 显示将要删除的数据
        self.stdout.write(self.style.WARNING(f'将要删除的车间数量: {total_groups}'))
        for group in groups_to_delete:
            component_count = group.components.count()
            self.stdout.write(f'  - {group.name} (key="{group.key}"): {component_count} 个机器人组件')

        self.stdout.write(self.style.WARNING(f'将要删除的机器人组件: {total_components}'))
        self.stdout.write(self.style.WARNING(f'将要删除的风险事件: {total_risk_events}'))
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('[DRY RUN] 模拟运行完成，没有实际删除数据'))
            return

        # 确认删除
        if not force:
            confirm = input('确认删除以上数据吗？(输入 yes 确认): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('已取消操作'))
                return

        # 执行删除
        self.stdout.write('正在删除...')

        # 先删除风险事件
        risk_events_deleted, _ = RiskEvent.objects.filter(group__key__in=self.EXCLUDED_GROUP_KEYS).delete()
        self.stdout.write(f'  - 已删除 {risk_events_deleted} 条风险事件')

        # 再删除机器人组件
        components_deleted, _ = RobotComponent.objects.filter(group__key__in=self.EXCLUDED_GROUP_KEYS).delete()
        self.stdout.write(f'  - 已删除 {components_deleted} 个机器人组件')

        # 最后删除车间
        groups_deleted, _ = groups_to_delete.delete()
        self.stdout.write(f'  - 已删除 {groups_deleted} 个车间')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('清理完成！'))
