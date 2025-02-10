import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

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
                
                # Create recent_folders table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recent_folders (
                        folder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folder_path TEXT NOT NULL UNIQUE,
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
                
                # Handle each search criterion
                for key, value in criteria.items():
                    if not value:
                        continue
                        
                    # Handle date fields
                    if key in ('last_modified', 'created_date'):
                        if value == "YYYY-MM-DD":
                            continue
                        # Allow partial date matches (e.g., just the date portion)
                        where_clauses.append(f"date({key}) = date(?)")
                        values.append(value)
                    else:
                        # For text fields, use case-insensitive LIKE
                        where_clauses.append(f"lower({key}) LIKE lower(?)")
                        values.append(f"%{value}%")
                
                # Build the SQL query
                sql = "SELECT * FROM files_metadata"
                if where_clauses:
                    sql += " WHERE " + " AND ".join(where_clauses)
                sql += " ORDER BY last_modified DESC"
                
                self.logger.debug(f"Executing search query: {sql} with values: {values}")
                cursor.execute(sql, values)
                results = [dict(row) for row in cursor.fetchall()]
                self.logger.info(f"Search returned {len(results)} results")
                return results
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error in search_files: {e}")
            return []
    
    def get_recent_folders(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get list of recently accessed folders"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM recent_folders 
                    ORDER BY last_accessed DESC 
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting recent folders: {e}")
            return []
    
    def add_recent_folder(self, folder_path: str) -> bool:
        """Add or update a folder in recent_folders table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update if exists, insert if not
                cursor.execute("""
                    INSERT INTO recent_folders (folder_path, last_accessed)
                    VALUES (?, CURRENT_TIMESTAMP)
                    ON CONFLICT(folder_path) 
                    DO UPDATE SET last_accessed = CURRENT_TIMESTAMP
                """, (folder_path,))
                
                # Keep only the 5 most recent
                cursor.execute("""
                    DELETE FROM recent_folders 
                    WHERE folder_path NOT IN (
                        SELECT folder_path 
                        FROM recent_folders 
                        ORDER BY last_accessed DESC 
                        LIMIT 5
                    )
                """)
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error in add_recent_folder: {e}")
            return False

    def get_file_metadata(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM files_metadata WHERE file_id = ?', (file_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting file metadata: {e}")
            return None

    def remove_recent_folder(self, folder_path: str) -> bool:
        """Remove a folder from the recent_folders table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM recent_folders WHERE folder_path = ?",
                    (folder_path,)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Error removing recent folder: {e}")
            return False

    def update_file_metadata_by_path(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a file based on its path"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build the update query
                set_clause = ', '.join([f"{k} = ?" for k in metadata.keys()])
                values = list(metadata.values()) + [file_path]
                
                sql = f'UPDATE files_metadata SET {set_clause} WHERE file_path = ?'
                self.logger.debug(f"Executing update query: {sql} with values: {values}")
                
                cursor.execute(sql, values)
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Successfully updated metadata for {file_path}")
                    return True
                else:
                    self.logger.warning(f"No rows updated for {file_path}")
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error(f"Database error updating metadata for {file_path}: {e}")
            return False

    def get_file_metadata_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a file based on its path"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM files_metadata WHERE file_path = ?', (file_path,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting file metadata for {file_path}: {e}")
            return None