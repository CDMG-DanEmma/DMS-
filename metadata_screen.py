import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
import logging
from typing import Dict, Any, List, Optional
import sqlite3
from config import METADATA_FIELDS, DEPARTMENTS
import os

class MetadataScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger('app.metadata_screen')
        self._create_widgets()
        
    def _create_widgets(self):
        """Create and arrange all widgets for the Metadata screen"""
        # Configure grid weights for resizing
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Main container with three panels
        self.main_paned = ttk.PanedWindow(self, orient='horizontal')
        self.main_paned.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # Set initial pane sizes (adjust these values as needed)
        self.update_idletasks()  # Ensure window dimensions are updated
        total_width = self.winfo_width()
        
        # Left panel - Folder Tree (20% of width)
        folder_frame = ttk.LabelFrame(self.main_paned, text="Folders")
        self.main_paned.add(folder_frame, weight=20)
        
        # Configure folder frame grid
        folder_frame.grid_rowconfigure(0, weight=1)
        folder_frame.grid_columnconfigure(0, weight=1)

        # Create folder treeview
        self.folder_tree = ttk.Treeview(folder_frame, show='tree')
        folder_scroll = ttk.Scrollbar(folder_frame, orient="vertical", command=self.folder_tree.yview)
        self.folder_tree.configure(yscrollcommand=folder_scroll.set)
        
        self.folder_tree.grid(row=0, column=0, sticky='nsew')
        folder_scroll.grid(row=0, column=1, sticky='ns')
        
        # Middle panel - File List (50% of width)
        file_frame = ttk.LabelFrame(self.main_paned, text="Files")
        self.main_paned.add(file_frame, weight=50)
        
        # Configure file frame grid
        file_frame.grid_rowconfigure(1, weight=1)
        file_frame.grid_columnconfigure(0, weight=1)

        # Search/Filter frame
        filter_frame = ttk.Frame(file_frame)
        filter_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(filter_frame, text="Filter:").grid(row=0, column=0, padx=5)
        self.filter_entry = ttk.Entry(filter_frame)
        self.filter_entry.grid(row=0, column=1, sticky='ew', padx=5)
        self.filter_entry.bind('<KeyRelease>', self._filter_files)

        # File listbox with multiple selection
        self.file_list = ttk.Treeview(
            file_frame,
            columns=('name', 'type', 'department', 'revision'),
            show='headings',
            selectmode='extended'
        )
        
        self.file_list.heading('name', text='Name')
        self.file_list.heading('type', text='Type')
        self.file_list.heading('department', text='Department')
        self.file_list.heading('revision', text='Revision')
        
        # Configure column widths proportionally
        self.file_list.column('name', width=200, minwidth=100)
        self.file_list.column('type', width=80, minwidth=60)
        self.file_list.column('department', width=120, minwidth=80)
        self.file_list.column('revision', width=80, minwidth=60)
        
        file_scroll_y = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_list.yview)
        file_scroll_x = ttk.Scrollbar(file_frame, orient="horizontal", command=self.file_list.xview)
        self.file_list.configure(yscrollcommand=file_scroll_y.set, xscrollcommand=file_scroll_x.set)
        
        self.file_list.grid(row=1, column=0, sticky='nsew')
        file_scroll_y.grid(row=1, column=1, sticky='ns')
        file_scroll_x.grid(row=2, column=0, sticky='ew')

        # Right panel - Metadata Editor (30% of width)
        editor_frame = ttk.LabelFrame(self.main_paned, text="Edit Metadata")
        self.main_paned.add(editor_frame, weight=30)
        
        # Configure editor frame grid
        editor_frame.grid_rowconfigure(2, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)

        # Selection info
        self.selection_label = ttk.Label(editor_frame, text="No files selected")
        self.selection_label.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

        # Create scrollable frame for metadata fields
        canvas = ttk.Canvas(editor_frame)
        scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Metadata fields
        self.metadata_widgets = {}
        
        # Add all metadata fields
        self._add_field(scrollable_frame, "department", widget_type="combobox", values=DEPARTMENTS)
        self._add_field(scrollable_frame, "file_type")
        self._add_field(scrollable_frame, "revision")
        self._add_field(scrollable_frame, "drawing_type")
        self._add_field(scrollable_frame, "plant_area")
        self._add_field(scrollable_frame, "issue_status")
        self._add_field(scrollable_frame, "equipment_included")
        self._add_field(scrollable_frame, "notes", widget_type="text")
        self._add_field(scrollable_frame, "todos", widget_type="text")

        # Pack the canvas and scrollbar
        canvas.grid(row=2, column=0, sticky='nsew', padx=5)
        scrollbar.grid(row=2, column=1, sticky='ns')

        # Buttons
        btn_frame = ttk.Frame(editor_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky='ew', padx=5, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Update Selected",
            command=self._update_selected,
            style='primary.TButton'
        ).pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame,
            text="Clear Fields",
            command=self._clear_fields
        ).pack(side='left', padx=5)

        # Bind events
        self.folder_tree.bind('<<TreeviewSelect>>', self._on_folder_selected)
        self.file_list.bind('<<TreeviewSelect>>', self._on_files_selected)
        
        # Configure canvas scrolling
        canvas.bind('<Enter>', lambda e: self._bind_mousewheel(canvas))
        canvas.bind('<Leave>', lambda e: self._unbind_mousewheel(canvas))

        # Bind resize event to update pane sizes
        self.bind('<Configure>', self._on_resize)

    def _populate_folder_tree(self):
        """Populate the folder tree with the current folder structure"""
        self.logger.debug("Starting folder tree population")
        self.folder_tree.delete(*self.folder_tree.get_children())
        
        if not self.controller.current_folder:
            self.logger.warning("No current folder to populate")
            return
            
        def add_folder(parent, path):
            self.logger.debug(f"Adding folder to tree: {path}")
            folder_name = os.path.basename(path) or path
            folder_id = self.folder_tree.insert(
                parent, 
                'end', 
                text=folder_name, 
                values=(path,),
                open=True  # Keep folders expanded
            )
            
            try:
                # Add subfolders
                for item in os.scandir(path):
                    if item.is_dir() and not item.name.startswith('.'):
                        add_folder(folder_id, item.path)
            except PermissionError:
                self.logger.warning(f"Permission denied accessing folder: {path}")
            except Exception as e:
                self.logger.error(f"Error accessing folder {path}: {e}")
            return folder_id  # Return the folder ID for verification
            
        try:
            # Add the root folder
            self.logger.debug(f"Attempting to add root folder: {self.controller.current_folder}")
            root_id = add_folder('', self.controller.current_folder)
            if root_id:
                self.logger.info(f"Successfully populated folder tree for: {self.controller.current_folder}")
            else:
                self.logger.error("Failed to create root folder in tree")
        except Exception as e:
            self.logger.error(f"Error populating folder tree: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to load folder structure:\n{str(e)}"
            )

    def _on_folder_selected(self, event):
        """Handle folder selection"""
        selection = self.folder_tree.selection()
        if not selection:
            return
            
        folder_path = self.folder_tree.item(selection[0])['values'][0]
        self._load_files(folder_path)

    def _load_files(self, folder_path: str):
        """Load files from the selected folder"""
        self.file_list.delete(*self.file_list.get_children())
        
        try:
            for item in os.scandir(folder_path):
                if item.is_file():
                    metadata = self.controller.db.get_file_metadata(item.path) or {}
                    self.file_list.insert(
                        '',
                        'end',
                        values=(
                            item.name,
                            metadata.get('file_type', ''),
                            metadata.get('department', ''),
                            metadata.get('revision', '')
                        ),
                        tags=(item.path,)
                    )
        except Exception as e:
            self.logger.error(f"Error loading files from {folder_path}: {e}")

    def _filter_files(self, event):
        """Filter files based on search text"""
        search_text = self.filter_entry.get().lower()
        
        for item in self.file_list.get_children():
            file_name = self.file_list.item(item)['values'][0].lower()
            if search_text in file_name:
                self.file_list.reattach(item, '', 'end')
            else:
                self.file_list.detach(item)

    def _on_files_selected(self, event):
        """Handle file selection"""
        selection = self.file_list.selection()
        count = len(selection)
        
        if count == 0:
            self.selection_label.config(text="No files selected")
            self._clear_fields()
            return
        else:
            self.selection_label.config(text=f"{count} file{'s' if count > 1 else ''} selected")

        # Get metadata for all selected files
        metadata_list = []
        for item in selection:
            file_path = self.file_list.item(item)['tags'][0]
            metadata = self.controller.db.get_file_metadata_by_path(file_path) or {}
            metadata_list.append(metadata)

        # If no metadata found, clear fields and return
        if not metadata_list:
            self._clear_fields()
            return

        # For each metadata field, check if all selected files have the same value
        for field, widget in self.metadata_widgets.items():
            # Get all values including empty strings for null/missing values
            values = set(str(metadata.get(field, '')) for metadata in metadata_list)

            # Update widget based on values
            if len(values) == 1:
                # All files have the same value (including all being empty)
                value = values.pop()
                if isinstance(widget, ttk.Text):
                    widget.delete("1.0", tk.END)
                    widget.insert("1.0", value)
                elif isinstance(widget, ttk.Combobox):
                    widget.set(value)
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, value)
            else:
                # Files have different values
                if isinstance(widget, ttk.Text):
                    widget.delete("1.0", tk.END)
                    widget.insert("1.0", "varies")
                elif isinstance(widget, ttk.Combobox):
                    widget.set("varies")
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, "varies")

    def _update_selected(self):
        """Update metadata for all selected files"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select files to update")
            return

        # Gather metadata changes
        updates = {}
        for field, widget in self.metadata_widgets.items():
            if isinstance(widget, ttk.Text):
                value = widget.get("1.0", "end-1c").strip()
            else:
                value = widget.get().strip()
            if value:
                updates[field] = value

        if not updates:
            messagebox.showwarning("No Changes", "Please enter metadata values to update")
            return

        # Update each selected file
        success_count = 0
        error_count = 0
        for item in selection:
            file_path = self.file_list.item(item)['tags'][0]
            try:
                self.logger.debug(f"Updating metadata for {file_path} with values: {updates}")
                if self.controller.db.update_file_metadata_by_path(file_path, updates):
                    success_count += 1
                else:
                    error_count += 1
                    self.logger.error(f"Failed to update metadata for {file_path}")
            except Exception as e:
                error_count += 1
                self.logger.error(f"Error updating metadata for {file_path}: {e}")

        # Refresh the file list
        current_folder = self.folder_tree.item(self.folder_tree.selection()[0])['values'][0]
        self._load_files(current_folder)

        if error_count > 0:
            messagebox.showwarning(
                "Update Complete",
                f"Updated {success_count} files\nFailed to update {error_count} files"
            )
        else:
            messagebox.showinfo(
                "Update Complete",
                f"Successfully updated metadata for {success_count} files"
            )

    def _clear_fields(self):
        """Clear all metadata input fields"""
        for widget in self.metadata_widgets.values():
            if isinstance(widget, ttk.Text):
                widget.delete("1.0", tk.END)
            elif isinstance(widget, ttk.Combobox):
                widget.set('')
            else:
                widget.delete(0, tk.END)

    def refresh(self):
        """Refresh the screen"""
        self.logger.debug("Starting metadata screen refresh")
        # Clear existing data
        self._clear_fields()
        self.file_list.delete(*self.file_list.get_children())
        
        # Populate folder tree if we have a current folder
        if self.controller.current_folder:
            self.logger.debug(f"Current folder is: {self.controller.current_folder}")
            self._populate_folder_tree()
            # Check if we have any items in the tree
            if self.folder_tree.get_children():
                self.logger.debug("Folder tree populated, selecting root item")
                root_item = self.folder_tree.get_children()[0]
                self.folder_tree.selection_set(root_item)
                self.folder_tree.see(root_item)
                # Trigger folder selection to load files
                self._on_folder_selected(None)
            else:
                self.logger.warning("No items in folder tree after population")
        else:
            self.logger.warning("No current folder set during refresh")

    def _add_field(self, parent, field_name: str, widget_type: str = "entry", values: list = None):
        """Helper method to add a metadata field"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=2)
        
        # Create label with capitalized field name
        label = ttk.Label(frame, text=field_name.replace('_', ' ').title() + ":")
        label.pack(side='left')
        
        # Create appropriate widget type
        if widget_type == "combobox":
            widget = ttk.Combobox(frame, values=values, state='readonly')
            widget.pack(side='left', fill='x', expand=True, padx=5)
        elif widget_type == "text":
            widget = ttk.Text(frame, height=3, width=30)
            widget.pack(side='left', fill='x', expand=True, padx=5)
        else:  # Default to entry
            widget = ttk.Entry(frame)
            widget.pack(side='left', fill='x', expand=True, padx=5)
            
        self.metadata_widgets[field_name] = widget

    def _bind_mousewheel(self, widget):
        """Bind mousewheel to scrolling"""
        widget.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, widget))
        
    def _unbind_mousewheel(self, widget):
        """Unbind mousewheel from scrolling"""
        widget.unbind_all("<MouseWheel>")
        
    def _on_mousewheel(self, event, widget):
        """Handle mousewheel scrolling"""
        widget.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_resize(self, event):
        """Handle resize event"""
        # Update pane sizes based on new window dimensions
        self.update_idletasks()
        total_width = self.winfo_width()
        
        # Left panel - Folder Tree (20% of width)
        self.main_paned.configure(weights=(20, 50, 30))
        folder_frame = self.main_paned.nametowidget(self.main_paned.identify(region='cell', x=0, y=0))
        folder_frame.grid_columnconfigure(0, weight=1)
        folder_frame.grid_columnconfigure(1, weight=1)
        
        # Middle panel - File List (50% of width)
        file_frame = self.main_paned.nametowidget(self.main_paned.identify(region='cell', x=0, y=1))
        file_frame.grid_columnconfigure(0, weight=1)
        
        # Right panel - Metadata Editor (30% of width)
        editor_frame = self.main_paned.nametowidget(self.main_paned.identify(region='cell', x=0, y=2))
        editor_frame.grid_columnconfigure(0, weight=1)