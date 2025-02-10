import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as ttk
from datetime import datetime
import logging
import os

class JobsScreen(ttk.Frame):
    """Screen for managing folders and recent history"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger(f'app.{self.__class__.__name__.lower()}')
        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        # Configure grid weights for resizing
        self.grid_rowconfigure(2, weight=1)  # Give weight to recent history section
        self.grid_columnconfigure(0, weight=1)
        
        # Title Section
        title_frame = ttk.Frame(self)
        title_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=10)
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ttk.Label(
            title_frame,
            text="Folder Management",
            font=("TkDefaultFont", 16, "bold")
        )
        title_label.grid(row=0, column=0, sticky='w')

        # Folder Selection Section
        folder_frame = ttk.LabelFrame(self, text="Open Folder", padding=10)
        folder_frame.grid(row=1, column=0, sticky='ew', padx=20, pady=10)
        folder_frame.grid_columnconfigure(0, weight=1)

        open_btn = ttk.Button(
            folder_frame,
            text="Select Folder",
            command=self._open_folder,
            style='primary.TButton'
        )
        open_btn.grid(row=0, column=0, pady=5)

        # Recent History Section
        recent_frame = ttk.LabelFrame(self, text="Recent History", padding=10)
        recent_frame.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)
        recent_frame.grid_rowconfigure(0, weight=1)
        recent_frame.grid_columnconfigure(0, weight=1)

        # Create Treeview for recent folders with scrollbars
        tree_container = ttk.Frame(recent_frame)
        tree_container.grid(row=0, column=0, sticky='nsew')
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        self.recent_tree = ttk.Treeview(
            tree_container,
            columns=('path', 'last_accessed'),
            show='headings',
            selectmode='browse'
        )

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(
            tree_container, 
            orient="vertical", 
            command=self.recent_tree.yview
        )
        x_scrollbar = ttk.Scrollbar(
            tree_container, 
            orient="horizontal", 
            command=self.recent_tree.xview
        )
        
        self.recent_tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        # Configure columns
        self.recent_tree.heading('path', text='Folder Path')
        self.recent_tree.heading('last_accessed', text='Last Accessed')
        
        # Configure column widths proportionally
        self.recent_tree.column('path', width=400, minwidth=200)
        self.recent_tree.column('last_accessed', width=150, minwidth=100)
        
        # Grid layout for treeview and scrollbars
        self.recent_tree.grid(row=0, column=0, sticky='nsew')
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        x_scrollbar.grid(row=1, column=0, sticky='ew')
        
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
            self.logger.debug("No folder selected in recent tree")
            return

        folder_path = self.recent_tree.item(selection[0])['values'][0]
        self.logger.info(f"Selected folder from recent list: {folder_path}")

        if not os.path.exists(folder_path):
            self.logger.warning(f"Recent folder not found: {folder_path}")
            messagebox.showwarning(
                "Folder Not Found",
                f"The folder no longer exists:\n{folder_path}\n\nIt will be removed from the recent list."
            )
            # Remove the non-existent folder from the database
            try:
                self.controller.db.remove_recent_folder(folder_path)
                self.refresh()  # Refresh the list to remove the entry
            except Exception as e:
                self.logger.error(f"Error removing non-existent folder from database: {e}")
            return

        self.logger.info(f"Processing selected folder: {folder_path}")
        if self._process_folder(folder_path):
            self.controller.current_folder = folder_path
            self.refresh()
            self.controller.refresh_all_screens()
            self.logger.info(f"Switching to metadata screen for folder: {folder_path}")
            self.controller.show_screen("metadata")

    def refresh(self):
        """Refresh the recent folders list"""
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        recent_folders = self.controller.db.get_recent_folders()
        for folder in recent_folders:
            self.recent_tree.insert(
                '',
                'end',
                values=(
                    folder['folder_path'],
                    folder['last_accessed'].strftime('%Y-%m-%d %H:%M')
                )
            )
        self.logger.info("Recent folders list refreshed")