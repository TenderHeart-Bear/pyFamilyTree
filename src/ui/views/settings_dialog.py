"""
Dialog for configuring application settings.
"""
import customtkinter as ctk
from typing import Optional, Dict, Any

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configure window
        self.title("Settings")
        self.geometry("400x400")
        self.resizable(False, False)
        
        # Initialize result
        self.result: Optional[Dict[str, Any]] = None
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Appearance settings
        self.appearance_label = ctk.CTkLabel(
            self.main_frame,
            text="Appearance",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.appearance_label.pack(pady=(0, 10))
        
        # Theme mode
        self.theme_frame = ctk.CTkFrame(self.main_frame)
        self.theme_frame.pack(fill="x", pady=10)
        
        self.theme_label = ctk.CTkLabel(
            self.theme_frame,
            text="Theme Mode:"
        )
        self.theme_label.pack(side="left", padx=10)
        
        self.theme_var = ctk.StringVar(value="system")
        self.theme_menu = ctk.CTkOptionMenu(
            self.theme_frame,
            values=["Light", "Dark", "System"],
            variable=self.theme_var
        )
        self.theme_menu.pack(side="right", padx=10)
        
        # Export settings
        self.export_label = ctk.CTkLabel(
            self.main_frame,
            text="Export Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.export_label.pack(pady=(20, 10))
        
        # Auto export
        self.auto_export_var = ctk.BooleanVar(value=False)
        self.auto_export_check = ctk.CTkCheckBox(
            self.main_frame,
            text="Auto-export visualizations",
            variable=self.auto_export_var
        )
        self.auto_export_check.pack(pady=5)
        
        # Export format
        self.format_frame = ctk.CTkFrame(self.main_frame)
        self.format_frame.pack(fill="x", pady=10)
        
        self.format_label = ctk.CTkLabel(
            self.format_frame,
            text="Export Format:"
        )
        self.format_label.pack(side="left", padx=10)
        
        self.format_var = ctk.StringVar(value="svg")
        self.format_menu = ctk.CTkOptionMenu(
            self.format_frame,
            values=["SVG", "PNG", "Both"],
            variable=self.format_var
        )
        self.format_menu.pack(side="right", padx=10)
        
        # Graph settings
        self.graph_label = ctk.CTkLabel(
            self.main_frame,
            text="Graph Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.graph_label.pack(pady=(20, 10))
        
        # Default generations
        self.generations_frame = ctk.CTkFrame(self.main_frame)
        self.generations_frame.pack(fill="x", pady=10)
        
        self.generations_label = ctk.CTkLabel(
            self.generations_frame,
            text="Default Generations:"
        )
        self.generations_label.pack(side="left", padx=10)
        
        self.generations_var = ctk.StringVar(value="2")
        self.generations_entry = ctk.CTkEntry(
            self.generations_frame,
            width=50,
            textvariable=self.generations_var
        )
        self.generations_entry.pack(side="right", padx=10)
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", pady=(20, 0))
        
        self.cancel_button = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            command=self.cancel
        )
        self.cancel_button.pack(side="left", padx=10, expand=True)
        
        self.confirm_button = ctk.CTkButton(
            self.button_frame,
            text="Confirm",
            command=self.confirm
        )
        self.confirm_button.pack(side="right", padx=10, expand=True)
        
        # Make dialog modal
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.transient(parent)
    
    def cancel(self):
        """Cancel dialog"""
        self.result = None
        self.destroy()
    
    def confirm(self):
        """Confirm and save settings"""
        try:
            # Validate generations
            try:
                generations = int(self.generations_var.get())
                if generations < 0:
                    raise ValueError("Generations cannot be negative")
            except ValueError:
                raise ValueError("Default generations must be a valid number")
            
            # Save settings
            self.result = {
                'appearance': {
                    'theme': self.theme_var.get().lower()
                },
                'export': {
                    'auto_export': self.auto_export_var.get(),
                    'format': self.format_var.get().lower()
                },
                'graph': {
                    'default_generations': generations
                }
            }
            
            self.destroy()
            
        except Exception as e:
            # Show error in a dialog
            error_dialog = ctk.CTkInputDialog(
                text=str(e),
                title="Error"
            )
            error_dialog.destroy()  # Just show the message
    
    def get_settings(self) -> Optional[Dict[str, Any]]:
        """Get the dialog settings"""
        self.wait_window()
        return self.result 