"""
app.py
Main application window for the family tree visualization tool.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import Optional

from ..data.excel_converter import select_excel_file_and_sheet, create_xml_from_excel_sheet
from ..graph import D3FamilyTreeGraph
from .widgets.svg_viewer import SVGViewer

class FamilyTreeApp(tk.Tk):
    def __init__(self):
        """Initialize the main application window."""
        super().__init__()
        
        self.title("Family Tree Visualizer")
        self.geometry("1200x800")
        
        # Initialize variables
        self.current_graph: Optional[D3FamilyTreeGraph] = None
        self.current_svg_path: Optional[str] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create main menu
        self._create_menu()
        
        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar
        self._create_toolbar()
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize without SVG viewer
        self.svg_viewer = None
        self.status_var.set("Ready")
    
    def _create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Excel File...", command=self._open_excel_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self._zoom_in)
        view_menu.add_command(label="Zoom Out", command=self._zoom_out)
        view_menu.add_command(label="Reset View", command=self._reset_view)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menubar)
    
    def _create_toolbar(self):
        """Create the toolbar with common actions."""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Style buttons
        style = ttk.Style()
        style.configure("Tool.TButton", padding=5)
        
        # Add buttons
        ttk.Button(toolbar, text="Open Excel", style="Tool.TButton",
                  command=self._open_excel_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", style="Tool.TButton",
                  command=self._refresh_view).pack(side=tk.LEFT, padx=2)
        
        # Add style selector
        ttk.Label(toolbar, text="Style:").pack(side=tk.LEFT, padx=5)
        self.style_var = tk.StringVar(value="classic")
        style_combo = ttk.Combobox(toolbar, textvariable=self.style_var,
                                 values=["Classic", "Embedded"], state="readonly")
        style_combo.pack(side=tk.LEFT, padx=5)
        style_combo.bind("<<ComboboxSelected>>", self._on_style_change)
    
    def _open_excel_file(self):
        """Handle opening an Excel file."""
        try:
            excel_file_path, sheet_name = select_excel_file_and_sheet()
            if not excel_file_path or not sheet_name:
                return
            
            # Create XML directory
            excel_base_name = os.path.splitext(os.path.basename(excel_file_path))[0]
            output_xml_dir = os.path.join("assets", excel_base_name, sheet_name)
            os.makedirs(output_xml_dir, exist_ok=True)
            
            # Convert Excel to XML
            self.status_var.set("Converting Excel to XML...")
            self.update_idletasks()
            create_xml_from_excel_sheet(excel_file_path, sheet_name, output_xml_dir)
            
            # Generate graph
            self._generate_graph(output_xml_dir)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Excel file: {e}")
            self.status_var.set("Error opening file")
    
    def _generate_graph(self, xml_dir: str):
        """Generate the family tree graph."""
        try:
            self.status_var.set("Generating family tree...")
            self.update_idletasks()
            
            # Always use D3 engine
            self.current_graph = D3FamilyTreeGraph(xml_data_dir=xml_dir, output_format="html")
            
            # Generate the graph
            self.current_svg_path = self.current_graph.generate_graph()
            
            # Display the SVG
            self._display_svg()
            
            self.status_var.set("Family tree generated successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating family tree: {e}")
            self.status_var.set("Error generating family tree")
    
    def _display_svg(self):
        """Display the SVG in the viewer."""
        if not self.current_svg_path:
            return
        
        # Remove existing viewer if any
        if self.svg_viewer:
            self.svg_viewer.pack_forget()
            self.svg_viewer.destroy()
        
        # Create new viewer
        self.svg_viewer = SVGViewer(self.main_frame, self.current_svg_path)
        self.svg_viewer.pack(fill=tk.BOTH, expand=True)
        
        # Set up callbacks
        self.svg_viewer.set_node_click_callback(self._on_node_click)
        self.svg_viewer.set_node_hover_callback(self._on_node_hover)
    
    def _on_node_click(self, node_id: str):
        """Handle node click events."""
        if self.current_graph and node_id in self.current_graph.characters:
            char_data = self.current_graph.characters[node_id]
            self.svg_viewer.show_node_info(char_data)
    
    def _on_node_hover(self, node_id: str):
        """Handle node hover events."""
        if self.current_graph and node_id in self.current_graph.characters:
            char_data = self.current_graph.characters[node_id]
            self.status_var.set(f"Hovering: {char_data.get('name', 'Unknown')}")
    
    def _on_style_change(self, event=None):
        """Handle style change events."""
        if self.current_graph:
            xml_dir = self.current_graph.xml_data_dir
            self._generate_graph(xml_dir)
    
    def _zoom_in(self):
        """Zoom in the view."""
        if self.svg_viewer:
            self.svg_viewer.zoom_in()
    
    def _zoom_out(self):
        """Zoom out the view."""
        if self.svg_viewer:
            self.svg_viewer.zoom_out()
    
    def _reset_view(self):
        """Reset the view."""
        if self.svg_viewer:
            self.svg_viewer.reset_view()
    
    def _refresh_view(self):
        """Refresh the current view."""
        if self.current_graph:
            self._generate_graph(self.current_graph.xml_data_dir)
    
    def _show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            "About Family Tree Visualizer",
            "Family Tree Visualizer\n\n"
            "A tool for visualizing family relationships\n"
            "from Excel data.\n\n"
            "© 2024 Your Name"
        )

def main():
    """Main entry point for the UI application."""
    app = FamilyTreeApp()
    app.mainloop()

if __name__ == "__main__":
    main() 