"""
Embedded web view widget for displaying HTML content within the tkinter application.
"""
import customtkinter as ctk
import tkinter as tk
from pathlib import Path
import os
import sys
import tempfile
import threading
from typing import Optional, Callable
import webbrowser
from urllib.parse import urljoin
from urllib.request import pathname2url

# Try to import webview library for embedded browser
try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False

# Try to import tkinter.html for basic HTML rendering
try:
    import tkinter.html as tkhtml
    HAS_TKHTML = True
except ImportError:
    HAS_TKHTML = False

class EmbeddedWebViewer(ctk.CTkFrame):
    """
    An embedded web viewer widget that can display HTML content within tkinter.
    Falls back to different methods based on available libraries.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.html_content = ""
        self.html_file_path = None
        self.webview_window = None
        self.webview_thread = None
        self.temp_files = []  # Track temporary files for cleanup
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Initialize the appropriate viewer
        self._init_viewer()
    
    def _init_viewer(self):
        """Initialize the appropriate web viewer based on available libraries"""
        
        if HAS_WEBVIEW:
            print("DEBUG: Using webview library for embedded browser")
            self._init_webview_viewer()
        else:
            print("DEBUG: webview library not available, using fallback iframe approach")
            self._init_fallback_viewer()
    
    def _init_webview_viewer(self):
        """Initialize webview-based embedded browser"""
        # Create container frame
        self.webview_frame = ctk.CTkFrame(self, corner_radius=0)
        self.webview_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Create toolbar
        self.toolbar = ctk.CTkFrame(self.webview_frame, height=40)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.toolbar.grid_columnconfigure(2, weight=1)
        
        # Add toolbar buttons
        self.refresh_btn = ctk.CTkButton(
            self.toolbar,
            text="Refresh",
            width=80,
            height=30,
            command=self.refresh
        )
        self.refresh_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.external_btn = ctk.CTkButton(
            self.toolbar,
            text="Open in Browser",
            width=120,
            height=30,
            command=self.open_in_external_browser
        )
        self.external_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.toolbar,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=3, padx=10, pady=5, sticky="e")
        
        # Create placeholder for webview
        self.webview_placeholder = ctk.CTkFrame(self.webview_frame)
        self.webview_placeholder.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.webview_frame.grid_rowconfigure(1, weight=1)
        
        # Add placeholder text
        self.placeholder_label = ctk.CTkLabel(
            self.webview_placeholder,
            text="Web content will appear here\nClick 'Load Content' to view the family tree",
            font=ctk.CTkFont(size=14)
        )
        self.placeholder_label.pack(expand=True)
    
    def _init_fallback_viewer(self):
        """Initialize fallback viewer without webview library"""
        # Create container frame
        self.fallback_frame = ctk.CTkFrame(self, corner_radius=0)
        self.fallback_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Create toolbar
        self.toolbar = ctk.CTkFrame(self.fallback_frame, height=40)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.toolbar.grid_columnconfigure(2, weight=1)
        
        # Add toolbar buttons
        self.open_btn = ctk.CTkButton(
            self.toolbar,
            text="Open in Browser",
            width=120,
            height=30,
            command=self.open_in_external_browser
        )
        self.open_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.refresh_btn = ctk.CTkButton(
            self.toolbar,
            text="Refresh File",
            width=100,
            height=30,
            command=self.refresh
        )
        self.refresh_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.toolbar,
            text="Ready - Click 'Open in Browser' to view",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=3, padx=10, pady=5, sticky="e")
        
        # Create info area
        self.info_frame = ctk.CTkFrame(self.fallback_frame)
        self.info_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.fallback_frame.grid_rowconfigure(1, weight=1)
        
        # Add info text
        self.info_text = ctk.CTkTextbox(
            self.info_frame,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.info_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.info_frame.grid_rowconfigure(0, weight=1)
        
        # Default text
        self.info_text.insert("1.0", 
            "Interactive Family Tree Viewer\n\n"
            "Your family tree has been generated with full interactivity!\n\n"
            "Features:\n"
            "• Click on any person to see their details\n"
            "• Search family members by name\n"
            "• Zoom and pan with mouse wheel and dragging\n"
            "• Modern web interface with smooth animations\n"
            "• Hover effects and tooltips\n\n"
            "Click 'Open in Browser' above to view the interactive family tree.\n\n"
            "The family tree is saved as an HTML file that you can:\n"
            "• Bookmark for easy access\n"
            "• Share with family members\n"
            "• View offline anytime\n"
            "• Print or export as needed"
        )
        self.info_text.configure(state="disabled")
    
    def load_html_file(self, file_path: str):
        """Load HTML file into the viewer"""
        self.html_file_path = file_path
        
        if not os.path.exists(file_path):
            self.status_label.configure(text="Error: File not found")
            return
        
        # Read HTML content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.html_content = f.read()
            
            if HAS_WEBVIEW:
                self._load_webview_content()
            else:
                self._update_fallback_info()
                
        except Exception as e:
            self.status_label.configure(text=f"Error loading file: {str(e)}")
    
    def _load_webview_content(self):
        """Load content into webview"""
        try:
            # Create webview window in a separate thread
            if self.webview_window is None:
                self.webview_thread = threading.Thread(target=self._create_webview_window)
                self.webview_thread.daemon = True
                self.webview_thread.start()
            else:
                # Update existing webview
                self.webview_window.load_url(f"file://{os.path.abspath(self.html_file_path)}")
            
            self.status_label.configure(text="Family tree loaded successfully")
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
    
    def _create_webview_window(self):
        """Create webview window in separate thread"""
        try:
            # Create webview window
            self.webview_window = webview.create_window(
                'Family Tree',
                f"file://{os.path.abspath(self.html_file_path)}",
                width=800,
                height=600,
                resizable=True,
                fullscreen=False,
                minimized=False,
                on_top=False
            )
            
            # Start webview (this blocks)
            webview.start(debug=False)
            
        except Exception as e:
            print(f"Error creating webview: {e}")
    
    def _update_fallback_info(self):
        """Update fallback viewer with file info"""
        if self.html_file_path:
            self.info_text.configure(state="normal")
            self.info_text.delete("1.0", "end")
            self.info_text.insert("1.0", 
                f"Interactive Family Tree Ready!\n\n"
                f"File: {os.path.basename(self.html_file_path)}\n"
                f"Location: {os.path.dirname(self.html_file_path)}\n"
                f"Size: {os.path.getsize(self.html_file_path)} bytes\n\n"
                f"Click 'Open in Browser' to view the interactive family tree.\n\n"
                f"Features Available:\n"
                f"• Click on any person to see their details\n"
                f"• Search family members by name\n"
                f"• Zoom and pan with mouse wheel and dragging\n"
                f"• Modern web interface with smooth animations\n"
                f"• Hover effects and tooltips\n\n"
                f"The family tree includes advanced interactions that work best in a web browser.\n\n"
                f"This HTML file can be:\n"
                f"• Bookmarked for easy access\n"
                f"• Shared with family members\n"
                f"• Viewed offline anytime\n"
                f"• Printed or exported as needed"
            )
            self.info_text.configure(state="disabled")
            self.status_label.configure(text="Ready - Click 'Open in Browser' to view")
    
    def open_in_external_browser(self):
        """Open the HTML file in external browser"""
        if self.html_file_path and os.path.exists(self.html_file_path):
            try:
                webbrowser.open(f"file://{os.path.abspath(self.html_file_path)}")
                self.status_label.configure(text="Opened in external browser")
            except Exception as e:
                self.status_label.configure(text=f"Error opening browser: {str(e)}")
        else:
            self.status_label.configure(text="No file to open")
    
    def refresh(self):
        """Refresh the current content"""
        if self.html_file_path:
            self.load_html_file(self.html_file_path)
        else:
            self.status_label.configure(text="No file to refresh")
    
    def load_html_content(self, content: str):
        """Load HTML content directly"""
        self.html_content = content
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        # Track temporary file for cleanup
        self.temp_files.append(temp_path)
        
        self.load_html_file(temp_path)
    
    def get_html_file_path(self) -> Optional[str]:
        """Get the current HTML file path"""
        return self.html_file_path
    
    def destroy(self):
        """Clean up resources"""
        # Clean up webview
        if self.webview_window:
            try:
                webview.destroy_window(self.webview_window)
            except:
                pass
        
        # Clean up temporary files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except OSError:
                pass  # File might already be deleted
        self.temp_files.clear()
        
        super().destroy()


class SimpleWebViewer(ctk.CTkFrame):
    """
    A simpler web viewer that focuses on opening content in external browser
    with a nice preview interface.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.html_file_path = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Create header
        self.header_frame = ctk.CTkFrame(self, height=60)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Interactive Family Tree",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        # Open button
        self.open_btn = ctk.CTkButton(
            self.header_frame,
            text="Open in Browser",
            width=140,
            height=40,
            command=self.open_in_browser,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.open_btn.grid(row=0, column=2, padx=15, pady=10)
        
        # Content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Info text
        self.info_text = ctk.CTkTextbox(
            self.content_frame,
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.info_text.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        # Default content
        self._show_default_content()
    
    def _show_default_content(self):
        """Show default content"""
        content = """🌳 Interactive Family Tree Viewer

Your family tree has been generated with full web-based interactivity!

✨ Features:
• Click on any person to see their detailed information
• Search family members by name in real-time
• Zoom and pan with mouse wheel and dragging
• Modern web interface with smooth animations
• Hover effects and helpful tooltips
• Responsive design that works on any screen size

🚀 How to Use:
1. Click "Open in Browser" above to view your family tree
2. Click on any person in the tree to see their details
3. Use the search box to quickly find family members
4. Zoom in/out with mouse wheel or toolbar buttons
5. Drag to pan around large family trees

💾 File Information:
• Your family tree is saved as an HTML file
• Works offline - no internet connection needed
• Can be shared with family members
• Bookmark the file for easy access
• Print or export as needed

🔧 Technical Details:
• Built with modern web technologies
• Responsive CSS design
• JavaScript-powered interactions
• SVG graphics for crisp rendering at any zoom level
• Works in any modern web browser

Click "Open in Browser" to explore your interactive family tree!"""
        
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", content)
        self.info_text.configure(state="disabled")
    
    def load_html_file(self, file_path: str):
        """Load HTML file"""
        self.html_file_path = file_path
        
        if not os.path.exists(file_path):
            self._show_error("File not found")
            return
        
        # Update content with file info
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            content = f"""🌳 Interactive Family Tree Ready!

File: {file_name}
Size: {file_size:,} bytes
Location: {os.path.dirname(file_path)}

✨ Your family tree includes:
• Click on any person to see their detailed information
• Search family members by name in real-time
• Zoom and pan with mouse wheel and dragging
• Modern web interface with smooth animations
• Hover effects and helpful tooltips

🚀 Ready to explore!
Click "Open in Browser" above to view your interactive family tree.

The family tree will open in your default web browser where you can:
• Navigate through generations with smooth animations
• Search for specific family members instantly
• View detailed information for each person
• Zoom in to see fine details or zoom out for the big picture
• Print or share the family tree easily

💡 Pro Tips:
• Bookmark the family tree page for easy access
• Use Ctrl+F in the browser to search for specific names
• The family tree works offline - no internet needed
• Share the HTML file with family members
• Right-click and "Save As" to create copies

Click "Open in Browser" to start exploring your family tree!"""
            
            self.info_text.configure(state="normal")
            self.info_text.delete("1.0", "end")
            self.info_text.insert("1.0", content)
            self.info_text.configure(state="disabled")
            
        except Exception as e:
            self._show_error(f"Error loading file: {str(e)}")
    
    def _show_error(self, message: str):
        """Show error message"""
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", f"❌ Error: {message}")
        self.info_text.configure(state="disabled")
    
    def open_in_browser(self):
        """Open HTML file in browser"""
        if self.html_file_path and os.path.exists(self.html_file_path):
            try:
                webbrowser.open(f"file://{os.path.abspath(self.html_file_path)}")
                
                # Update status
                self.info_text.configure(state="normal")
                current_content = self.info_text.get("1.0", "end")
                self.info_text.delete("1.0", "end")
                self.info_text.insert("1.0", "✅ Family tree opened in browser!\n\n" + current_content)
                self.info_text.configure(state="disabled")
                
            except Exception as e:
                self._show_error(f"Could not open browser: {str(e)}")
        else:
            self._show_error("No family tree file to open") 