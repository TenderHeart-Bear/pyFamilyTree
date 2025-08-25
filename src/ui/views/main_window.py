"""
Main window implementation for the Family Tree application.
"""
import customtkinter as ctk
from typing import Optional, Callable
import os
from tkinter import filedialog
import tkinter as tk
from ...config import SettingsManager

class MainWindow(ctk.CTk):
    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        
        self.settings_manager = settings_manager
        
        # Configure window
        window_settings = self.settings_manager.get('window.main')
        self.title(window_settings['title'])
        self.geometry(f"{window_settings['default_size']['width']}x{window_settings['default_size']['height']}")
        self.minsize(
            window_settings['min_size']['width'],
            window_settings['min_size']['height']
        )
        
        # Configure grid layout (3 columns: sidebar, content, and node info)
        self.grid_columnconfigure(0, weight=0)  # Sidebar - fixed width
        self.grid_columnconfigure(1, weight=1)  # Content - expandable
        self.grid_columnconfigure(2, weight=0)  # Node info panel - fixed width
        self.grid_rowconfigure(0, weight=1)     # Full height
        
        # Get layout settings
        layout_settings = self.settings_manager.get('layout')
        sidebar_settings = layout_settings['sidebar']
        node_info_settings = layout_settings['node_info_panel']
        content_settings = layout_settings['content']
        
        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=sidebar_settings['width'],
            corner_radius=0
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar_frame.grid_rowconfigure(5, weight=1)  # Space for status
        self.sidebar_frame.grid_propagate(False)  # Maintain fixed width
        
        # Get font settings
        font_settings = self.settings_manager.get('fonts')
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Family Tree\nVisualizer", 
            font=ctk.CTkFont(
                size=font_settings['logo']['size'],
                weight=font_settings['logo']['weight']
            )
        )
        self.logo_label.grid(
            row=0,
            column=0,
            padx=sidebar_settings['padding']['x'],
            pady=(sidebar_settings['padding']['y'] * 2, sidebar_settings['padding']['y']),
            sticky="ew"
        )
        
        # Sidebar buttons
        button_settings = {
            'height': 40,
            'font': ctk.CTkFont(
                size=font_settings['normal']['size'],
                weight=font_settings['normal']['weight']
            )
        }
        
        self.load_data_button = ctk.CTkButton(
            self.sidebar_frame, 
            text="Load Data",
            command=self.load_data,
            **button_settings
        )
        self.load_data_button.grid(
            row=1,
            column=0,
            padx=sidebar_settings['padding']['x'],
            pady=sidebar_settings['padding']['y'],
            sticky="ew"
        )
        
        self.visualize_button = ctk.CTkButton(
            self.sidebar_frame, 
            text="Visualize Tree",
            command=self.visualize_tree,
            state="disabled",  # Initially disabled until data is loaded
            **button_settings
        )
        self.visualize_button.grid(
            row=2,
            column=0,
            padx=sidebar_settings['padding']['x'],
            pady=sidebar_settings['padding']['y'],
            sticky="ew"
        )
        
        self.settings_button = ctk.CTkButton(
            self.sidebar_frame, 
            text="Settings",
            command=self.open_settings,
            **button_settings
        )
        self.settings_button.grid(
            row=3,
            column=0,
            padx=sidebar_settings['padding']['x'],
            pady=sidebar_settings['padding']['y'],
            sticky="ew"
        )
        
        # Add reload button
        self.reload_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Reload",
            command=self.reload_visualization,
            **button_settings
        )
        self.reload_button.grid(
            row=4,
            column=0,
            padx=sidebar_settings['padding']['x'],
            pady=sidebar_settings['padding']['y'],
            sticky="ew"
        )
        
        # Add open in browser button
        self.open_browser_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Open in Browser",
            command=self.open_in_browser,
            state="disabled",  # Initially disabled
            **button_settings
        )
        self.open_browser_button.grid(
            row=5,
            column=0,
            padx=sidebar_settings['padding']['x'],
            pady=sidebar_settings['padding']['y'],
            sticky="ew"
        )
        
        # Status label with scrollable text
        self.status_frame = ctk.CTkFrame(self.sidebar_frame)
        self.status_frame.grid(
            row=6,
            column=0,
            padx=sidebar_settings['padding']['x'],
            pady=sidebar_settings['padding']['y'],
            sticky="nsew"
        )
        self.status_frame.grid_rowconfigure(0, weight=1)
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="No data loaded",
            font=ctk.CTkFont(
                size=font_settings['status']['size'],
                weight=font_settings['status']['weight']
            ),
            wraplength=160,
            justify="left"
        )
        self.status_label.grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            sticky="nsew"
        )
        
        # Create main content area
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=content_settings['padding']['x'],
            pady=content_settings['padding']['y']
        )
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Create node info panel on the right side
        self.node_info_frame = ctk.CTkFrame(
            self,
            width=node_info_settings['width'],
            corner_radius=0
        )
        self.node_info_frame.grid(row=0, column=2, sticky="nsew", padx=0, pady=0)
        self.node_info_frame.grid_propagate(False)  # Maintain fixed width
        
        # Node info panel title
        self.node_info_title = ctk.CTkLabel(
            self.node_info_frame,
            text="Node Information",
            font=ctk.CTkFont(
                size=font_settings['section_title']['size'],
                weight=font_settings['section_title']['weight']
            )
        )
        self.node_info_title.grid(
            row=0,
            column=0,
            padx=20,
            pady=(20, 10),
            sticky="ew"
        )
        
        # Node info text area
        self.node_info_text = ctk.CTkTextbox(
            self.node_info_frame,
            width=node_info_settings['width'] - 20,
            height=node_info_settings['text_height'],
            font=ctk.CTkFont(
                size=font_settings['normal']['size'],
                weight=font_settings['normal']['weight']
            )
        )
        self.node_info_text.grid(
            row=1,
            column=0,
            padx=20,
            pady=(0, 20),
            sticky="nsew"
        )
        self.node_info_frame.grid_rowconfigure(1, weight=1)
        
        # Placeholder for tree visualization
        self.tree_view = ctk.CTkLabel(
            self.content_frame,
            text="Tree Visualization will appear here\n\nClick 'Load Data' to begin",
            font=ctk.CTkFont(
                size=font_settings['normal']['size'],
                weight=font_settings['normal']['weight']
            ),
            text_color="gray"
        )
        self.tree_view.grid(
            row=0,
            column=0,
            padx=content_settings['padding']['x'],
            pady=content_settings['padding']['y'],
            sticky="nsew"
        )
        
        # Set default appearance mode and color theme
        ctk.set_appearance_mode(self.settings_manager.get('appearance.theme', 'System'))
        ctk.set_default_color_theme("blue")
        
        # Callback handlers
        self._on_data_loaded: Optional[Callable[[str, str], None]] = None
        self._on_visualize: Optional[Callable[[], None]] = None
        self._on_settings: Optional[Callable[[], None]] = None
        self._on_reload: Optional[Callable[[], None]] = None
        self._on_open_browser: Optional[Callable[[], None]] = None
        
        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Handle window closing"""
        try:
    
            self.destroy()
        except Exception as e:
            print(f"DEBUG: Error during window close: {e}")
    
    def set_callbacks(self,
                     on_data_loaded: Optional[Callable[[str, str], None]] = None,
                     on_visualize: Optional[Callable[[], None]] = None,
                     on_settings: Optional[Callable[[], None]] = None,
                     on_reload: Optional[Callable[[], None]] = None,
                     on_open_browser: Optional[Callable[[], None]] = None):
        """Set callback handlers for UI events"""
        self._on_data_loaded = on_data_loaded
        self._on_visualize = on_visualize
        self._on_settings = on_settings
        self._on_reload = on_reload
        self._on_open_browser = on_open_browser
    
    def load_data(self):
        """Handle loading data from Excel/XML files"""
        try:
            file_formats = self.settings_manager.get('files.supported_formats')
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[
                    ("Excel files", " ".join(file_formats['excel'])),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                # Get sheet name
                sheet_name = self._show_sheet_name_dialog()
                if sheet_name and self._on_data_loaded:
                    self._on_data_loaded(file_path, sheet_name)
        except Exception as e:
            print(f"DEBUG: Error in load_data: {e}")
            self.show_error(f"Error loading data: {str(e)}")
    
    def _show_sheet_name_dialog(self) -> Optional[str]:
        """Show dialog to get sheet name"""
        try:
            dialog = ctk.CTkInputDialog(
                text="Enter the name of the worksheet to process:",
                title="Sheet Name"
            )
            return dialog.get_input()
        except Exception as e:
            print(f"DEBUG: Error showing sheet name dialog: {e}")
            return None
    
    def visualize_tree(self):
        """Handle tree visualization"""
        try:
            if self._on_visualize:
                self._on_visualize()
        except Exception as e:
            print(f"DEBUG: Error in visualize_tree: {e}")
            self.show_error(f"Error visualizing tree: {str(e)}")
    
    def open_settings(self):
        """Open settings dialog"""
        try:
            if self._on_settings:
                self._on_settings()
        except Exception as e:
            print(f"DEBUG: Error opening settings: {e}")
            self.show_error(f"Error opening settings: {str(e)}")
    
    def update_status(self, message: str, enable_visualize: bool = True):
        """Update status message and visualize button state"""
        try:
            self.status_label.configure(text=message)
            self.visualize_button.configure(state="normal" if enable_visualize else "disabled")

        except Exception as e:
            print(f"DEBUG: Error updating status: {e}")
    
    def show_error(self, message: str):
        """Show error dialog"""
        try:

            error_settings = self.settings_manager.get('window.error_dialog')
            font_settings = self.settings_manager.get('fonts')
            
            # Create error dialog
            error_window = ctk.CTkToplevel(self)
            error_window.title("Error")
            error_window.geometry(f"{error_settings['size']['width']}x{error_settings['size']['height']}")
            error_window.transient(self)
            error_window.grab_set()
            
            # Center the error window
            error_window.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() - error_window.winfo_width()) // 2
            y = self.winfo_y() + (self.winfo_height() - error_window.winfo_height()) // 2
            error_window.geometry(f"+{x}+{y}")
            
            # Error message
            error_label = ctk.CTkLabel(
                error_window,
                text=message,
                font=ctk.CTkFont(
                    size=font_settings['error']['size'],
                    weight=font_settings['error']['weight']
                ),
                wraplength=350,
                justify="left"
            )
            error_label.pack(padx=20, pady=20, expand=True)
            
            # OK button
            ok_button = ctk.CTkButton(
                error_window,
                text="OK",
                command=error_window.destroy,
                width=100,
                font=ctk.CTkFont(
                    size=font_settings['normal']['size'],
                    weight=font_settings['normal']['weight']
                )
            )
            ok_button.pack(pady=10)
            
            # Keep visualize button enabled
            self.visualize_button.configure(state="normal")
            
        except Exception as e:
            print(f"DEBUG: Error showing error dialog: {e}")
    
    def set_tree_view(self, widget: ctk.CTkBaseClass):
        """Replace the tree view placeholder with actual visualization"""
        try:
                        
            if hasattr(self, 'tree_view') and self.tree_view:
                print(f"DEBUG: Destroying old tree view: {type(self.tree_view)}")
                try:
                    self.tree_view.destroy()
                except Exception as e:
                    print(f"DEBUG: Error destroying old tree view: {e}")
            
            content_settings = self.settings_manager.get('layout.content')
            print(f"DEBUG: Setting new tree view: {type(widget)}")
            self.tree_view = widget
            self.tree_view.grid(
                row=0,
                column=0,
                sticky="nsew",
                padx=content_settings['padding']['x'],
                pady=content_settings['padding']['y']
            )
            
            # Force update of the layout
            self.content_frame.update_idletasks()
            self.update_idletasks()
            

            
        except Exception as e:
            print(f"DEBUG: Error in set_tree_view: {e}")
            import traceback
            print(traceback.format_exc())
    
    def update_node_info(self, info_text: str):
        """Update the node information panel with new content"""
        try:
            self.node_info_text.delete("1.0", "end")
            self.node_info_text.insert("1.0", info_text)
        except Exception as e:
            print(f"DEBUG: Error updating node info: {e}")
    
    def clear_node_info(self):
        """Clear the node information panel"""
        try:
            self.node_info_text.delete("1.0", "end")
        except Exception as e:
            print(f"DEBUG: Error clearing node info: {e}")
    
    def reload_visualization(self):
        """Reload the last dataset"""
        try:
            if self._on_reload:
                self._on_reload()
            else:
                # Fallback to re-visualizing if no reload callback is set
                if self._on_visualize:
                    self._on_visualize()
        except Exception as e:
            print(f"DEBUG: Error reloading dataset: {e}")
            self.show_error(f"Error reloading dataset: {str(e)}")
    
    def open_in_browser(self):
        """Open the current visualization in browser"""
        try:
            if self._on_open_browser:
                self._on_open_browser()
            else:
                self.show_error("Open in browser functionality not available")
        except Exception as e:
            print(f"DEBUG: Error opening in browser: {e}")
            self.show_error(f"Error opening in browser: {str(e)}")
    
    def enable_open_browser_button(self):
        """Enable the Open in Browser button"""
        self.open_browser_button.configure(state="normal")
    
    def disable_open_browser_button(self):
        """Disable the Open in Browser button"""
        self.open_browser_button.configure(state="disabled")
    
    def show_coming_soon_dialog(self, node_id: str = None):
        """Show a Coming Soon dialog for future node detail features"""
        try:
            # Create coming soon dialog
            dialog = ctk.CTkToplevel(self)
            dialog.title("Node Details - Coming Soon")
            dialog.geometry("400x300")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
            y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")
            
            font_settings = self.settings_manager.get('fonts')
            
            # Coming soon message
            title_label = ctk.CTkLabel(
                dialog,
                text="🚧 Coming Soon! 🚧",
                font=ctk.CTkFont(
                    size=font_settings['section_title']['size'] + 10,
                    weight="bold"
                ),
                text_color="orange"
            )
            title_label.pack(padx=20, pady=(20, 10))
            
            message_label = ctk.CTkLabel(
                dialog,
                text="Node Detail View Feature\n\nThis feature will allow you to:\n• View detailed person information\n• Edit person details\n• Add/modify relationships\n• View family photos\n• Add notes and stories",
                font=ctk.CTkFont(
                    size=font_settings['normal']['size'],
                    weight=font_settings['normal']['weight']
                ),
                justify="left"
            )
            message_label.pack(padx=20, pady=10, expand=True)
            
            if node_id:
                node_info_label = ctk.CTkLabel(
                    dialog,
                    text=f"Selected Node: {node_id}",
                    font=ctk.CTkFont(
                        size=font_settings['status']['size'],
                        weight=font_settings['status']['weight']
                    ),
                    text_color="gray"
                )
                node_info_label.pack(padx=20, pady=(0, 10))
            
            # OK button
            ok_button = ctk.CTkButton(
                dialog,
                text="OK",
                command=dialog.destroy,
                width=100,
                font=ctk.CTkFont(
                    size=font_settings['normal']['size'],
                    weight=font_settings['normal']['weight']
                )
            )
            ok_button.pack(pady=(10, 20))
            
        except Exception as e:
            print(f"DEBUG: Error showing coming soon dialog: {e}")
    
    def handle_node_click_coming_soon(self, node_id: str):
        """Handle node clicks to show coming soon dialog"""
        try:
            print(f"DEBUG: Node clicked: {node_id}")
            self.show_coming_soon_dialog(node_id)
        except Exception as e:
            print(f"DEBUG: Error handling node click: {e}")