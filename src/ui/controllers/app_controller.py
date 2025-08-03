"""
Main application controller for the Family Tree application.
"""
from typing import Optional, Tuple, Dict, Any
import os
import json
import customtkinter as ctk
from ...core.interfaces.data_provider import DataProvider
from ...core.path_manager import path_manager
from ...data.xml_handler import XMLDataProvider
from ..views.main_window import MainWindow
from ..views.settings_dialog import SettingsDialog
from ..views.visualization_dialog import VisualizationDialog
from ..widgets.graph_viewer import GraphViewer
from ...graph.family import FamilyTreeGraph
from ...data.excel_converter import create_xml_from_excel_sheet
import datetime
import cairosvg

class AppController:
    def __init__(self):
        self.data_provider: Optional[DataProvider] = None
        self.main_window: Optional[MainWindow] = None
        self.current_data_dir: Optional[str] = None
        self.current_graph: Optional[FamilyTreeGraph] = None
        self.visualization_params: Dict[str, Any] = {
            'start_person': '',
            'generations_back': 0,
            'generations_forward': 0,
            'style': '1'  # Default to classic style
        }
        self.settings: Dict[str, Any] = self._load_settings()
        
        # Clean up old sessions on startup
        path_manager.cleanup_old_sessions(keep_count=5)
        
    def initialize(self):
        """Initialize the application"""
        self.main_window = MainWindow()
        self._setup_event_handlers()
        self._apply_settings()
        
    def run(self):
        """Start the application"""
        if self.main_window:
            self.main_window.mainloop()
    
    def _setup_event_handlers(self):
        """Set up event handlers for the main window"""
        if self.main_window:
            self.main_window.set_callbacks(
                on_data_loaded=self.handle_load_data,
                on_visualize=self.handle_visualize_tree,
                on_settings=self.handle_settings,
                on_reload=self.handle_reload_data
            )
    
    def handle_load_data(self, file_path: str, sheet_name: str):
        """Handle loading data from Excel file"""
        try:
            print(f"\nDEBUG: Loading data from Excel file: {file_path}")
            print(f"DEBUG: Sheet name: {sheet_name}")
            
            # Create XML directory based on Excel file and sheet names
            excel_base_name = os.path.splitext(os.path.basename(file_path))[0]
            xml_dir = os.path.join("assets", excel_base_name, sheet_name)
            
            # Create XML files from Excel
            xml_dir = create_xml_from_excel_sheet(file_path, sheet_name, xml_dir)
            print(f"DEBUG: XML files created in: {xml_dir}")
            
            # Initialize data provider with the XML directory
            self._initialize_data_provider(xml_dir)
            print("DEBUG: Data provider initialized")
            
            # Save last dataset information for reload functionality
            self._save_last_dataset(file_path, sheet_name, xml_dir)
            
            if self.main_window:
                self.main_window.update_status(
                    f"Loaded data from {os.path.basename(file_path)} - {sheet_name}",
                    enable_visualize=True  # Always enable visualization after loading data
                )
            
        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                print(traceback.format_exc())
            if self.main_window:
                self.main_window.show_error(f"Error loading data: {str(e)}")
                # Still keep visualize enabled in case they want to try again
                self.main_window.update_status("Error loading data", enable_visualize=True)
    
    def handle_visualize_tree(self):
        """Handle tree visualization request"""
        if not self.current_data_dir:
            if self.main_window:
                self.main_window.show_error("No data loaded. Please load data first.")
            return
        
        # Show dialog to get visualization parameters
        params = self._show_visualization_dialog()
        if not params:
            return  # User cancelled
        
        try:
            # Create new session for this visualization
            session_dir = path_manager.create_session()
            
            # Store visualization parameters
            self.visualization_params = params
            
            # Create graph with appropriate parameters
            if params.get('generate_all', False):
                # Generate complete tree
                self.current_graph = FamilyTreeGraph(
                    xml_data_dir=self.current_data_dir
                )
            else:
                # Generate specific view
                start_person = params.get('start_person', '')
                self.current_graph = FamilyTreeGraph(
                    xml_data_dir=self.current_data_dir,
                    start_person_name=start_person if start_person else None,
                    generations_back=params.get('generations_back', 0),
                    generations_forward=params.get('generations_forward', 0)
                )
            
            # Generate visualization
            if self.current_graph and self.current_graph.characters:
                # Get output format from settings
                export_settings = self.settings.get('export', {})
                export_format = export_settings.get('format', 'svg').lower()
                
                # Generate the visualization
                output_path = self.current_graph.generate_visualization(
                    output_format=export_format,
                    output_dir=session_dir
                )
                
                if output_path and os.path.exists(output_path):
                    # Show the visualization
                    self._show_visualization(output_path, export_format)
                    
                    # Auto-export if enabled
                    if self.settings.get('export', {}).get('auto_export', False):
                        self._auto_export_visualization(output_path, export_format)
                else:
                    if self.main_window:
                        self.main_window.show_error("Failed to generate visualization")
            else:
                if self.main_window:
                    # Provide more specific error message based on the situation
                    if not self.current_graph:
                        self.main_window.show_error("Failed to create family tree graph")
                    elif not params.get('generate_all', False) and params.get('start_person'):
                        # Person-specific search failed
                        self.main_window.show_error(
                            f"Could not find person '{params.get('start_person', '')}' or no family members found.\n"
                            f"Please check the name spelling or try different generation settings."
                        )
                    else:
                        self.main_window.show_error("No characters found to graph")
        
        except Exception as e:
            error_msg = f"Error creating visualization: {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            if hasattr(e, '__traceback__'):
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
            if self.main_window:
                self.main_window.show_error(error_msg)
    
    def _show_visualization_dialog(self) -> Optional[Dict[str, Any]]:
        """Show dialog to get visualization parameters"""
        if self.main_window:
            dialog = VisualizationDialog(self.main_window)
            return dialog.get_parameters()
        return None
    
    def handle_settings(self):
        """Handle settings dialog"""
        if self.main_window:
            dialog = SettingsDialog(self.main_window)
            settings = dialog.get_settings()
            
            if settings:
                self.settings = settings
                self._apply_settings()
                self._save_settings()
    
    def handle_reload_data(self):
        """Handle reloading the last dataset"""
        try:
            # Get last dataset information
            last_dataset_info = path_manager.get_last_dataset()
            
            if not last_dataset_info:
                if self.main_window:
                    self.main_window.show_error("No previous dataset found to reload")
                return
            
            file_path = last_dataset_info.get('file_path')
            sheet_name = last_dataset_info.get('sheet_name')
            xml_dir = last_dataset_info.get('xml_dir')
            
            if not all([file_path, sheet_name, xml_dir]):
                if self.main_window:
                    self.main_window.show_error("Incomplete last dataset information")
                return
            
            # Check if the original Excel file still exists
            if not os.path.exists(file_path):
                if self.main_window:
                    self.main_window.show_error(f"Original file not found: {file_path}")
                return
            
            # Check if XML directory still exists, if not recreate
            if not os.path.exists(xml_dir):
                print(f"DEBUG: XML directory not found, recreating from Excel file")
                # Recreate XML files from Excel
                xml_dir = create_xml_from_excel_sheet(file_path, sheet_name, xml_dir)
            
            # Initialize data provider
            self._initialize_data_provider(xml_dir)
            print(f"DEBUG: Reloaded dataset from {file_path} - {sheet_name}")
            
            if self.main_window:
                self.main_window.update_status(
                    f"Reloaded data from {os.path.basename(file_path)} - {sheet_name}",
                    enable_visualize=True
                )
        
        except Exception as e:
            error_msg = f"Error reloading dataset: {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            if self.main_window:
                self.main_window.show_error(error_msg)
    
    def handle_node_click(self, node_id: str):
        """Handle node click for interactive person selection"""
        if not self.current_graph:
            return
        
        # Get person data from the graph for context
        person_data = self.current_graph.characters.get(node_id)
        if not person_data:
            print(f"DEBUG: No data found for node ID: {node_id}")
            return
        
        # For now, show "Coming Soon" dialog - detailed view is a future feature
        person_name = person_data.get('name', node_id)
        print(f"DEBUG: Node clicked: {node_id} ({person_name})")
        
        if self.main_window:
            self.main_window.show_coming_soon_dialog(f"{node_id} - {person_name}")
    
    def _show_person_details(self, node_id: str):
        """Show detailed information for a person"""
        if not self.current_graph or not node_id:
            return
        
        person_data = self.current_graph.characters.get(node_id)
        if not person_data:
            return
        
        # Create details window
        details_window = ctk.CTkToplevel(self.main_window)
        details_window.title("Person Details")
        details_window.geometry("600x400")
        details_window.resizable(True, True)
        
        # Make it modal
        details_window.transient(self.main_window)
        details_window.grab_set()
        
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(details_window)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Person name as title
        person_name = person_data.get('name', node_id)
        title_label = ctk.CTkLabel(
            scroll_frame,
            text=person_name,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create details grid
        details_frame = ctk.CTkFrame(scroll_frame)
        details_frame.pack(fill="x", padx=10, pady=5)
        
        # Define fields to display
        fields = [
            ('ID', 'id'),
            ('Name', 'name'),
            ('Birth Date', 'birthday'),
            ('Birth Place', 'birth_place'),
            ('Death Date', 'date_of_death'),
            ('Death Place', 'place_of_burial'),
            ('Marital Status', 'marital_status'),
            ('Marriage Date', 'marriage_date'),
            ('Marriage Place', 'place_of_marriage'),
            ('Spouse', 'spouse'),
            ('Father', 'father'),
            ('Mother', 'mother')
        ]
        
        row = 0
        for label, field in fields:
            value = person_data.get(field, '')
            if value:  # Only show non-empty fields
                # Label
                label_widget = ctk.CTkLabel(
                    details_frame,
                    text=f"{label}:",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                label_widget.grid(row=row, column=0, sticky="w", padx=10, pady=5)
                
                # Value
                value_widget = ctk.CTkLabel(
                    details_frame,
                    text=str(value),
                    font=ctk.CTkFont(size=14)
                )
                value_widget.grid(row=row, column=1, sticky="w", padx=10, pady=5)
                
                row += 1
        
        # Configure grid weights
        details_frame.grid_columnconfigure(1, weight=1)
        
        # Close button
        close_button = ctk.CTkButton(
            details_window,
            text="Close",
            command=details_window.destroy
        )
        close_button.pack(pady=10)
    
    def _add_person_info_to_frame(self, frame: ctk.CTkFrame, person_data: Dict[str, Any]):
        """Add formatted person information to the frame"""
        # Name
        name_label = ctk.CTkLabel(
            frame,
            text=person_data.get('name', 'Unknown'),
            font=ctk.CTkFont(size=18, weight="bold")
        )
        name_label.pack(pady=(0, 10))
        
        # Basic Information
        info_fields = [
            ('ID', 'id'),
            ('Gender', 'gender'),
            ('Birth Date', 'birthday'),
            ('Death Date', 'date_of_death'),
            ('Birth Place', 'birth_place'),
            ('Death Place', 'death_place'),
            ('Father ID', 'father_id'),
            ('Mother ID', 'mother_id'),
            ('Spouse ID', 'spouse_id')
        ]
        
        for label, field in info_fields:
            value = person_data.get(field, '')
            if value:
                info_frame = ctk.CTkFrame(frame)
                info_frame.pack(fill="x", pady=2)
                
                label_widget = ctk.CTkLabel(
                    info_frame,
                    text=f"{label}:",
                    font=ctk.CTkFont(weight="bold")
                )
                label_widget.pack(side="left", padx=5)
                
                value_widget = ctk.CTkLabel(info_frame, text=str(value))
                value_widget.pack(side="left", padx=5)
        
        # Additional information
        additional_info = [
            ('Occupation', 'occupation'),
            ('Education', 'education'),
            ('Military Service', 'military_service'),
            ('Religion', 'religion'),
            ('Notes', 'notes')
        ]
        
        for label, field in additional_info:
            value = person_data.get(field, '')
            if value:
                info_frame = ctk.CTkFrame(frame)
                info_frame.pack(fill="x", pady=2)
                
                label_widget = ctk.CTkLabel(
                    info_frame,
                    text=f"{label}:",
                    font=ctk.CTkFont(weight="bold")
                )
                label_widget.pack(anchor="w", padx=5)
                
                # For longer text, use a text widget
                if len(str(value)) > 50:
                    text_widget = ctk.CTkTextbox(info_frame, height=60)
                    text_widget.pack(fill="x", padx=5, pady=2)
                    text_widget.insert("1.0", str(value))
                    text_widget.configure(state="disabled")
                else:
                    value_widget = ctk.CTkLabel(info_frame, text=str(value))
                    value_widget.pack(anchor="w", padx=5)
    
    def _initialize_data_provider(self, data_dir: str):
        """Initialize the data provider with the given directory"""
        self.current_data_dir = data_dir
        self.data_provider = XMLDataProvider(data_dir)
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            settings_file = path_manager.get_settings_file_path()
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                print(f"DEBUG: Loaded settings from {settings_file}")
                return settings
            
            # Default settings
            return {
                'appearance': {
                    'theme': 'system'
                },
                'export': {
                    'auto_export': False,
                    'format': 'svg'
                },
                'graph': {
                    'default_generations': 2
                }
            }
            
        except Exception as e:
            print(f"DEBUG ERROR: Error loading settings: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                print(traceback.format_exc())
            return {}
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            settings_file = path_manager.get_settings_file_path()
            
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            print(f"DEBUG: Saved settings to {settings_file}")
            
        except Exception as e:
            print(f"DEBUG ERROR: Error saving settings: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                print(traceback.format_exc())
    
    def _apply_settings(self):
        """Apply current settings"""
        try:
            # Apply appearance settings
            appearance = self.settings.get('appearance', {})
            theme = appearance.get('theme', 'system')
            ctk.set_appearance_mode(theme)
            
            # Apply graph settings
            graph = self.settings.get('graph', {})
            default_generations = graph.get('default_generations', 2)
            self.visualization_params['generations_back'] = default_generations
            self.visualization_params['generations_forward'] = default_generations
            
            print("DEBUG: Applied settings successfully")
            
        except Exception as e:
            print(f"DEBUG ERROR: Error applying settings: {str(e)}")
            if hasattr(e, '__traceback__'):
                print(traceback.format_exc())
    
    def _export_visualization(self):
        """Export visualization based on settings"""
        try:
            if not self.current_graph:
                return
            
            # Get export settings
            export_settings = self.settings.get('export', {})
            export_format = export_settings.get('format', 'svg').lower()
            
            # Export based on format
            if export_format in ['svg', 'both']:
                # SVG is already generated by graphviz
                svg_path = self.current_graph.get_svg_path()
                print(f"DEBUG: SVG available at {svg_path}")
            
            if export_format in ['png', 'both']:
                # Convert SVG to PNG
                svg_path = self.current_graph.get_svg_path()
                png_path = self.current_graph.get_png_path()
                
                if os.path.exists(svg_path):
                    cairosvg.svg2png(
                        url=svg_path,
                        write_to=png_path,
                        output_width=1600,
                        output_height=1200
                    )
                    print(f"DEBUG: Exported PNG to {png_path}")
            
        except Exception as e:
            print(f"DEBUG ERROR: Error exporting visualization: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                print(traceback.format_exc())
            if self.main_window:
                self.main_window.show_error(f"Error exporting visualization: {str(e)}")

    def _show_visualization(self, output_path: str, export_format: str):
        """Show the generated visualization in the appropriate viewer"""
        try:
            print(f"DEBUG: Showing visualization: {output_path} (format: {export_format})")
            
            if export_format.lower() == 'html':
                # Open HTML file in browser
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(output_path)}")
                print(f"DEBUG: Opened HTML visualization in browser")
            elif export_format.lower() in ['svg', 'png']:
                # Show in embedded viewer
                if self.main_window:
                    try:
                        # Try to show in embedded viewer
                        viewer = GraphViewer(self.main_window, output_path)
                        viewer.show()
                        print(f"DEBUG: Displayed visualization in embedded viewer")
                    except Exception as viewer_error:
                        print(f"DEBUG: Could not show in embedded viewer: {viewer_error}")
                        # Fallback to system default
                        import webbrowser
                        webbrowser.open(f"file://{os.path.abspath(output_path)}")
                        print(f"DEBUG: Opened visualization with system default")
            
            # Update status
            if self.main_window:
                self.main_window.update_status(f"Visualization generated: {os.path.basename(output_path)}")
                
        except Exception as e:
            print(f"DEBUG ERROR: Error showing visualization: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                print(traceback.format_exc())
            if self.main_window:
                self.main_window.show_error(f"Error showing visualization: {str(e)}")
    
    def _auto_export_visualization(self, output_path: str, export_format: str):
        """Auto-export visualization in additional formats if enabled"""
        try:
            export_settings = self.settings.get('export', {})
            auto_export = export_settings.get('auto_export', False)
            
            if not auto_export:
                return
            
            print(f"DEBUG: Auto-exporting visualization from {output_path}")
            
            # Get base path without extension
            base_path = os.path.splitext(output_path)[0]
            
            # Export to PNG if not already PNG
            if export_format.lower() != 'png':
                png_path = f"{base_path}.png"
                if output_path.endswith('.svg'):
                    cairosvg.svg2png(
                        url=output_path,
                        write_to=png_path,
                        output_width=1600,
                        output_height=1200
                    )
                    print(f"DEBUG: Auto-exported PNG to {png_path}")
            
            # Export to SVG if not already SVG
            if export_format.lower() != 'svg' and self.current_graph:
                svg_path = self.current_graph.get_svg_path()
                if os.path.exists(svg_path):
                    print(f"DEBUG: SVG already available at {svg_path}")
                    
        except Exception as e:
            print(f"DEBUG ERROR: Error in auto-export: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                print(traceback.format_exc())
    
    def _save_last_dataset(self, file_path: str, sheet_name: str, xml_dir: str):
        """Save last dataset information for reload functionality"""
        try:
            # Save last dataset information
            last_dataset_info = {
                'file_path': file_path,
                'sheet_name': sheet_name,
                'xml_dir': xml_dir
            }
            
            # Save to file
            path_manager.save_last_dataset(last_dataset_info)
            
            print("DEBUG: Last dataset information saved successfully")
            
        except Exception as e:
            print(f"DEBUG ERROR: Error saving last dataset information: {str(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                print(traceback.format_exc())

class VisualizationDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Visualization Parameters")
        self.geometry("400x400")  # Made taller for new option
        
        # Center the dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Generate All option
        self.generate_all_var = ctk.BooleanVar(value=False)
        self.generate_all = ctk.CTkCheckBox(
            self,
            text="Generate Complete Tree",
            variable=self.generate_all_var,
            command=self._toggle_inputs
        )
        self.generate_all.pack(padx=20, pady=(20, 10), fill="x")
        
        # Parameters frame
        self.params_frame = ctk.CTkFrame(self)
        self.params_frame.pack(padx=20, pady=10, fill="x")
        
        # Create widgets
        self.start_person = ctk.CTkEntry(
            self.params_frame,
            placeholder_text="Starting person (optional)"
        )
        self.start_person.pack(padx=20, pady=10, fill="x")
        
        # Generations back with label
        ctk.CTkLabel(
            self.params_frame,
            text="Generations Back (ancestors):"
        ).pack(padx=20, pady=(10, 0), anchor="w")
        
        self.generations_back = ctk.CTkEntry(
            self.params_frame,
            placeholder_text="Number of generations back"
        )
        self.generations_back.pack(padx=20, pady=(0, 10), fill="x")
        self.generations_back.insert(0, "0")
        
        # Generations forward with label
        ctk.CTkLabel(
            self.params_frame,
            text="Generations Forward (descendants):"
        ).pack(padx=20, pady=(10, 0), anchor="w")
        
        self.generations_forward = ctk.CTkEntry(
            self.params_frame,
            placeholder_text="Number of generations forward"
        )
        self.generations_forward.pack(padx=20, pady=(0, 10), fill="x")
        self.generations_forward.insert(0, "0")
        
        # Style selection
        self.style_var = ctk.StringVar(value="1")
        self.style_frame = ctk.CTkFrame(self)
        self.style_frame.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(self.style_frame, text="Style:").pack(side="left", padx=5)
        ctk.CTkRadioButton(
            self.style_frame, text="Classic",
            variable=self.style_var, value="1"
        ).pack(side="left", padx=10)
        ctk.CTkRadioButton(
            self.style_frame, text="Embedded",
            variable=self.style_var, value="2"
        ).pack(side="left", padx=10)
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(padx=20, pady=20, fill="x")
        
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel",
            command=self.cancel
        )
        self.cancel_button.pack(side="left", padx=10, expand=True)
        
        self.ok_button = ctk.CTkButton(
            self.button_frame, text="OK",
            command=self.confirm
        )
        self.ok_button.pack(side="left", padx=10, expand=True)
        
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.grab_set()
        self.wait_window()
    
    def _toggle_inputs(self):
        """Enable/disable input fields based on Generate All checkbox"""
        state = "disabled" if self.generate_all_var.get() else "normal"
        self.start_person.configure(state=state)
        self.generations_back.configure(state=state)
        self.generations_forward.configure(state=state)
    
    def cancel(self):
        """Cancel the dialog"""
        self.result = None
        self.destroy()
    
    def confirm(self):
        """Confirm the dialog"""
        try:
            if self.generate_all_var.get():
                self.result = {
                    'generate_all': True,
                    'style': self.style_var.get()
                }
            else:
                self.result = {
                    'generate_all': False,
                    'start_person': self.start_person.get().strip(),
                    'generations_back': int(self.generations_back.get() or 0),
                    'generations_forward': int(self.generations_forward.get() or 0),
                    'style': self.style_var.get()
                }
            self.destroy()
        except ValueError:
            # Show error if generations are not valid numbers
            error_dialog = ctk.CTkInputDialog(
                text="Please enter valid numbers for generations",
                title="Error"
            )
            error_dialog.destroy()
    
    def get_parameters(self) -> Optional[Dict[str, Any]]:
        """Get the dialog results"""
        return self.result 