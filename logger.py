import sqlite3
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from logging.handlers import TimedRotatingFileHandler
from config import LOG_DIR, LOG_BACKUP_COUNT, LOG_ROTATION

class DatabaseManager:
    def __init__(self, db_path: str = "fms.db"):
        self.db_path = db_path
        self.logger = logging.getLogger('database')
        self._init_database()
    
    def _init_database(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create files_metadata table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS files_metadata (
                        file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        source TEXT,
                        file_type TEXT,
                        issue_status TEXT,
                        revision TEXT,
                        department TEXT,
                        drawing_type TEXT,
                        plant_area TEXT,
                        equipment_included TEXT,
                        notes TEXT,
                        todos TEXT,
                        last_modified DATETIME,
                        created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create recent_projects table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recent_projects (
                        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_folder_path TEXT NOT NULL,
                        last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user_input_history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_input_history (
                        input_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        field_name TEXT NOT NULL,
                        field_value TEXT NOT NULL,
                        usage_count INTEGER DEFAULT 1
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
        
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
    
    def add_file_metadata(self, metadata: Dict[str, Any]) -> Optional[int]:
        """Add new file metadata to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                columns = ', '.join(metadata.keys())
                placeholders = ', '.join(['?' for _ in metadata])
                sql = f'INSERT INTO files_metadata ({columns}) VALUES ({placeholders})'
                cursor.execute(sql, list(metadata.values()))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            self.logger.error(f"Error adding file metadata: {e}")
            return None
    
    def update_file_metadata(self, file_id: int, metadata: Dict[str, Any]) -> bool:
        """Update existing file metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                set_clause = ', '.join([f"{k} = ?" for k in metadata.keys()])
                sql = f'UPDATE files_metadata SET {set_clause} WHERE file_id = ?'
                values = list(metadata.values()) + [file_id]
                cursor.execute(sql, values)
                conn.commit()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Error updating file metadata: {e}")
            return False
    
    def search_files(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search files based on metadata criteria"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                where_clauses = []
                values = []
                for key, value in criteria.items():
                    if value:
                        where_clauses.append(f"{key} LIKE ?")
                        values.append(f"%{value}%")
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1"
                sql = f"SELECT * FROM files_metadata WHERE {where_sql}"
                
                cursor.execute(sql, values)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error searching files: {e}")
            return []
    
    def get_recent_projects(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get list of recently accessed projects"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM recent_projects 
                    ORDER BY last_accessed DESC 
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting recent projects: {e}")
            return []

def setup_logging() -> logging.Logger:
    """
    Set up application logging with file and console handlers.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('app')
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler (rotating weekly)
    file_handler = TimedRotatingFileHandler(
        LOG_DIR / 'app.log',
        when=LOG_ROTATION,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger