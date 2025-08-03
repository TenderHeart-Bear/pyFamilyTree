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
        Check if a point is within an SVG element's bounds using precise collision detection.
        
        Args:
            x: X coordinate
            y: Y coordinate
            element: SVG element
            
        Returns:
            bool: True if point is within element bounds
        """
        try:
            # Check different element types with proper collision detection
            if element.tag.endswith('polygon'):
                return self._point_in_polygon(x, y, element)
            elif element.tag.endswith('rect'):
                return self._point_in_rect(x, y, element)
            elif element.tag.endswith('ellipse'):
                return self._point_in_ellipse(x, y, element)
            else:
                # Fallback to bounding box for other elements
                elem_x = float(element.get('x', 0))
                elem_y = float(element.get('y', 0))
                elem_width = float(element.get('width', 0))
                elem_height = float(element.get('height', 0))
                
                return (elem_x <= x <= elem_x + elem_width and
                        elem_y <= y <= elem_y + elem_height)
                        
        except (ValueError, TypeError):
            return False
    
    def _point_in_polygon(self, x: float, y: float, polygon) -> bool:
        """
        Check if point is inside a polygon using ray casting algorithm.
        """
        points_str = polygon.get('points', '')
        if not points_str:
            return False
        
        # Parse polygon points
        coords = []
        for coord in points_str.replace(',', ' ').split():
            try:
                coords.append(float(coord))
            except ValueError:
                continue
        
        # Group into (x, y) pairs
        points = [(coords[i], coords[i+1]) for i in range(0, len(coords)-1, 2)]
        
        if len(points) < 3:
            return False
        
        # Ray casting algorithm with edge case handling
        inside = False
        j = len(points) - 1
        
        for i in range(len(points)):
            xi, yi = points[i]
            xj, yj = points[j]
            
            # Check if point is exactly on an edge
            if self._point_on_edge(x, y, xi, yi, xj, yj):
                return True
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    def _point_on_edge(self, px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> bool:
        """
        Check if a point lies on a line segment (edge of polygon).
        """
        # Calculate cross product to check if point is on the line
        cross_product = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
        
        # If cross product is not zero, point is not on the line
        if abs(cross_product) > 1e-10:  # Small epsilon for floating point precision
            return False
        
        # Check if point is within the segment bounds
        dot_product = (px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)
        squared_distance = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1)
        
        return 0 <= dot_product <= squared_distance
    
    def _point_in_rect(self, x: float, y: float, rect) -> bool:
        """
        Check if point is inside a rectangle with rounded corners support.
        """
        rect_x = float(rect.get('x', 0))
        rect_y = float(rect.get('y', 0))
        width = float(rect.get('width', 0))
        height = float(rect.get('height', 0))
        rx = float(rect.get('rx', 0))  # Corner radius
        ry = float(rect.get('ry', 0))
        
        # Check if point is within rectangular bounds
        if not (rect_x <= x <= rect_x + width and rect_y <= y <= rect_y + height):
            return False
        
        # If no rounded corners, we're done
        if rx <= 0 and ry <= 0:
            return True
        
        # Handle rounded corners
        if rx > 0 or ry > 0:
            if ry <= 0:
                ry = rx
            if rx <= 0:
                rx = ry
                
            # Check corner exclusion zones
            corners = [
                (rect_x + rx, rect_y + ry, x < rect_x + rx and y < rect_y + ry),
                (rect_x + width - rx, rect_y + ry, x > rect_x + width - rx and y < rect_y + ry),
                (rect_x + rx, rect_y + height - ry, x < rect_x + rx and y > rect_y + height - ry),
                (rect_x + width - rx, rect_y + height - ry, x > rect_x + width - rx and y > rect_y + height - ry)
            ]
            
            for cx, cy, in_corner in corners:
                if in_corner:
                    # Check if point is outside the corner radius
                    dx = (x - cx) / rx
                    dy = (y - cy) / ry
                    if (dx * dx + dy * dy) > 1:
                        return False
        
        return True
    
    def _point_in_ellipse(self, x: float, y: float, ellipse) -> bool:
        """
        Check if point is inside an ellipse.
        """
        cx = float(ellipse.get('cx', 0))
        cy = float(ellipse.get('cy', 0))
        rx = float(ellipse.get('rx', 0))
        ry = float(ellipse.get('ry', 0))
        
        if rx <= 0 or ry <= 0:
            return False
        
        # Ellipse equation: ((x-cx)/rx)² + ((y-cy)/ry)² <= 1
        dx = (x - cx) / rx
        dy = (y - cy) / ry
        
        return (dx * dx + dy * dy) <= 1
    
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