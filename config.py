from pathlib import Path

# Application Settings
APP_NAME = "File Management System"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1024x768"

# Database Settings
DB_NAME = "fms.db"
DB_PATH = Path(DB_NAME)

# File Extensions and Types Mapping
FILE_TYPES = {
    ".pdf": "PDF",
    ".dwg": "DWG",
    ".doc": "DOC",
    ".docx": "DOC",
    ".xls": "XLS",
    ".xlsx": "XLS",
    ".txt": "TXT",
    ".csv": "CSV",
    ".zip": "ZIP",
    ".rar": "RAR"
}

# Metadata Fields
METADATA_FIELDS = [
    "department",
    "file_type",
    "revision",
    "drawing_type",
    "plant_area",
    "issue_status",
    "equipment_included"
]

# Department Options (if using predefined list)
DEPARTMENTS = [
    "Electrical",
    "Mechanical",
    "Civil",
    "Structural",
    "Process",
    "Instrumentation",
    "Document Control"
]

# Logging Configuration
LOG_DIR = Path("logs")
LOG_BACKUP_COUNT = 4  # Number of weeks to keep log backups
LOG_ROTATION = 'W0'  # Weekly rotation on Monday

# UI Theme Settings
UI_THEME = "litera"  # ttkbootstrap theme
UI_PADDING = 10
UI_BUTTON_WIDTH = 15

# Search Settings
MAX_RECENT_PROJECTS = 5
SEARCH_RESULTS_PER_PAGE = 50