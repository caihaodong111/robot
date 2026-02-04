"""
定时导入 weeklyresult.csv 文件到数据库
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from robots.weekly_result_service import import_weeklyresult_csv, get_latest_weeklyresult_csv


class Command(BaseCommand):
    help = '从指定路径导入最新的 weeklyresult.csv 文件到数据库（用于定时任务）'

    # 配置参数
    def add_arguments(self, parser):
        parser.add_argument(
            '--folder-path',
            type=str,
            default='/Users/caihd/Desktop/sg',
            help='CSV 文件所在文件夹路径',
        )
        parser.add_argument(
            '--project',
            type=str,
            default='reuse',
            help='项目名称 (reuse, engine-robot, v206, V214&254)',
        )
        parser.add_argument(
            '--file-path',
            type=str,
            default=None,
            help='直接指定 CSV 文件路径（如果指定则忽略 folder-path 和 project）',
        )
        parser.add_argument(
            '--clear-old',
            action='store_true',
            help='导入前清空旧的周结果数据',
        )

    def handle(self, *args, **options):
        folder_path = options.get('folder_path')
        project = options.get('project')
        file_path = options.get('file_path')
        clear_old = options.get('clear_old')

        self.stdout.write(self.style.SUCCESS(f'开始导入周结果数据...'))
        self.stdout.write(f'  时间: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'  项目: {project}')
        self.stdout.write(f'  文件夹: {folder_path}')

        try:
            # 如果指定了清空旧数据
            if clear_old:
                from robots.models import WeeklyResult
                deleted_count = WeeklyResult.objects.all().delete()[0]
                self.stdout.write(self.style.WARNING(f'  已清空 {deleted_count} 条旧数据'))

            # 执行导入
            result = import_weeklyresult_csv(
                file_path=file_path,
                folder_path=folder_path,
                project=project,
            )

            # 输出结果
            self.stdout.write(self.style.SUCCESS(f'  导入成功!'))
            self.stdout.write(f'  源文件: {result["source_file"]}')
            self.stdout.write(f'  新增记录: {result["records_imported"]}')
            self.stdout.write(f'  更新记录: {result["records_updated"]}')
            self.stdout.write(f'  总记录数: {result["total_records"]}')
            if result.get('week_start') and result.get('week_end'):
                self.stdout.write(f'  周范围: {result["week_start"]} ~ {result["week_end"]}')

            return result

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f'  文件未找到: {e}'))
            raise
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  导入失败: {e}'))
            raise
