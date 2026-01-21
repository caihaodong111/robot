"""
Import robot axis data from bb MySQL database to local SQLite
"""
import pymysql
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from robots.models import RobotAxisData


class Command(BaseCommand):
    help = 'Import robot axis data from bb MySQL database'

    # MySQL connection configuration
    DB_CONFIG = {
        'host': '20.24.202.76',
        'port': 3306,
        'user': 'bb',
        'password': 'Cai123123',
        'database': 'bb',
        'charset': 'utf8mb4'
    }

    # Tables to import
    TABLES = {
        'as33_020rb_400': 'AS33_020RB_400',
        'e212_080rb_100': 'E212_080RB_100'
    }

    def handle(self, *args, **options):
        for table_name, part_no in self.TABLES.items():
            self.import_table(table_name, part_no)

    def import_table(self, table_name, part_no):
        """Import data from a single table"""
        self.stdout.write(f'Importing {part_no} from {table_name}...')

        conn = pymysql.connect(**self.DB_CONFIG)
        try:
            # Get all data from the table
            query = f'SELECT * FROM `{table_name}` ORDER BY `Timestamp`'
            df = pd.read_sql(query, conn)

            if df.empty:
                self.stdout.write(self.style.WARNING(f'No data found in {table_name}'))
                return

            self.stdout.write(f'  Found {len(df)} records')

            # Clear existing data for this robot
            deleted_count = RobotAxisData.objects.filter(part_no=part_no).delete()
            if deleted_count[0] > 0:
                self.stdout.write(f'  Deleted {deleted_count[0]} old records')

            # Prepare data for bulk insert
            records = []
            for _, row in df.iterrows():
                records.append(self.create_record(part_no, row))

            # Bulk create
            RobotAxisData.objects.bulk_create(records, batch_size=1000)

            self.stdout.write(self.style.SUCCESS(f'  Created {len(records)} records for {part_no}'))

        finally:
            conn.close()

    def create_record(self, part_no, row):
        """Create a RobotAxisData instance from a row"""
        # Map column names from MySQL to model fields
        field_map = {
            # A1-A6 currents
            'Curr_A1': 'curr_a1', 'Curr_A2': 'curr_a2', 'Curr_A3': 'curr_a3',
            'Curr_A4': 'curr_a4', 'Curr_A5': 'curr_a5', 'Curr_A6': 'curr_a6',
            'Curr_E1': 'curr_e1',
            # Max currents
            'MAXCurr_A1': 'max_curr_a1', 'MAXCurr_A2': 'max_curr_a2', 'MAXCurr_A3': 'max_curr_a3',
            'MAXCurr_A4': 'max_curr_a4', 'MAXCurr_A5': 'max_curr_a5', 'MAXCurr_A6': 'max_curr_a6',
            'MAXCurr_E1': 'max_curr_e1',
            # Min currents
            'MinCurr_A1': 'min_curr_a1', 'MinCurr_A2': 'min_curr_a2', 'MinCurr_A3': 'min_curr_a3',
            'MinCurr_A4': 'min_curr_a4', 'MinCurr_A5': 'min_curr_a5', 'MinCurr_A6': 'min_curr_a6',
            'MinCurr_E1': 'min_curr_e1',
            # Temperatures
            'Tem_1': 'tem_1', 'Tem_2': 'tem_2', 'Tem_3': 'tem_3',
            'Tem_4': 'tem_4', 'Tem_5': 'tem_5', 'Tem_6': 'tem_6', 'Tem_7': 'tem_7',
            # Positions
            'AxisP1': 'axisp1', 'AxisP2': 'axisp2', 'AxisP3': 'axisp3',
            'AxisP4': 'axisp4', 'AxisP5': 'axisp5', 'AxisP6': 'axisp6', 'AxisP7': 'axisp7',
            # Speed
            'Speed1': 'speed1', 'Speed2': 'speed2', 'Speed3': 'speed3',
            'Speed4': 'speed4', 'Speed5': 'speed5', 'Speed6': 'speed6', 'Speed7': 'speed7',
            # Torque
            'Torque1': 'torque1', 'Torque2': 'torque2', 'Torque3': 'torque3',
            'Torque4': 'torque4', 'Torque5': 'torque5', 'Torque6': 'torque6', 'Torque7': 'torque7',
            # Following error
            'Fol1': 'fol1', 'Fol2': 'fol2', 'Fol3': 'fol3',
            'Fol4': 'fol4', 'Fol5': 'fol5', 'Fol6': 'fol6', 'Fol7': 'fol7',
        }

        # Create record dict
        record_data = {
            'part_no': part_no,
            'timestamp': row.get('Timestamp'),
            'snr_c': int(row.get('SNR_C', 0)) if pd.notna(row.get('SNR_C')) else None,
            'p_name': row.get('P_name'),
            'ref': row.get('ref'),
            'robot_stop': bool(row.get('robot_stop', False)),
        }

        # Map all fields
        for mysql_col, model_field in field_map.items():
            value = row.get(mysql_col)
            if pd.notna(value):
                record_data[model_field] = value

        return RobotAxisData(**record_data)
