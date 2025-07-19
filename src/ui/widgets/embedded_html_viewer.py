"""
Embedded HTML viewer that displays interactive family tree content directly within tkinter
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import os
import webbrowser
import tempfile
import json
from typing import Dict, Any, Optional
import threading
import time

# Try different embedded browser solutions
HAS_WEBVIEW = False
HAS_CEFPYTHON = False
HAS_TKHTML = False

try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    pass

try:
    from cefpython3 import cef
    HAS_CEFPYTHON = True
except ImportError:
    pass

try:
    import tkinter.html as tkhtml
    HAS_TKHTML = True
except ImportError:
    pass

class EmbeddedHTMLViewer(ctk.CTkFrame):
    """
    Embedded HTML viewer that displays family tree content directly within the application
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.html_file_path = None
        self.character_data = {}
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._setup_ui()
        self._determine_viewer_type()
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Header with title and controls
        self.header_frame = ctk.CTkFrame(self, height=50)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Interactive Family Tree",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        # Controls frame (only Open in Browser)
        self.controls_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.controls_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")

        # Open in browser button
        self.browser_btn = ctk.CTkButton(
            self.controls_frame, text="Open in Browser", width=120, height=30,
            command=self.open_in_browser
        )
        self.browser_btn.grid(row=0, column=0, padx=(10, 0))

        # Main content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
    
    def _determine_viewer_type(self):
        """Determine which type of viewer to use"""
        if HAS_WEBVIEW:
            print("DEBUG: Using webview for embedded HTML")
            self._setup_webview()
        else:
            print("DEBUG: pywebview not available, falling back to browser")
            self._setup_browser_fallback()

    def _setup_webview(self):
        """Setup webview-based viewer"""
        self.webview_frame = ctk.CTkFrame(self.content_frame)
        self.webview_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.webview_window = None
        self.status_label = ctk.CTkLabel(
            self.webview_frame,
            text="Loading embedded viewer...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(expand=True)

    def _setup_browser_fallback(self):
        self.browser_frame = ctk.CTkFrame(self.content_frame)
        self.browser_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        label = ctk.CTkLabel(
            self.browser_frame,
            text="pywebview not available. Opening in browser...",
            font=ctk.CTkFont(size=12)
        )
        label.pack(expand=True)

    def load_html_file(self, file_path: str):
        """Load HTML file and display in embedded webview or browser"""
        self.html_file_path = file_path
        if not os.path.exists(file_path):
            self._show_error("HTML file not found")
            print("[DEBUG] HTML file not found:", file_path)
            return
        if HAS_WEBVIEW:
            self._show_in_webview(file_path)
        else:
            self.open_in_browser()

    def _show_in_webview(self, file_path: str):
        import threading
        def run_webview():
            import webview
            try:
                parent_handle = self.webview_frame.winfo_id()
                print(f"[DEBUG] Attempting to embed webview in frame with handle: {parent_handle}")
                webview.create_window(
                    "Family Tree Viewer",
                    url=f"file://{os.path.abspath(file_path)}",
                    width=1200,
                    height=800,
                    resizable=True,
                    parent=parent_handle
                )
                webview.start()
            except Exception as e:
                print(f"[DEBUG] Embedding webview failed: {e}. (Fallbacks commented out for debugging)")
                # try:
                #     webview.create_window(
                #         "Family Tree Viewer",
                #         url=f"file://{os.path.abspath(file_path)}",
                #         width=1200,
                #         height=800,
                #         resizable=True
                #     )
                #     webview.start()
                # except Exception as e2:
                #     print(f"[DEBUG] Separate webview window failed: {e2}. Falling back to browser.")
                #     self.open_in_browser()
        threading.Thread(target=run_webview, daemon=True).start()
        if hasattr(self, 'status_label'):
            self.status_label.configure(text="Embedded viewer loaded.")

    def open_in_browser(self):
        """Open HTML file in external browser"""
        if self.html_file_path:
            webbrowser.open(f"file://{os.path.abspath(self.html_file_path)}")

    def _show_error(self, message: str):
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", f"❌ Error: {message}")
        print(f"EmbeddedHTMLViewer Error: {message}")

    def open_settings_dialog(self):
        """Open settings dialog with focus toggle"""
        dialog = tk.Toplevel(self)
        dialog.title("Viewer Settings")
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        dialog.grab_set()
        label = tk.Label(dialog, text="Auto-Focus on Roots/Selection:", font=("Arial", 12))
        label.pack(pady=(20, 5))
        toggle = tk.Checkbutton(dialog, text="Enable Auto-Focus", variable=self.focus_toggle_var, font=("Arial", 11))
        toggle.pack(pady=5)
        close_btn = tk.Button(dialog, text="Close", command=dialog.destroy)
        close_btn.pack(pady=10)

    def _get_focus_node_ids(self):
        """Determine which node(s) to focus on: roots for full tree, selected person for subtree"""
        # Heuristic: if only one person in character_data, focus on them
        if len(self.character_data) == 1:
            return list(self.character_data.keys())
        # If all persons have parent info, focus on selected person if any
        if hasattr(self, 'selected_element') and self.selected_element:
            return [self.selected_element]
        # Otherwise, focus on Generation 1 (roots)
        roots = []
        for pid, pdata in self.character_data.items():
            if not pdata.get('father_id') and not pdata.get('mother_id'):
                roots.append(pid)
        return roots if roots else None

    def _focus_on_nodes(self, node_ids):
        """Auto-fit and center the canvas view to the bounding box of the given node_ids"""
        # Find all polygons for these node_ids
        focus_points = []
        for item_id, info in self.svg_elements.items():
            if info.get('type') == 'polygon' and info.get('person_id') in node_ids:
                focus_points.extend(info['points'])
        if not focus_points:
            print(f"[DEBUG] _focus_on_nodes: No polygons found for node_ids {node_ids}")
            return
        min_x = min(focus_points[::2])
        max_x = max(focus_points[::2])
        min_y = min(focus_points[1::2])
        max_y = max(focus_points[1::2])
        print(f"[DEBUG] _focus_on_nodes: bbox x=({min_x},{max_x}), y=({min_y},{max_y}) for nodes {node_ids}")
        self._auto_fit_canvas(min_x, max_x, min_y, max_y) 