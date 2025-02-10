import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
import logging
from typing import Dict, Any
import sqlite3
from config import METADATA_FIELDS, DEPARTMENTS, SEARCH_RESULTS_PER_PAGE, FILE_TYPES

class SearchScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger('app.search_screen')
        
        # Search criteria widgets
        self.search_widgets = {}
        
        # Sorting state
        self.sort_column = None
        self.sort_reverse = False
        
        # Column configurations
        self.column_configs = [
            ('name', 'File Name', 200),
            ('path', 'Path', 300),
            ('type', 'Type', 80),
            ('department', 'Department', 120),
            ('revision', 'Revision', 80),
            ('drawing_type', 'Drawing Type', 120),
            ('plant_area', 'Plant Area', 120),
            ('equipment', 'Equipment', 120),
            ('issue_status', 'Issue Status', 100),
            ('notes', 'Notes', 200),
            ('todos', 'TODOs', 200),
            ('modified', 'Modified', 150),
            ('created', 'Created', 150)
        ]
        
        # Create the main layout
        self._create_widgets()
        
    def _create_widgets(self):
        """Create and arrange all widgets for the Search screen"""
        # Configure grid weights for resizing
        self.grid_rowconfigure(2, weight=1)  # Give weight to results section
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title_frame = ttk.Frame(self)
        title_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=10)
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ttk.Label(
            title_frame,
            text="File Search",
            font=("TkDefaultFont", 16, "bold")
        )
        title_label.grid(row=0, column=0, sticky='w')
        
        # Add helper text for wildcards
        helper_text = ttk.Label(
            title_frame,
            text="Use * for wildcards (e.g., *.dwg for all DWG files)",
            font=("TkDefaultFont", 9),
            foreground='gray'
        )
        helper_text.grid(row=1, column=0, sticky='w', pady=(0, 5))
        
        # Search Criteria Section
        criteria_frame = ttk.LabelFrame(self, text="Search Criteria", padding=10)
        criteria_frame.grid(row=1, column=0, sticky='ew', padx=20, pady=10)
        
        # Define all searchable fields
        search_fields = [
            ('file_name', 'File Name'),
            ('file_path', 'File Path'),
            ('source', 'Source'),
            ('file_type', 'File Type'),
            ('department', 'Department'),
            ('revision', 'Revision'),
            ('drawing_type', 'Drawing Type'),
            ('plant_area', 'Plant Area'),
            ('equipment_included', 'Equipment'),
            ('issue_status', 'Issue Status'),
            ('notes', 'Notes'),
            ('todos', 'TODOs'),
            ('last_modified', 'Last Modified'),
            ('created_date', 'Created Date')
        ]
        
        # Create a grid for search fields
        for i, (field, label) in enumerate(search_fields):
            row = i // 2
            col = i % 2
            
            # Configure column weights
            criteria_frame.grid_columnconfigure(col*2+1, weight=1)
            
            # Create label
            label = ttk.Label(criteria_frame, text=label)
            label.grid(row=row, column=col*2, padx=5, pady=5, sticky='e')
            
            # Create entry/combobox based on field type
            if field == 'department' and DEPARTMENTS:
                widget = ttk.Combobox(
                    criteria_frame,
                    values=DEPARTMENTS,
                    state='readonly'
                )
            elif field == 'file_type':
                widget = ttk.Combobox(
                    criteria_frame,
                    values=list(set(FILE_TYPES.values())),
                    state='readonly'
                )
            elif field in ('last_modified', 'created_date'):
                # Create date entry with placeholder
                widget = ttk.Entry(criteria_frame)
                widget.insert(0, "YYYY-MM-DD")
                widget.bind('<FocusIn>', lambda e, w=widget: self._on_date_focus_in(e, w))
                widget.bind('<FocusOut>', lambda e, w=widget: self._on_date_focus_out(e, w))
            else:
                widget = ttk.Entry(criteria_frame)
                
            widget.grid(row=row, column=col*2+1, padx=5, pady=5, sticky='ew')
            self.search_widgets[field] = widget
            
            # Bind Enter key to search function for all entry widgets
            if isinstance(widget, ttk.Entry):
                widget.bind('<Return>', lambda e: self._perform_search())
        
        # Button Frame
        button_frame = ttk.Frame(criteria_frame)
        button_frame.grid(row=len(search_fields)//2 + 1, column=0, 
                         columnspan=4, pady=10)
        
        search_btn = ttk.Button(
            button_frame,
            text="Search",
            command=self._perform_search,
            style='primary.TButton'
        )
        search_btn.pack(side='left', padx=5)
        
        clear_btn = ttk.Button(
            button_frame,
            text="Clear",
            command=self._clear_search
        )
        clear_btn.pack(side='left', padx=5)
        
        # Results Section
        results_frame = ttk.LabelFrame(self, text="Search Results", padding=10)
        results_frame.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Create Treeview for results
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=('name', 'path', 'type', 'department', 'revision', 'drawing_type', 'plant_area', 'equipment', 'issue_status', 'notes', 'todos', 'modified', 'created'),
            show='headings',
            selectmode='extended'
        )
        
        # Configure columns
        for col, heading, width in self.column_configs:
            self.results_tree.heading(
                col,
                text=heading,
                command=lambda c=col: self._sort_treeview(c)
            )
            self.results_tree.column(col, width=width, minwidth=width//2)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(
            results_frame,
            orient='vertical',
            command=self.results_tree.yview
        )
        x_scrollbar = ttk.Scrollbar(
            results_frame,
            orient='horizontal',
            command=self.results_tree.xview
        )
        
        self.results_tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # Grid layout for treeview and scrollbars
        self.results_tree.grid(row=0, column=0, sticky='nsew')
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        x_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Bind double-click event
        self.results_tree.bind('<Double-1>', self._on_result_double_click)

    def _on_date_focus_in(self, event, widget):
        """Clear placeholder text when date field gets focus"""
        if widget.get() == "YYYY-MM-DD":
            widget.delete(0, tk.END)

    def _on_date_focus_out(self, event, widget):
        """Restore placeholder text if date field is empty"""
        if not widget.get():
            widget.insert(0, "YYYY-MM-DD")
            
    def _perform_search(self):
        """Execute search based on criteria"""
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # Gather search criteria
        criteria = {}
        for field, widget in self.search_widgets.items():
            value = widget.get().strip()
            if value and value != "YYYY-MM-DD":  # Skip empty fields and date placeholders
                criteria[field] = value
                
        try:
            # Use the controller's database manager to perform search
            results = self.controller.db.search_files(criteria)
            
            # Update results tree
            for result in results:
                self.results_tree.insert(
                    '',
                    'end',
                    values=(
                        result['file_name'],
                        result['file_path'],
                        result['file_type'],
                        result['department'],
                        result['revision'],
                        result['drawing_type'],
                        result['plant_area'],
                        result['equipment_included'],
                        result['issue_status'],
                        result['notes'],
                        result['todos'],
                        result.get('last_modified', '').split('.')[0],  # Remove microseconds
                        result.get('created_date', '').split('.')[0]  # Remove microseconds
                    )
                )
                
            self.logger.info(f"Search completed: {len(results)} results found")
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error during search: {e}")
            messagebox.showerror(
                "Search Error",
                "An error occurred while searching the database"
            )
            
    def _clear_search(self):
        """Clear all search criteria and results"""
        # Clear search widgets
        for field, widget in self.search_widgets.items():
            if isinstance(widget, ttk.Combobox):
                widget.set('')
            elif field in ('last_modified', 'created_date'):
                widget.delete(0, tk.END)
                widget.insert(0, "YYYY-MM-DD")
            else:
                widget.delete(0, tk.END)
                
        # Clear results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
    def _on_result_double_click(self, event):
        """Handle double-click on search result"""
        selection = self.results_tree.selection()
        if not selection:
            return
            
        # Get the file path from the selected item
        file_path = self.results_tree.item(selection[0])['values'][1]  # Path is in second column
        
        try:
            # Attempt to open the file with default system application
            import os
            os.startfile(file_path)
            self.logger.info(f"Opened file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error opening file {file_path}: {e}")
            messagebox.showerror(
                "File Error",
                f"Unable to open the file:\n{file_path}"
            )
            
    def refresh(self):
        """Refresh the search results if needed"""
        # Could be used to update results when file metadata changes
        if any(widget.get().strip() not in ("", "YYYY-MM-DD") for widget in self.search_widgets.values()):
            self._perform_search()

    def _sort_treeview(self, column):
        """Sort treeview content when a column header is clicked"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        items = [(self.results_tree.set(item, column), item) for item in self.results_tree.get_children('')]
        items.sort(reverse=self.sort_reverse)
        
        for index, (_, item) in enumerate(items):
            self.results_tree.move(item, '', index)

        # Update column headers
        for col in self.results_tree['columns']:
            self.results_tree.heading(col, text=next(h for c, h, _ in self.column_configs if c == col))
        
        current_text = self.results_tree.heading(column)['text']
        self.results_tree.heading(column, text=f"{current_text} {'↑' if self.sort_reverse else '↓'}")