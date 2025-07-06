"""
Dialog for configuring family tree visualization parameters.
"""
import customtkinter as ctk
from typing import Optional, Dict, Any

class VisualizationDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configure window
        self.title("Visualization Settings")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Initialize result
        self.result: Optional[Dict[str, Any]] = None
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Mode selection
        self.mode_label = ctk.CTkLabel(
            self.main_frame,
            text="Visualization Mode",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.mode_label.pack(pady=(0, 10))
        
        self.mode_var = ctk.StringVar(value="specific")
        
        self.specific_radio = ctk.CTkRadioButton(
            self.main_frame,
            text="Specific View",
            variable=self.mode_var,
            value="specific",
            command=self._toggle_inputs
        )
        self.specific_radio.pack(pady=5)
        
        self.complete_radio = ctk.CTkRadioButton(
            self.main_frame,
            text="Complete Tree",
            variable=self.mode_var,
            value="complete",
            command=self._toggle_inputs
        )
        self.complete_radio.pack(pady=5)
        
        # Specific view parameters
        self.params_frame = ctk.CTkFrame(self.main_frame)
        self.params_frame.pack(fill="x", pady=20)
        
        # Start person
        self.start_label = ctk.CTkLabel(
            self.params_frame,
            text="Start Person (leave empty for root):"
        )
        self.start_label.pack(pady=(10, 5))
        
        self.start_entry = ctk.CTkEntry(self.params_frame)
        self.start_entry.pack(fill="x", padx=20)
        
        # Generations back
        self.back_label = ctk.CTkLabel(
            self.params_frame,
            text="Generations Back:"
        )
        self.back_label.pack(pady=(10, 5))
        
        self.back_var = ctk.StringVar(value="2")
        self.back_entry = ctk.CTkEntry(
            self.params_frame,
            textvariable=self.back_var
        )
        self.back_entry.pack(fill="x", padx=20)
        
        # Generations forward
        self.forward_label = ctk.CTkLabel(
            self.params_frame,
            text="Generations Forward:"
        )
        self.forward_label.pack(pady=(10, 5))
        
        self.forward_var = ctk.StringVar(value="2")
        self.forward_entry = ctk.CTkEntry(
            self.params_frame,
            textvariable=self.forward_var
        )
        self.forward_entry.pack(fill="x", padx=20)
        
        # Style selection
        self.style_label = ctk.CTkLabel(
            self.main_frame,
            text="Visual Style",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.style_label.pack(pady=(20, 10))
        
        self.style_var = ctk.StringVar(value="1")
        
        self.classic_radio = ctk.CTkRadioButton(
            self.main_frame,
            text="Classic",
            variable=self.style_var,
            value="1"
        )
        self.classic_radio.pack(pady=5)
        
        self.modern_radio = ctk.CTkRadioButton(
            self.main_frame,
            text="Modern",
            variable=self.style_var,
            value="2"
        )
        self.modern_radio.pack(pady=5)
        
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
        
        # Initial toggle
        self._toggle_inputs()
    
    def _toggle_inputs(self):
        """Toggle input fields based on mode"""
        if self.mode_var.get() == "specific":
            for widget in self.params_frame.winfo_children():
                widget.configure(state="normal")
        else:
            for widget in self.params_frame.winfo_children():
                widget.configure(state="disabled")
    
    def cancel(self):
        """Cancel dialog"""
        self.result = None
        self.destroy()
    
    def confirm(self):
        """Confirm and save parameters"""
        try:
            # Get mode
            is_complete = self.mode_var.get() == "complete"
            
            if is_complete:
                # Complete tree mode
                self.result = {
                    'generate_all': True,
                    'start_person': '',
                    'generations_back': 0,
                    'generations_forward': 0,
                    'style': self.style_var.get()
                }
            else:
                # Specific view mode
                try:
                    generations_back = int(self.back_var.get())
                    generations_forward = int(self.forward_var.get())
                except ValueError:
                    raise ValueError("Generations must be valid numbers")
                
                if generations_back < 0 or generations_forward < 0:
                    raise ValueError("Generations cannot be negative")
                
                self.result = {
                    'generate_all': False,
                    'start_person': self.start_entry.get().strip(),
                    'generations_back': generations_back,
                    'generations_forward': generations_forward,
                    'style': self.style_var.get()
                }
            
            self.destroy()
            
        except Exception as e:
            # Show error in a dialog
            error_dialog = ctk.CTkInputDialog(
                text=str(e),
                title="Error"
            )
            error_dialog.destroy()  # Just show the message
    
    def get_parameters(self) -> Optional[Dict[str, Any]]:
        """Get the dialog parameters"""
        self.wait_window()
        return self.result 