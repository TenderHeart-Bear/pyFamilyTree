"""
Graph viewer widget for displaying family tree visualizations.
"""
import customtkinter as ctk
from PIL import Image, ImageTk
import io
import os
import traceback
import cairosvg
import tkinter as tk

class GraphViewer(ctk.CTkScrollableFrame):
    def __init__(self, master, image_path: str, **kwargs):
        print("\nDEBUG: Starting GraphViewer initialization")
        print(f"DEBUG: Master widget type: {type(master)}")
        print(f"DEBUG: Original image path: {image_path}")
        print(f"DEBUG: Additional kwargs: {kwargs}")
        
        # Initialize with default appearance
        super().__init__(
            master,
            width=800,
            height=600,
            corner_radius=0,
            border_width=0,
            **kwargs
        )
        print("DEBUG: Base class initialized")
        
        # Configure grid weights for proper expansion
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main container frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        print("DEBUG: Main frame created")
        
        # Create canvas for the image
        self.canvas = ctk.CTkCanvas(
            self.main_frame,
            highlightthickness=0,
            width=800,
            height=600,
            bg="white"
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        print("DEBUG: Canvas created and configured")
        
        # Create toolbar frame
        self.toolbar = ctk.CTkFrame(self.main_frame, height=40)
        self.toolbar.grid(row=1, column=0, sticky="ew", padx=0, pady=(5, 0))
        self.toolbar.grid_columnconfigure(3, weight=1)  # Make space expand
        
        # Add zoom controls
        self.zoom_out_btn = ctk.CTkButton(
            self.toolbar,
            text="Zoom Out",
            width=80,
            height=30,
            command=self.zoom_out
        )
        self.zoom_out_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.zoom_in_btn = ctk.CTkButton(
            self.toolbar,
            text="Zoom In",
            width=80,
            height=30,
            command=self.zoom_in
        )
        self.zoom_in_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.zoom_reset_btn = ctk.CTkButton(
            self.toolbar,
            text="Reset",
            width=80,
            height=30,
            command=self.zoom_reset
        )
        self.zoom_reset_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Add status label
        self.status_label = ctk.CTkLabel(
            self.toolbar,
            text="Loading...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=4, padx=10, pady=5, sticky="e")
        
        # Fix double extension if present
        if image_path.lower().endswith('.svg.svg'):
            image_path = image_path[:-4]  # Remove one .svg
            print(f"DEBUG: Fixed double extension, new path: {image_path}")
        
        # Store the path
        self.image_path = os.path.abspath(image_path)
        print(f"DEBUG: Final image path set to: {self.image_path}")
        
        # Store reference to PhotoImage to prevent garbage collection
        self.photo = None
        self.original_image = None
        
        # Initialize zoom and pan variables
        self.zoom_factor = 1.0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.is_panning = False
        
        # Initialize node interaction callbacks
        self.node_click_callback = None
        self.node_hover_callback = None
        
        # Bind mouse events for panning and zooming
        try:
            self.canvas.bind("<Button-1>", self.start_pan)
            self.canvas.bind("<B1-Motion>", self.do_pan)
            self.canvas.bind("<ButtonRelease-1>", self.end_pan)
            
            # Bind scroll wheel for zooming
            self.canvas.bind("<MouseWheel>", self.on_mousewheel)
            
            # Add keyboard shortcuts for zoom (when canvas has focus)
            self.canvas.bind("<Key-plus>", self.zoom_in)
            self.canvas.bind("<Key-equal>", self.zoom_in)  # + without shift
            self.canvas.bind("<Key-minus>", self.zoom_out)
            self.canvas.bind("<Key-0>", self.zoom_reset)
            self.canvas.bind("<Control-Key-0>", self.zoom_reset)
            
            # Make canvas focusable for keyboard events
            self.canvas.focus_set()
            
        except Exception as e:
            # print(f"DEBUG: Warning - could not bind mouse events: {e}")
            pass
        
        # Schedule image load
        self.after(100, self.load_image)
        # print("DEBUG: Image load scheduled")
        
        # Bind resize event
        # print("DEBUG: Resize event bound")
        try:
            self.bind('<Configure>', self.on_resize)
        except Exception as e:
            # print(f"DEBUG: Warning - could not bind resize event: {e}")
            pass
        
        # print("DEBUG: GraphViewer initialization complete")
    
    def load_image(self):
        """Load and display the image"""
        # print("\nDEBUG: Starting image load")
        try:
            if not self.image_path:
                self.show_error("No image path provided")
                return
            
            # print(f"DEBUG: Loading image from: {self.image_path}")
            # print(f"DEBUG: File size: {os.path.getsize(self.image_path)} bytes")
            
            # Check if file exists
            if not os.path.exists(self.image_path):
                self.show_error(f"Image file not found: {self.image_path}")
                return
            
            # Set PIL image size limits to prevent decompression bomb warnings
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = 200000000  # 200 million pixels limit
            
            # If it's an SVG, convert to PNG for better display
            if self.image_path.lower().endswith('.svg'):
                # print("DEBUG: Converting SVG to PNG")
                try:
                    import cairosvg
                    import io
                    
                    # Convert SVG to PNG bytes with size limits
                    png_bytes = cairosvg.svg2png(
                        url=self.image_path,
                        output_width=1920,  # Max width
                        output_height=1080   # Max height
                    )
                    
                    # Create PIL Image from PNG bytes
                    self.original_image = Image.open(io.BytesIO(png_bytes))
                    
                except ImportError:
                    # If cairosvg is not available, try to load as regular image
                    self.original_image = Image.open(self.image_path)
            else:
                self.original_image = Image.open(self.image_path)
            
            # print(f"DEBUG: Original image loaded, size: {self.original_image.size}, mode: {self.original_image.mode}")
            
            # Reset zoom and center the image
            self.zoom_reset()
            
        except Exception as e:
            error_msg = f"Error loading image: {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            self.show_error(error_msg)
    
    def calculate_fit_zoom(self):
        """Calculate zoom factor to fit image in window"""
        if not self.original_image:
            return
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # If canvas not properly sized yet, use default
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600
        
        # Calculate zoom factors for width and height
        zoom_x = canvas_width / self.original_image.width
        zoom_y = canvas_height / self.original_image.height
        
        # Use the smaller zoom factor to fit the entire image
        self.zoom_factor = min(zoom_x, zoom_y, 1.0)  # Don't zoom beyond original size
        
        # Ensure minimum zoom
        if self.zoom_factor < 0.1:
            self.zoom_factor = 0.1
    
    def display_image(self):
        """Display the scaled image on the canvas with proper zoom and pan support"""
        if not self.original_image:
            return
        
        try:
            # Calculate new dimensions
            new_width = int(self.original_image.width * self.zoom_factor)
            new_height = int(self.original_image.height * self.zoom_factor)
            
            # print(f"DEBUG: Scaling image to: {new_width}x{new_height} (factor: {self.zoom_factor:.2f})")
            
            # Scale the image
            scaled_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for tkinter
            self.photo = ImageTk.PhotoImage(scaled_image)
            
            # Clear canvas and display image with pan offsets
            self.canvas.delete("all")
            
            # Position image using pan offsets
            image_x = self.pan_offset_x
            image_y = self.pan_offset_y
            
            self.canvas.create_image(image_x, image_y, anchor=tk.NW, image=self.photo)
            
            # Update scroll region to include the entire image area
            # This allows for scrolling when the image is larger than the canvas
            scroll_x1 = min(0, image_x)
            scroll_y1 = min(0, image_y)
            scroll_x2 = max(self.canvas.winfo_width(), image_x + new_width)
            scroll_y2 = max(self.canvas.winfo_height(), image_y + new_height)
            
            self.canvas.configure(scrollregion=(scroll_x1, scroll_y1, scroll_x2, scroll_y2))
            
            # Update status
            self.status_label.configure(
                text=f"Zoom: {self.zoom_factor:.1f}x | Size: {new_width}x{new_height}"
            )
            
        except Exception as e:
            error_msg = f"Error displaying image: {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            self.show_error(error_msg)
    
    def zoom_in(self, event=None):
        """Zoom in by 20% around the center of the current view"""
        try:
            # Get canvas center for zoom focus
            canvas_center_x = self.canvas.winfo_width() / 2
            canvas_center_y = self.canvas.winfo_height() / 2
            
            # Calculate the point in the image that's currently at the center
            old_image_center_x = (canvas_center_x - self.pan_offset_x) / self.zoom_factor
            old_image_center_y = (canvas_center_y - self.pan_offset_y) / self.zoom_factor
            
            # Apply zoom
            self.zoom_factor *= 1.2
            
            # Calculate new pan offsets to keep the same point at the center
            new_image_center_x = old_image_center_x * self.zoom_factor
            new_image_center_y = old_image_center_y * self.zoom_factor
            
            self.pan_offset_x = canvas_center_x - new_image_center_x
            self.pan_offset_y = canvas_center_y - new_image_center_y
            
            self.display_image()
        except Exception as e:
            # print(f"DEBUG ERROR: Error zooming in: {e}")
            pass
    
    def zoom_out(self, event=None):
        """Zoom out by 20% around the center of the current view"""
        try:
            # Get canvas center for zoom focus
            canvas_center_x = self.canvas.winfo_width() / 2
            canvas_center_y = self.canvas.winfo_height() / 2
            
            # Calculate the point in the image that's currently at the center
            old_image_center_x = (canvas_center_x - self.pan_offset_x) / self.zoom_factor
            old_image_center_y = (canvas_center_y - self.pan_offset_y) / self.zoom_factor
            
            # Apply zoom with minimum limit
            new_zoom = self.zoom_factor / 1.2
            if new_zoom < 0.1:
                new_zoom = 0.1
            self.zoom_factor = new_zoom
            
            # Calculate new pan offsets to keep the same point at the center
            new_image_center_x = old_image_center_x * self.zoom_factor
            new_image_center_y = old_image_center_y * self.zoom_factor
            
            self.pan_offset_x = canvas_center_x - new_image_center_x
            self.pan_offset_y = canvas_center_y - new_image_center_y
            
            self.display_image()
        except Exception as e:
            # print(f"DEBUG ERROR: Error zooming out: {e}")
            pass
    
    def zoom_reset(self, event=None):
        """Reset zoom to fit image in window and center it"""
        try:
            # Calculate fit zoom
            self.calculate_fit_zoom()
            
            # Center the image
            if self.original_image:
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                if canvas_width <= 1:
                    canvas_width = 800
                if canvas_height <= 1:
                    canvas_height = 600
                
                image_width = self.original_image.width * self.zoom_factor
                image_height = self.original_image.height * self.zoom_factor
                
                # Center the image
                self.pan_offset_x = (canvas_width - image_width) / 2
                self.pan_offset_y = (canvas_height - image_height) / 2
            
            self.display_image()
        except Exception as e:
            # print(f"DEBUG ERROR: Error resetting zoom: {e}")
            pass
    
    def start_pan(self, event):
        """Start panning"""
        try:
            # Set focus for keyboard shortcuts
            self.canvas.focus_set()
            
            # First check if this is a node click
            if self._handle_click_for_nodes(event):
                return  # Node click handled, don't start panning
            
            # No node click, start panning
            self.is_panning = True
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.canvas.configure(cursor="hand2")
        except Exception as e:
            print(f"DEBUG ERROR: Error starting pan: {e}")
    
    def do_pan(self, event):
        """Handle panning"""
        try:
            if self.is_panning:
                dx = event.x - self.pan_start_x
                dy = event.y - self.pan_start_y
                self.pan_offset_x += dx
                self.pan_offset_y += dy
                self.pan_start_x = event.x
                self.pan_start_y = event.y
                self.display_image()
        except Exception as e:
            print(f"DEBUG ERROR: Error panning: {e}")
    
    def end_pan(self, event):
        """Stop panning"""
        try:
            self.is_panning = False
            self.canvas.configure(cursor="arrow")
        except Exception as e:
            print(f"DEBUG ERROR: Error stopping pan: {e}")
    
    def on_mousewheel(self, event):
        """Handle mouse wheel events - zoom around mouse position"""
        try:
            # Get mouse position
            mouse_x = event.x
            mouse_y = event.y
            
            # Calculate the point in the image that's currently under the mouse
            old_image_point_x = (mouse_x - self.pan_offset_x) / self.zoom_factor
            old_image_point_y = (mouse_y - self.pan_offset_y) / self.zoom_factor
            
            # Determine zoom direction
            zoom_in = False
            if hasattr(event, 'delta'):
                # Windows
                zoom_in = event.delta > 0
            elif hasattr(event, 'num'):
                # Linux
                zoom_in = event.num == 4
            
            # Apply zoom
            if zoom_in:
                self.zoom_factor *= 1.2
            else:
                new_zoom = self.zoom_factor / 1.2
                if new_zoom < 0.1:
                    new_zoom = 0.1
                self.zoom_factor = new_zoom
            
            # Calculate new pan offsets to keep the same point under the mouse
            new_image_point_x = old_image_point_x * self.zoom_factor
            new_image_point_y = old_image_point_y * self.zoom_factor
            
            self.pan_offset_x = mouse_x - new_image_point_x
            self.pan_offset_y = mouse_y - new_image_point_y
            
            self.display_image()
            
        except Exception as e:
            print(f"DEBUG ERROR: Error handling mouse wheel: {e}")
    
    def on_resize(self, event):
        """Handle window resize events"""
        try:
            if event.widget == self:
                # print(f"DEBUG: Resize event: {event.width}x{event.height}")
                # Trigger a display update after resize
                self.after(100, self.display_image)
        except Exception as e:
            # print(f"DEBUG: Error in resize handler: {e}")
            pass
    
    def set_node_click_callback(self, callback):
        """Set a callback function for node clicks"""
        self.node_click_callback = callback
    
    def set_node_hover_callback(self, callback):
        """Set a callback function for node hover events"""
        self.node_hover_callback = callback
    
    def show_error(self, message: str):
        """Show error message on the canvas"""
        try:
            # Clear canvas and display error
            self.canvas.delete("all")
            self.canvas.create_text(
                400, 300,  # Center of default canvas
                text=message,
                fill="red",
                justify="center",
                font=("Arial", 12)
            )
        except Exception:
            # Fallback to print if canvas operations fail
            print(f"Graph Viewer Error: {message}")
    
    def _get_node_at_position(self, x, y):
        """
        Get the node ID at the given canvas coordinates.
        This is a simplified implementation that would need to be enhanced
        for proper SVG coordinate mapping.
        """
        try:
            # For now, return a placeholder - in a real implementation,
            # this would parse the SVG file and map coordinates to node IDs
            # This is where you'd implement the actual node detection logic
            
            # Convert canvas coordinates to image coordinates
            if self.original_image:
                # Account for zoom and pan
                image_x = (x - self.pan_offset_x) / self.zoom_factor
                image_y = (y - self.pan_offset_y) / self.zoom_factor
                
                # TODO: Implement actual SVG parsing and node boundary detection
                # For now, return None to indicate no node found
                return None
            
            return None
        except Exception as e:
            print(f"DEBUG: Error getting node at position: {e}")
            return None
    
    def _handle_click_for_nodes(self, event):
        """Handle click events for node selection"""
        try:
            # Check if we have a node click callback
            if self.node_click_callback:
                # Get node at click position
                node_id = self._get_node_at_position(event.x, event.y)
                if node_id:
                    # Call the callback with the node ID
                    self.node_click_callback(node_id)
                    return True  # Indicate that we handled the click
            
            return False  # Click not handled by node selection
        except Exception as e:
            print(f"DEBUG: Error handling node click: {e}")
            return False 