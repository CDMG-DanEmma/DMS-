#!/usr/bin/env python3
"""
File Management System (FMS) - Main Application Entry Point

This module serves as the entry point for the FMS application, initializing the GUI
and coordinating between different components of the system.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as ttk
from pathlib import Path
import logging
import sys
import os
from typing import Dict, Optional
from datetime import datetime

# Import application modules
from db_manager import DatabaseManager
from logger import setup_logging
from file_scanner import FileScanner
from utils import get_file_type, format_timestamp, get_relative_path
from search_screen import SearchScreen
from metadata_screen import MetadataScreen
from jobs_screens import JobsScreen
import config

class Screen(ttk.Frame):
    """Base class for application screens"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(f'app.{self.__class__.__name__.lower()}')

    def refresh(self):
        """Refresh screen content - to be implemented by subclasses"""
        pass

class JobsScreen(Screen):
    """Screen for managing job folders and recent projects"""
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        # Title Section
        title_frame = ttk.Frame(self)
        title_frame.pack(fill='x', padx=20, pady=10)
        
        title_label = ttk.Label(
            title_frame,
            text="Folder Management",
            font=("TkDefaultFont", 16, "bold")
        )
        title_label.pack(side='left')

        # Folder Selection Section
        folder_frame = ttk.LabelFrame(self, text="Open Folder", padding=10)
        folder_frame.pack(fill='x', padx=20, pady=10)

        open_btn = ttk.Button(
            folder_frame,
            text="Select Folder",
            command=self._open_folder,
            style='primary.TButton'
        )
        open_btn.pack(pady=5)

        # Recent History Section
        recent_frame = ttk.LabelFrame(self, text="Recent History", padding=10)
        recent_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Create Treeview for recent folders
        self.recent_tree = ttk.Treeview(
            recent_frame,
            columns=('path', 'last_accessed'),
            show='headings',
            selectmode='browse',
            height=5
        )

        self.recent_tree.heading('path', text='Folder Path')
        self.recent_tree.heading('last_accessed', text='Last Accessed')
        
        self.recent_tree.column('path', width=300)
        self.recent_tree.column('last_accessed', width=150)
        
        self.recent_tree.pack(fill='both', expand=True)
        self.recent_tree.bind('<Double-1>', self._on_recent_folder_selected)

    def _open_folder(self):
        """Handle opening a folder"""
        folder_path = filedialog.askdirectory(title="Select Folder")
        if not folder_path:
            return

        if not self._process_folder(folder_path):
            return

        self.controller.current_folder = folder_path
        self.refresh()
        self.controller.refresh_all_screens()

    def _process_folder(self, folder_path: str) -> bool:
        """Process a selected folder"""
        if not os.path.exists(folder_path):
            self.logger.warning(f"Folder not found: {folder_path}")
            messagebox.showwarning(
                "Invalid Folder",
                f"The folder does not exist:\n{folder_path}"
            )
            return False
            
        try:
            # Update recent folders
            self.controller.db.add_recent_folder(folder_path)
            
            # Scan folder contents
            if self.controller.scanner:
                self.controller.scanner.scan_folder(folder_path)
            
            self.logger.info(f"Successfully processed folder: {folder_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing folder {folder_path}: {e}")
            messagebox.showerror(
                "Processing Error",
                f"Error processing folder:\n{str(e)}"
            )
            return False

    def _on_recent_folder_selected(self, event):
        """Handle double-click on recent folder"""
        selection = self.recent_tree.selection()
        if not selection:
            return

        folder_path = self.recent_tree.item(selection[0])['values'][0]
        if not os.path.exists(folder_path):
            self.logger.warning(f"Recent folder not found: {folder_path}")
            messagebox.showwarning(
                "Folder Not Found",
                f"The folder no longer exists:\n{folder_path}"
            )
            return

        if self._process_folder(folder_path):
            self.controller.current_folder = folder_path
            self.refresh()
            self.controller.refresh_all_screens()
            self.controller.show_screen("metadata")

    def refresh(self):
        """Refresh the recent folders list"""
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        recent_folders = self.controller.db.get_recent_folders()
        for folder in recent_folders:
            # Convert string timestamp to datetime if needed
            last_accessed = folder['last_accessed']
            if isinstance(last_accessed, str):
                last_accessed = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
            
            self.recent_tree.insert(
                '',
                'end',
                values=(
                    folder['folder_path'],
                    last_accessed.strftime('%Y-%m-%d %H:%M')
                )
            )
        self.logger.info("Recent folders list refreshed")

class FileManagementSystem:
    """Main application class"""
    def __init__(self):
        # Initialize logger first
        self.logger = setup_logging()
        self.logger.info("Initializing File Management System")

        # Create main window
        self.root = ttk.Window(themename=config.UI_THEME)
        self.root.title(config.APP_NAME)
        self.root.geometry(config.WINDOW_SIZE)
        
        # Configure root window to expand
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Initialize database
        self.db = DatabaseManager()
        
        # Initialize file scanner
        self.scanner = FileScanner(self.db)
        
        # Track current folder - try to restore last used folder
        self.current_folder = self._restore_last_folder()

        # Create container for screens
        self.container = ttk.Frame(self.root)
        self.container.grid(row=1, column=0, sticky="nsew")
        
        # Configure container to expand
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Initialize screens dictionary and navigation
        self.screens: Dict[str, Screen] = {}
        self._setup_navigation()
        self._initialize_screens()

        # Show initial screen
        self.show_screen("jobs")

    def _restore_last_folder(self) -> Optional[str]:
        """Restore the last selected folder if it exists"""
        try:
            last_folder = self.db.get_last_selected_folder()
            if last_folder and os.path.exists(last_folder):
                self.logger.info(f"Restored last folder: {last_folder}")
                return last_folder
            else:
                self.logger.info("No valid last folder to restore")
                return None
        except Exception as e:
            self.logger.error(f"Error restoring last folder: {e}")
            return None

    def _setup_navigation(self):
        """Create navigation menu"""
        nav_frame = ttk.Frame(self.root)
        nav_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        nav_frame.grid_columnconfigure(3, weight=1)  # Make the last column expand

        for i, screen_name in enumerate(["Jobs", "Search", "Metadata"]):
            btn = ttk.Button(
                nav_frame,
                text=screen_name,
                command=lambda s=screen_name.lower(): self.show_screen(s)
            )
            btn.grid(row=0, column=i, padx=5)

    def _initialize_screens(self):
        """Initialize all application screens"""
        self.screens["jobs"] = JobsScreen(self.container, self)
        self.screens["search"] = SearchScreen(self.container, self)
        self.screens["metadata"] = MetadataScreen(self.container, self)

        # Configure grid for all screens
        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

    def show_screen(self, screen_name: str):
        """Switch to the specified screen"""
        screen = self.screens.get(screen_name)
        if screen:
            screen.tkraise()
            screen.refresh()  # Refresh the screen when it's shown
            self.logger.info(f"Switched to {screen_name} screen")

    def refresh_all_screens(self):
        """Refresh all screens"""
        for screen in self.screens.values():
            screen.refresh()

    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.logger.info("Application shutting down")

def main():
    """Main entry point"""
    try:
        app = FileManagementSystem()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()