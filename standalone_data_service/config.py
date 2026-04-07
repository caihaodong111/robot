from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

# Celery / Redis
CELERY_BROKER_URL = "redis://127.0.0.1:6379/15"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/15"

# Local files
WAM_FILE = Path("/Users/caihd/Desktop/sg5.7/设备状态.xlsx")
FILLING_FILE = Path("/Users/caihd/Desktop/sg5.7/MRA1_filling_status.xlsx")
LENZE_FILE = Path("/Users/caihd/Desktop/sg5.7/temperature_min_max_results.xlsx")

# Main database
DB_NAME = "sg"
DB_USER = "sg"
DB_PASSWORD = "123123"
DB_HOST = "20.5.234.198"
DB_PORT = 3306

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

# Independent SQL used only by this standalone service.
# It follows the same high-risk counting口径 as the current ROBOT OVERVIEW:
# read from robot_components where level = 'H', joined with robot_groups.
HIGH_RISK_SQL = """
SELECT
    COALESCE(NULLIF(g.name, ''), NULLIF(g.`key`, ''), 'UNKNOWN') AS group_name,
    COUNT(*) AS high_risk_count
FROM robot_components rc
LEFT JOIN robot_groups g ON g.id = rc.group_id
WHERE rc.level = 'H'
GROUP BY COALESCE(NULLIF(g.name, ''), NULLIF(g.`key`, ''), 'UNKNOWN')
ORDER BY high_risk_count DESC, group_name ASC
LIMIT 8
"""

OVERVIEW_OUTPUT_FILE = OUTPUT_DIR / "overview_snapshot.json"
RUN_META_OUTPUT_FILE = OUTPUT_DIR / "last_run_meta.json"
