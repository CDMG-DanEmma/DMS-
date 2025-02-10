import os
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional, Set
import sqlite3
from config import FILE_TYPES

class FileScanner:
    """Handles scanning of folders and updating the metadata database."""
    
    def __init__(self, db_manager):
        """Initialize the FileScanner with a database manager instance."""
        self.db_manager = db_manager
        self.logger = logging.getLogger('app.file_scanner')
        
    def scan_folder(self, folder_path: str) -> bool:
        """
        Scan a folder and update the database with file metadata.
        
        Args:
            folder_path (str): Path to the folder to scan
            
        Returns:
            bool: True if scan completed successfully, False otherwise
        """
        try:
            # Validate folder exists
            if not os.path.exists(folder_path):
                self.logger.error(f"Folder not found: {folder_path}")
                return False
                
            # Get existing files in database for this folder
            existing_files = self._get_existing_files(folder_path)
            
            # Track processed files to identify removed ones
            processed_files: Set[str] = set()
            
            # Scan all files in folder and subfolders
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    try:
                        # Get file metadata
                        metadata = self._extract_metadata(file_path)
                        
                        if file_path in existing_files:
                            # Update existing record if modified
                            if metadata['last_modified'] > existing_files[file_path]:
                                self.db_manager.update_file_metadata(
                                    file_path,
                                    metadata
                                )
                                self.logger.debug(f"Updated metadata: {file_path}")
                        else:
                            # Add new record
                            self.db_manager.add_file_metadata(metadata)
                            self.logger.debug(f"Added new file: {file_path}")
                            
                        processed_files.add(file_path)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing file {file_path}: {e}")
                        continue
            
            # Identify and handle removed files
            removed_files = set(existing_files.keys()) - processed_files
            if removed_files:
                self._handle_removed_files(removed_files)
            
            self.logger.info(
                f"Scan completed - Processed: {len(processed_files)}, "
                f"Removed: {len(removed_files)}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Scan failed for folder {folder_path}: {e}")
            return False
            
    def _extract_metadata(self, file_path: str) -> Dict:
        """
        Extract metadata from a file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            Dict: Metadata dictionary
        """
        file_stat = os.stat(file_path)
        file_name = os.path.basename(file_path)
        extension = os.path.splitext(file_name)[1].lower()
        
        metadata = {
            'file_path': file_path,
            'file_name': file_name,
            'source': Path(file_path).drive or 'local',
            'file_type': FILE_TYPES.get(extension, 'OTHER'),
            'last_modified': datetime.fromtimestamp(file_stat.st_mtime),
            'created_date': datetime.fromtimestamp(file_stat.st_ctime)
        }
        
        return metadata
        
    def _get_existing_files(self, folder_path: str) -> Dict[str, datetime]:
        """
        Get existing files from database for the given folder.
        
        Args:
            folder_path (str): Path to the folder
            
        Returns:
            Dict[str, datetime]: Dictionary of file paths and their last modified times
        """
        try:
            results = self.db_manager.search_files({'file_path': folder_path})
            return {
                r['file_path']: r['last_modified'] 
                for r in results 
                if 'file_path' in r and 'last_modified' in r
            }
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting existing files: {e}")
            return {}
            
    def _handle_removed_files(self, removed_files: Set[str]) -> None:
        """
        Handle files that no longer exist in the folder.
        
        Args:
            removed_files (Set[str]): Set of file paths that were not found
        """
        try:
            # For now, we'll just log removed files
            # Future: Could mark them as inactive or delete them
            for file_path in removed_files:
                self.logger.warning(f"File no longer exists: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error handling removed files: {e}")

    def get_scan_summary(self, folder_path: str) -> Dict:
        """
        Get a summary of files in the database for the given folder.
        
        Args:
            folder_path (str): Path to the folder
            
        Returns:
            Dict: Summary statistics
        """
        try:
            results = self.db_manager.search_files({'file_path': folder_path})
            
            # Count files by type
            type_counts = {}
            for result in results:
                file_type = result.get('file_type', 'OTHER')
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
                
            # Count tagged vs untagged
            tagged = sum(1 for r in results if r.get('department') and r.get('revision'))
            
            return {
                'total_files': len(results),
                'type_counts': type_counts,
                'tagged_files': tagged,
                'untagged_files': len(results) - tagged
            }
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting scan summary: {e}")
            return {
                'total_files': 0,
                'type_counts': {},
                'tagged_files': 0,
                'untagged_files': 0
            }