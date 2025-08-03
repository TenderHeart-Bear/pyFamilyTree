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
from typing import Dict, Callable, Optional, Any
import xml.etree.ElementTree as ET

class SVGViewer(ttk.Frame):
    def __init__(self, master: tk.Widget, svg_path: str, character_data: Dict[str, Dict[str, Any]] = None):
        """
        Initialize the SVG viewer widget.
        
        Args:
            master: Parent widget
            svg_path: Path to the SVG file to display
            character_data: Dictionary mapping person IDs to their data (for clickable areas)
        """
        super().__init__(master)
        self.svg_path = svg_path
        self.character_data = character_data or {}
        # Initialize variables
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.dragging = False
        self.drag_started = False  # Track if drag actually started
        self.last_x = 0
        self.last_y = 0
        
        # Callbacks for node interactions
        self.node_click_callback: Optional[Callable[[str], None]] = None
        self.node_hover_callback: Optional[Callable[[str], None]] = None
        self.open_browser_callback: Optional[Callable[[], None]] = None
        
        # Store clickable areas
        self.clickable_areas = {}
        
        # Debug mode for showing clickable areas
        self.debug_clickable_areas = False
        
        self._setup_ui()
        self._load_svg()
        self._bind_events()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(main_frame, bg='white')
        
        # Create scrollbars with better configuration
        h_scrollbar = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        # Configure canvas scrolling
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Grid layout for better scrollbar positioning
        self.canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure grid weights for proper expansion
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Create zoom controls frame
        self.zoom_frame = ttk.Frame(self)
        self.zoom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add zoom controls
        ttk.Button(self.zoom_frame, text="Zoom In", command=self._zoom_in).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.zoom_frame, text="Zoom Out", command=self._zoom_out).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.zoom_frame, text="Reset Zoom", command=self._reset_zoom).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.zoom_frame, text="Debug Areas", command=self._toggle_debug_areas).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.zoom_frame, text="Open in Browser", command=self.open_in_browser).pack(side=tk.LEFT)
    
    def _load_svg(self):
        """Load and display the SVG file."""
        try:
            # Convert SVG to PNG using cairosvg with proper scaling
            # Use a reasonable scale to avoid over-zooming
            scale = min(1.0, self.zoom_level)  # Cap zoom level to prevent over-zooming
            png_data = cairosvg.svg2png(url=self.svg_path, scale=scale)
            
            # Create PIL Image from PNG data
            image = Image.open(io.BytesIO(png_data))
            
            # Convert to PhotoImage for Tkinter
            self.photo = ImageTk.PhotoImage(image)
            
            # Display on canvas
            self.canvas.delete("all")
            image_item = self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            
            # Get the actual image dimensions
            image_width = self.photo.width()
            image_height = self.photo.height()
            
            # Calculate scroll region to ensure all content is visible
            # Use the actual image size plus generous padding
            scroll_width = image_width + 200  # Extra padding for right side
            scroll_height = image_height + 200  # Extra padding for bottom
            
            # Set minimum scroll region to ensure scrollbars appear
            scroll_width = max(scroll_width, 1200)
            scroll_height = max(scroll_height, 800)
            
            # Ensure scroll region is at least as large as the canvas for smooth scrolling
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # If canvas hasn't been drawn yet, use reasonable defaults
            if canvas_width <= 1:
                canvas_width = 800
            if canvas_height <= 1:
                canvas_height = 600
            
            # Make sure scroll region is larger than canvas for proper scrolling
            scroll_width = max(scroll_width, canvas_width + 100)
            scroll_height = max(scroll_height, canvas_height + 100)
            
            self.canvas.configure(scrollregion=(0, 0, scroll_width, scroll_height))
            
            # Ensure scrollbars are properly configured
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            
            # Create clickable areas for nodes
            self._create_clickable_areas()
            
            print(f"DEBUG: SVG loaded - Image size: {image_width}x{image_height}")
            print(f"DEBUG: Scroll region set to: (0, 0, {scroll_width}, {scroll_height})")
            print(f"DEBUG: Created {len(self.clickable_areas)} clickable areas")
            print(f"DEBUG: Zoom level: {self.zoom_level}, Scale used: {scale}")
            
            # Debug: Check if scrollbars are needed
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            print(f"DEBUG: Canvas size: {canvas_width}x{canvas_height}")
            print(f"DEBUG: Scrollbars needed: {'Yes' if scroll_width > canvas_width or scroll_height > canvas_height else 'No'}")
            
        except Exception as e:
            print(f"Error loading SVG: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_clickable_areas(self):
        """Create invisible clickable rectangles for each node based on actual SVG positions"""
        try:
            # Clear existing clickable areas
            self.clickable_areas = {}
            
            # Parse the SVG file to get actual node positions and viewport info
            tree = ET.parse(self.svg_path)
            root = tree.getroot()
            
            # Get SVG viewport dimensions
            svg_width = None
            svg_height = None
            viewbox = None
            
            # Parse SVG dimensions
            width_attr = root.get('width')
            height_attr = root.get('height')
            viewbox_attr = root.get('viewBox')
            
            if width_attr and height_attr:
                try:
                    # Remove units like 'pt', 'px' etc.
                    svg_width = float(width_attr.replace('pt', '').replace('px', '').replace('cm', '').replace('mm', ''))
                    svg_height = float(height_attr.replace('pt', '').replace('px', '').replace('cm', '').replace('mm', ''))
                except ValueError:
                    pass
            
            if viewbox_attr:
                try:
                    viewbox_parts = viewbox_attr.split()
                    if len(viewbox_parts) >= 4:
                        viewbox = [float(x) for x in viewbox_parts]
                except ValueError:
                    pass
            
            # Find the main graph group and extract its transform
            main_transform_x = 0
            main_transform_y = 0
            for elem in root.iter():
                if elem.tag.endswith('g') and elem.get('id') == 'graph0':
                    transform = elem.get('transform', '')
                    # Parse transform like "scale(1 1) rotate(0) translate(4 839.2)"
                    if 'translate(' in transform:
                        import re
                        match = re.search(r'translate\(([-\d.]+)\s+([-\d.]+)\)', transform)
                        if match:
                            main_transform_x = float(match.group(1))
                            main_transform_y = float(match.group(2))
                    break
            
            # Calculate the actual scale used for PNG conversion
            actual_scale = min(1.0, self.zoom_level)
            
            # Get actual image dimensions
            image_width = self.photo.width() if hasattr(self, 'photo') and self.photo else None
            image_height = self.photo.height() if hasattr(self, 'photo') and self.photo else None
            
            print(f"DEBUG: SVG dimensions: {svg_width}x{svg_height}, ViewBox: {viewbox}")
            print(f"DEBUG: Main transform: translate({main_transform_x}, {main_transform_y})")
            print(f"DEBUG: Image dimensions: {image_width}x{image_height}, Scale: {actual_scale}")
            
            # Find all node groups (g elements with class="node")
            node_groups = []
            for elem in root.iter():
                if elem.tag.endswith('g') and elem.get('class') == 'node':
                    node_groups.append(elem)
            
            print(f"DEBUG: Found {len(node_groups)} node groups")
            
            for node_group in node_groups:
                # Get character ID from title element
                char_id = None
                title_elem = node_group.find('.//{http://www.w3.org/2000/svg}title')
                if title_elem is None:
                    # Try without namespace
                    title_elem = node_group.find('.//title')
                if title_elem is not None and title_elem.text:
                    char_id = title_elem.text.strip()
                
                if not char_id:
                    continue
                
                # Skip union/connector nodes (they contain 'x' or '-x-' in their IDs)
                if '-x-' in char_id or char_id.endswith('-x'):
                    print(f"DEBUG: Skipping union node {char_id}")
                    continue
                
                # Find the polygon element to get actual node boundaries
                polygon_elem = None
                for elem in node_group.iter():
                    if elem.tag.endswith('polygon'):
                        polygon_elem = elem
                        break
                
                if polygon_elem is not None:
                    points_attr = polygon_elem.get('points')
                    
                    if points_attr:
                        try:
                            # Parse polygon points to get bounding box
                            # Points format: "x1,y1 x2,y2 x3,y3 ..." or "x1 y1 x2 y2 ..."
                            points_str = points_attr.strip()
                            
                            # Split by spaces and handle comma-separated coordinates
                            coords = []
                            parts = points_str.split()
                            for part in parts:
                                if ',' in part:
                                    # Format: "x,y"
                                    x_str, y_str = part.split(',')
                                    coords.extend([float(x_str), float(y_str)])
                                else:
                                    # Format: separate x y values
                                    coords.append(float(part))
                            
                            # Extract x and y coordinates
                            x_coords = [coords[i] for i in range(0, len(coords), 2)]
                            y_coords = [coords[i] for i in range(1, len(coords), 2)]
                            
                            # Calculate bounding box
                            min_x = min(x_coords)
                            max_x = max(x_coords)
                            min_y = min(y_coords)
                            max_y = max(y_coords)
                            
                            # Calculate center and dimensions
                            center_x = (min_x + max_x) / 2
                            center_y = (min_y + max_y) / 2
                            node_width_svg = max_x - min_x
                            node_height_svg = max_y - min_y
                            
                            # Apply SVG coordinate transformations
                            # 1. Apply main group transform
                            transformed_x = center_x + main_transform_x
                            transformed_y = center_y + main_transform_y
                            
                            # 2. The main transform already handles coordinate system conversion
                            # Just use the transformed coordinates directly
                            screen_x = transformed_x
                            screen_y = transformed_y
                            
                            # 3. Scale for PNG conversion
                            scaled_x = screen_x * actual_scale
                            scaled_y = screen_y * actual_scale
                            scaled_width = node_width_svg * actual_scale
                            scaled_height = node_height_svg * actual_scale
                            
                            # Create clickable rectangle using actual node dimensions
                            outline_color = "red" if self.debug_clickable_areas else ""
                            outline_width = 2 if self.debug_clickable_areas else 0
                            rect_id = self.canvas.create_rectangle(
                                scaled_x - scaled_width/2, scaled_y - scaled_height/2,
                                scaled_x + scaled_width/2, scaled_y + scaled_height/2,
                                outline=outline_color, width=outline_width, fill="", tags="clickable"
                            )
                            
                            # Store the clickable area
                            self.clickable_areas[rect_id] = char_id
                            
                            print(f"DEBUG: Created clickable area for {char_id}")
                            print(f"  SVG polygon bounds: ({min_x},{min_y}) to ({max_x},{max_y})")
                            print(f"  SVG center: ({center_x}, {center_y})")
                            print(f"  SVG dimensions: {node_width_svg}x{node_height_svg}")
                            print(f"  Transformed center: ({transformed_x}, {transformed_y})")
                            print(f"  Screen center: ({screen_x}, {screen_y})")
                            print(f"  Canvas center: ({scaled_x}, {scaled_y})")
                            print(f"  Canvas dimensions: {scaled_width}x{scaled_height}")
                            
                        except (ValueError, IndexError) as e:
                            print(f"DEBUG: Could not parse polygon points for {char_id}: '{points_attr}', error: {e}")
                            continue
                else:
                    print(f"DEBUG: No polygon found for {char_id}, skipping")
            
            # If no SVG nodes found, fall back to character data approach
            if not self.clickable_areas and self.character_data:
                print("DEBUG: No SVG node groups found, using fallback positioning")
                self._create_fallback_clickable_areas()
                
        except Exception as e:
            print(f"Error creating clickable areas: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to character data approach
            if self.character_data:
                self._create_fallback_clickable_areas()
    
    def _create_fallback_clickable_areas(self):
        """Create clickable areas using estimated positions as fallback"""
        try:
            # Use the same actual scale as the main method
            actual_scale = min(1.0, self.zoom_level)
            
            # Estimate node positions based on character data
            node_width = 150 * actual_scale
            node_height = 60 * actual_scale
            spacing_x = 200 * actual_scale
            spacing_y = 100 * actual_scale
            
            # Create clickable areas for each character
            for i, (char_id, char_data) in enumerate(self.character_data.items()):
                # Calculate position (simplified grid layout)
                row = i // 3  # 3 nodes per row
                col = i % 3
                
                x = col * spacing_x + 50 * actual_scale
                y = row * spacing_y + 50 * actual_scale
                
                # Create clickable rectangle (visible only in debug mode)
                outline_color = "blue" if self.debug_clickable_areas else ""
                outline_width = 1 if self.debug_clickable_areas else 0
                rect_id = self.canvas.create_rectangle(
                    x, y, x + node_width, y + node_height,
                    outline=outline_color, width=outline_width, fill="", tags="clickable"
                )
                
                # Store the clickable area
                self.clickable_areas[rect_id] = char_id
                
                print(f"DEBUG: Created fallback clickable area for {char_id} at ({x}, {y})")
                
        except Exception as e:
            print(f"Error creating fallback clickable areas: {e}")
            import traceback
            traceback.print_exc()
    
    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Left mouse button for panning (click and drag)
        self.canvas.bind("<Button-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._pan)
        self.canvas.bind("<ButtonRelease-1>", self._end_pan)
        
        # Ctrl+Left click for node selection (more intuitive than right-click)
        self.canvas.bind("<Control-Button-1>", self._on_node_click)
        
        # Also allow simple clicks for node selection (when not dragging)
        self.canvas.bind("<ButtonRelease-1>", self._on_click_release)
        
        # Mouse motion for hover effects
        self.canvas.bind("<Motion>", self._on_hover)
        
        # Bind canvas resize to update scroll region
        self.canvas.bind("<Configure>", self._on_canvas_resize)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel events for zooming."""
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1
        
        # Limit zoom level to reasonable bounds
        self.zoom_level = max(0.1, min(2.0, self.zoom_level))
        
        # Reload SVG with new zoom level
        self._load_svg()
    
    def _zoom_in(self):
        """Zoom in using button."""
        self.zoom_level *= 1.2
        self.zoom_level = min(2.0, self.zoom_level)
        self._load_svg()
    
    def _zoom_out(self):
        """Zoom out using button."""
        self.zoom_level /= 1.2
        self.zoom_level = max(0.1, self.zoom_level)
        self._load_svg()
    
    def _reset_zoom(self):
        """Reset zoom to original size."""
        self.zoom_level = 1.0
        self._load_svg()
    
    def _toggle_debug_areas(self):
        """Toggle visibility of clickable area debug rectangles."""
        self.debug_clickable_areas = not self.debug_clickable_areas
        
        # Update existing clickable areas without reloading the entire SVG
        for rect_id in self.clickable_areas.keys():
            if self.debug_clickable_areas:
                # Make visible with red outline
                self.canvas.itemconfig(rect_id, outline="red", width=2)
            else:
                # Make invisible
                self.canvas.itemconfig(rect_id, outline="", width=0)
        
        print(f"DEBUG: Debug areas {'enabled' if self.debug_clickable_areas else 'disabled'}")
        print(f"DEBUG: Updated {len(self.clickable_areas)} clickable areas")
        
        # If enabling debug mode, show coordinate summary for first few areas
        if self.debug_clickable_areas and self.clickable_areas:
            print("DEBUG: Coordinate summary for first few clickable areas:")
            count = 0
            for rect_id, char_id in list(self.clickable_areas.items())[:3]:
                coords = self.canvas.coords(rect_id)
                if len(coords) >= 4:
                    x1, y1, x2, y2 = coords[:4]
                    print(f"  {char_id}: Canvas rect ({x1:.1f},{y1:.1f}) to ({x2:.1f},{y2:.1f})")
                count += 1
                if count >= 3:
                    break
    
    def _start_pan(self, event):
        """Start panning the view."""
        self.dragging = True
        self.drag_started = False  # Track if we actually started dragging
        self.last_x = event.x
        self.last_y = event.y
        # Change cursor to indicate panning
        self.canvas.config(cursor="fleur")
    
    def _pan(self, event):
        """Pan the view while dragging."""
        if self.dragging:
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            
            # Check if we've moved enough to consider it a drag
            if abs(dx) > 3 or abs(dy) > 3:
                self.drag_started = True
            
            # Use unit-based scrolling for smooth movement
            # Tkinter only supports "units" or "pages", not "pixels"
            # Adjust sensitivity for smoother movement
            scroll_dx = int(-dx / 2)  # Reduce sensitivity for smoother movement
            scroll_dy = int(-dy / 2)
            
            self.canvas.xview_scroll(scroll_dx, "units")
            self.canvas.yview_scroll(scroll_dy, "units")
            
            self.last_x = event.x
            self.last_y = event.y
    
    def _end_pan(self, event):
        """End panning."""
        self.dragging = False
        # Reset cursor
        self.canvas.config(cursor="")
    
    def _on_click_release(self, event):
        """Handle click release - if we didn't drag, treat as a node click."""
        if not self.drag_started:
            # This was a click, not a drag - handle as node click
            self._on_node_click(event)
        self.drag_started = False
    
    def _on_node_click(self, event):
        """Handle node clicks with any mouse button."""
        try:
            # Get canvas coordinates
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            # Find which clickable area was clicked using the exact click point
            clicked_items = self.canvas.find_overlapping(canvas_x, canvas_y, canvas_x, canvas_y)
            
            # If no items found at exact point, try a small area around the click
            if not clicked_items:
                clicked_items = self.canvas.find_overlapping(canvas_x - 2, canvas_y - 2, canvas_x + 2, canvas_y + 2)
            
            for item_id in clicked_items:
                if item_id in self.clickable_areas:
                    char_id = self.clickable_areas[item_id]
                    print(f"DEBUG: Clicked on character: {char_id} at canvas ({canvas_x:.1f}, {canvas_y:.1f})")
                    if self.node_click_callback:
                        self.node_click_callback(char_id)
                    return
            
            print(f"DEBUG: No character clicked at canvas ({canvas_x:.1f}, {canvas_y:.1f})")
            print(f"DEBUG: Found {len(clicked_items)} items at click location: {list(clicked_items)}")
            print(f"DEBUG: Available clickable areas: {list(self.clickable_areas.keys())}")
            
        except Exception as e:
            print(f"Error handling click: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_hover(self, event):
        """Handle mouse hover over nodes."""
        # For now, hover functionality is disabled
        # Could be implemented similar to click detection if needed
        pass
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize events to update scroll region."""
        # Update scroll region when canvas is resized
        if hasattr(self, 'photo') and self.photo:
            # Recalculate scroll region based on new canvas size
            canvas_width = event.width
            canvas_height = event.height
            
            # Get current scroll region
            current_region = self.canvas.bbox("all")
            if current_region:
                # Ensure scroll region is at least as large as canvas
                scroll_width = max(current_region[2], canvas_width + 100)
                scroll_height = max(current_region[3], canvas_height + 100)
                self.canvas.configure(scrollregion=(0, 0, scroll_width, scroll_height))
    
    def set_node_click_callback(self, callback: Callable[[str], None]):
        """Set callback for node clicks."""
        self.node_click_callback = callback
    
    def set_node_hover_callback(self, callback: Callable[[str], None]):
        """Set callback for node hover events."""
        self.node_hover_callback = callback
    
    def open_in_browser(self):
        """Open the SVG file in a web browser."""
        if self.open_browser_callback:
            self.open_browser_callback()
    
    def set_open_browser_callback(self, callback: Callable[[], None]):
        """Set callback for opening in browser."""
        self.open_browser_callback = callback 