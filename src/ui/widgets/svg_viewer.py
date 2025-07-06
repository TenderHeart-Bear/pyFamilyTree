"""
svg_viewer.py
A simple SVG viewer widget with interactive features for family tree visualization.
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cairosvg
import io
import json
from typing import Dict, Callable, Optional
import xml.etree.ElementTree as ET

class SVGViewer(ttk.Frame):
    def __init__(self, master: tk.Widget, svg_path: str):
        """
        Initialize the SVG viewer widget.
        
        Args:
            master: Parent widget
            svg_path: Path to the SVG file to display
        """
        super().__init__(master)
        self.svg_path = svg_path
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.dragging = False
        self.last_x = 0
        self.last_y = 0
        
        # Callbacks for node interactions
        self.node_click_callback: Optional[Callable[[str], None]] = None
        self.node_hover_callback: Optional[Callable[[str], None]] = None
        
        self._setup_ui()
        self._load_svg()
        self._bind_events()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Create canvas for SVG display
        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        self.h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        
        # Pack scrollbars
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add zoom controls
        self.zoom_frame = ttk.Frame(self)
        self.zoom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(self.zoom_frame, text="+", command=self.zoom_in).pack(side=tk.LEFT)
        ttk.Button(self.zoom_frame, text="-", command=self.zoom_out).pack(side=tk.LEFT)
        ttk.Button(self.zoom_frame, text="Reset", command=self.reset_view).pack(side=tk.LEFT)
        
        # Add info panel
        self.info_panel = ttk.LabelFrame(self, text="Node Information")
        self.info_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text = tk.Text(self.info_panel, wrap=tk.WORD, width=30, height=10)
        self.info_text.pack(padx=5, pady=5)
    
    def _load_svg(self):
        """Load and display the SVG file."""
        try:
            # Convert SVG to PNG using cairosvg
            png_data = cairosvg.svg2png(url=self.svg_path, scale=self.zoom_level)
            
            # Create PIL Image from PNG data
            image = Image.open(io.BytesIO(png_data))
            
            # Convert to PhotoImage for Tkinter
            self.photo = ImageTk.PhotoImage(image)
            
            # Display on canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            
            # Update canvas scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            print(f"Error loading SVG: {e}")
    
    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Middle mouse button for panning
        self.canvas.bind("<Button-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._pan)
        self.canvas.bind("<ButtonRelease-2>", self._end_pan)
        
        # Left click for node selection
        self.canvas.bind("<Button-1>", self._on_click)
        
        # Mouse motion for hover effects
        self.canvas.bind("<Motion>", self._on_hover)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel events for zooming."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def _start_pan(self, event):
        """Start panning the view."""
        self.dragging = True
        self.last_x = event.x
        self.last_y = event.y
    
    def _pan(self, event):
        """Pan the view while dragging."""
        if self.dragging:
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            self.pan_x += dx
            self.pan_y += dy
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self.last_x = event.x
            self.last_y = event.y
    
    def _end_pan(self, event):
        """End panning."""
        self.dragging = False
    
    def _on_click(self, event):
        """Handle node clicks."""
        # Get clicked element from SVG
        element = self._get_element_at(event.x, event.y)
        if element and self.node_click_callback:
            self.node_click_callback(element)
    
    def _on_hover(self, event):
        """Handle mouse hover over nodes."""
        # Get hovered element from SVG
        element = self._get_element_at(event.x, event.y)
        if element and self.node_hover_callback:
            self.node_hover_callback(element)
    
    def _get_element_at(self, x: int, y: int) -> Optional[str]:
        """
        Get the SVG element at the given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            str: Element ID if found, None otherwise
        """
        try:
            # Convert canvas coordinates to SVG coordinates
            canvas_x = self.canvas.canvasx(x)
            canvas_y = self.canvas.canvasy(y)
            
            # Scale coordinates based on zoom level
            svg_x = canvas_x / self.zoom_level
            svg_y = canvas_y / self.zoom_level
            
            # Parse SVG file to find element at coordinates
            tree = ET.parse(self.svg_path)
            root = tree.getroot()
            
            # Find clickable elements (nodes with IDs)
            for elem in root.iter():
                if elem.get('id'):
                    # Check if coordinates are within element bounds
                    # This is a simplified check - more complex geometry would need proper SVG parsing
                    if self._point_in_element(svg_x, svg_y, elem):
                        return elem.get('id')
            
            return None
            
        except Exception as e:
            print(f"Error getting element at coordinates: {e}")
            return None
    
    def _point_in_element(self, x: float, y: float, element) -> bool:
        """
        Check if a point is within an SVG element's bounds.
        
        Args:
            x: X coordinate
            y: Y coordinate
            element: SVG element
            
        Returns:
            bool: True if point is within element bounds
        """
        try:
            # Get element attributes
            elem_x = float(element.get('x', 0))
            elem_y = float(element.get('y', 0))
            elem_width = float(element.get('width', 0))
            elem_height = float(element.get('height', 0))
            
            # Check if point is within rectangular bounds
            return (elem_x <= x <= elem_x + elem_width and
                    elem_y <= y <= elem_y + elem_height)
                    
        except (ValueError, TypeError):
            return False
    
    def zoom_in(self):
        """Zoom in the view."""
        self.zoom_level *= 1.2
        self._load_svg()
    
    def zoom_out(self):
        """Zoom out the view."""
        self.zoom_level /= 1.2
        self._load_svg()
    
    def reset_view(self):
        """Reset the view to original size and position."""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._load_svg()
    
    def set_node_click_callback(self, callback: Callable[[str], None]):
        """Set callback for node clicks."""
        self.node_click_callback = callback
    
    def set_node_hover_callback(self, callback: Callable[[str], None]):
        """Set callback for node hover events."""
        self.node_hover_callback = callback
    
    def show_node_info(self, node_data: Dict):
        """Display node information in the info panel."""
        self.info_text.delete(1.0, tk.END)
        info_str = f"Name: {node_data.get('name', 'Unknown')}\n"
        info_str += f"Birth: {node_data.get('birth_date', '?')}\n"
        info_str += f"Death: {node_data.get('death_date', '')}\n"
        info_str += f"ID: {node_data.get('id', '')}\n"
        self.info_text.insert(tk.END, info_str)
    
    def clear_node_info(self):
        """Clear the info panel."""
        self.info_text.delete(1.0, tk.END) 