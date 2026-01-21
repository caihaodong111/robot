"""
Import robot data from bb MySQL database into sg project
"""
import pymysql
from django.core.management.base import BaseCommand
from django.utils import timezone
from robots.models import RobotGroup, RobotComponent


class Command(BaseCommand):
    help = 'Import robots as33_020rb_400 and e212_080rb_100 into engine group'

    # MySQL connection configuration (same as bb project)
    DB_CONFIG = {
        'host': '20.24.202.76',
        'port': 3306,
        'user': 'bb',
        'password': 'Cai123123',
        'database': 'bb',
        'charset': 'utf8mb4'
    }

    # Robot definitions
    ROBOTS = {
        'as33_020rb_400': {
            'name': 'AS33-020RB-400',
            'type_spec': 'KR210_R2700_Quantec',
            'tech': '焊接',
            'table_name': 'as33_020rb_400'
        },
        'e212_080rb_100': {
            'name': 'E212-080RB-100',
            'type_spec': 'KR120_R2700_Quantec',
            'tech': '搬运',
            'table_name': 'e212_080rb_100'
        }
    }

    def handle(self, *args, **options):
        # Get or create engine group
        engine_group, created = RobotGroup.objects.get_or_create(
            key='engine',
            defaults={
                'name': 'engine',
                'expected_total': 2
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created engine group'))

        # Import each robot
        for table_name, robot_info in self.ROBOTS.items():
            self.import_robot(engine_group, table_name, robot_info)

    def import_robot(self, group, table_name, robot_info):
        """Import a single robot"""
        part_no = table_name.upper()

        # Check if robot already exists
        existing = RobotComponent.objects.filter(part_no=part_no).first()
        if existing:
            self.stdout.write(f'Robot {part_no} already exists, skipping...')
            return

        # Connect to MySQL and get data
        conn = pymysql.connect(**self.DB_CONFIG)
        try:
            with conn.cursor() as cursor:
                # Get sample data to generate checks
                cursor.execute(f'SELECT * FROM `{table_name}` LIMIT 100')
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                # Generate checks based on data
                checks = self.generate_checks_from_data(columns, rows)

                # Get reference from first row
                cursor.execute(f'SELECT DISTINCT ref FROM `{table_name}` LIMIT 1')
                ref_result = cursor.fetchone()
                reference_no = ref_result[0] if ref_result else '20240708-20240731'

                # Create robot component
                robot = RobotComponent.objects.create(
                    group=group,
                    robot_id=part_no,
                    name=robot_info['name'],
                    part_no=part_no,
                    reference_no=reference_no,
                    number=0,
                    type_spec=robot_info['type_spec'],
                    tech=robot_info['tech'],
                    mark=0,
                    level='L',
                    status='online',
                    checks=checks,
                    risk_score=25,
                    risk_level='low',
                    battery=85,
                    health=92,
                    motor_temp=55,
                    network_latency=45,
                    last_seen=timezone.now()
                )

                self.stdout.write(self.style.SUCCESS(f'Created robot: {part_no}'))

        finally:
            conn.close()

    def generate_checks_from_data(self, columns, rows):
        """Generate checks data from actual robot data"""
        checks = {}

        # Axis labels and checks
        axis_labels = {
            'A1': '供电/线束',
            'A2': '温度/散热',
            'A3': '通信/网络',
            'A4': '传感器/对位',
            'A5': '抓手/执行器',
            'A6': '控制/程序',
            'A7': '安全/急停'
        }

        # Temperature thresholds
        temp_thresholds = {
            'Tem_1': 70,  # A1
            'Tem_2': 70,  # A2
            'Tem_3': 70,  # A3
            'Tem_4': 70,  # A4
            'Tem_5': 70,  # A5
            'Tem_6': 70,  # A6
            'Tem_7': 70   # A7
        }

        # Current thresholds for overcurrent check
        current_thresholds = {
            'Curr_A1': ('MAXCurr_A1', 0.95),
            'Curr_A2': ('MAXCurr_A2', 0.95),
            'Curr_A3': ('MAXCurr_A3', 0.95),
            'Curr_A4': ('MAXCurr_A4', 0.95),
            'Curr_A5': ('MAXCurr_A5', 0.95),
            'Curr_A6': ('MAXCurr_A6', 0.95),
            'Curr_E1': ('MAXCurr_E1', 0.95)
        }

        for i in range(1, 8):
            axis = f'A{i}' if i <= 6 else 'A7'
            temp_col = f'Tem_{i}'
            curr_col = f'Curr_{axis}'

            # Check temperature
            temp_ok = True
            if temp_col in columns:
                for row in rows:
                    col_idx = columns.index(temp_col)
                    temp_val = row[col_idx]
                    if temp_val and temp_val > temp_thresholds.get(temp_col, 70):
                        temp_ok = False
                        break

            # Check current
            curr_ok = True
            if curr_col in columns:
                for row in rows:
                    col_idx = columns.index(curr_col)
                    curr_val = row[col_idx]
                    if curr_col in current_thresholds:
                        max_col, threshold = current_thresholds[curr_col]
                        if max_col in columns:
                            max_idx = columns.index(max_col)
                            max_val = row[max_idx]
                            if max_val and abs(curr_val) > abs(max_val) * threshold:
                                curr_ok = False
                                break

            checks[axis] = {
                'ok': temp_ok and curr_ok,
                'label': axis_labels.get(axis, axis)
            }

        return checks
