"""
Modern Windows GUI Module for ViGCA

Provides a modern graphical user interface specifically designed
for Windows 11, using customtkinter for a sleek appearance.
"""
import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk

from vigca.screen_capture import ScreenCapture
from vigca.feature_extraction import FeatureExtractor
from vigca.target_manager import TargetManager
from vigca.cursor_control import CursorController
from vigca.configuration import Configuration

import logging
logger = logging.getLogger(__name__)

# Configure customtkinter appearance
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class ModernTooltip:
    """Modern tooltip for the UI."""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Show the tooltip."""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = ctk.CTkToplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(self.tooltip, text=self.text, corner_radius=8, 
                             fg_color=("gray75", "gray25"), text_color=("gray10", "gray90"),
                             padx=10, pady=5)
        label.pack()
    
    def hide_tooltip(self, event=None):
        """Hide the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class ScrollableTargetFrame(ctk.CTkScrollableFrame):
    """Scrollable frame for displaying targets."""
    
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.target_rows = []
    
    def add_target(self, target_id, target_name, is_active=False):
        """Add a target to the list."""
        row_frame = ctk.CTkFrame(self)
        row_frame.pack(fill="x", padx=5, pady=2, expand=True)
        
        # Store target_id in the frame
        row_frame.target_id = target_id
        
        # Active indicator
        active_var = tk.BooleanVar(value=is_active)
        active_cb = ctk.CTkCheckBox(row_frame, text="", variable=active_var, width=20, 
                                     command=lambda: self.command("toggle_active", target_id, active_var.get()))
        active_cb.pack(side="left", padx=5)
        
        # Target name
        name_label = ctk.CTkLabel(row_frame, text=target_name, anchor="w")
        name_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # Action buttons
        btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)
        
        rename_btn = ctk.CTkButton(btn_frame, text="✏️", width=30, height=24, 
                                   command=lambda: self.command("rename", target_id))
        rename_btn.pack(side="left", padx=2)
        ModernTooltip(rename_btn, "Rename target")
        
        delete_btn = ctk.CTkButton(btn_frame, text="🗑️", width=30, height=24, fg_color="#d32f2f",
                                  command=lambda: self.command("delete", target_id))
        delete_btn.pack(side="left", padx=2)
        ModernTooltip(delete_btn, "Delete target")
        
        self.target_rows.append((target_id, row_frame))
    
    def clear_targets(self):
        """Clear all targets from the list."""
        for _, row_frame in self.target_rows:
            row_frame.destroy()
        self.target_rows = []
    
    def get_target_row(self, target_id):
        """Get a target row by ID."""
        for tid, row_frame in self.target_rows:
            if tid == target_id:
                return row_frame
        return None

class WindowsVigcaGUI(ctk.CTkFrame):
    """
    Modern Windows GUI for Vision-Guided Cursor Automation.
    """
    
    def __init__(self, parent):
        """
        Initialize the GUI.
        
        Args:
            parent (ctk.CTk): Parent window
        """
        super().__init__(parent)
        self.parent = parent
        
        # Initialize the modules
        self.config = Configuration()
        self.screen_capture = ScreenCapture(
            capture_rate=float(self.config.get("screen_capture", "capture_rate") or 1.0),
            roi=self.config.get("screen_capture", "use_roi") and self.config.get("screen_capture", "roi") or None
        )
        self.feature_extractor = FeatureExtractor(
            method=str(self.config.get("feature_extraction", "method") or "template_matching")
        )
        self.feature_extractor.set_threshold(float(self.config.get("feature_extraction", "threshold") or 0.8))
        self.target_manager = TargetManager()
        self.cursor_controller = CursorController(
            speed=float(self.config.get("cursor_control", "speed") or 5.0),
            smooth=bool(self.config.get("cursor_control", "smooth") or True)
        )
        
        # State variables
        self.running = False
        self.training_mode = False
        self.selection_box = None
        self.active_targets = []
        
        # Set up the application state
        active_ids = self.config.get("application", "active_target_ids")
        if active_ids:
            for target_id in active_ids:
                target = self.target_manager.get_target(target_id)
                if target:
                    self.active_targets.append(target_id)
        
        # Set up the UI
        self.create_widgets()
        self.layout_widgets()
        
        # Start the display loop
        self.after(100, self.update_display)
        
        logger.debug("Windows GUI initialized")
    
    def create_widgets(self):
        """Create all the widgets for the UI."""
        # Create main frames
        self.main_frame = ctk.CTkFrame(self)
        
        self.control_frame = ctk.CTkFrame(self.main_frame)
        self.display_frame = ctk.CTkFrame(self.main_frame)
        self.right_panel = ctk.CTkFrame(self.main_frame)
        
        # Create the tabview for the right panel
        self.right_tabview = ctk.CTkTabview(self.right_panel)
        self.target_tab = self.right_tabview.add("Targets")
        self.config_tab = self.right_tabview.add("Settings")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", 
                                       fg_color=("gray90", "gray20"), corner_radius=0)
        
        # Create control widgets
        self.control_buttons_frame = ctk.CTkFrame(self.control_frame)
        
        self.run_button = ctk.CTkButton(
            self.control_buttons_frame, 
            text="Start Detection", 
            fg_color="#4caf50", 
            hover_color="#388e3c",
            command=self.toggle_detection
        )
        
        self.train_button = ctk.CTkButton(
            self.control_buttons_frame, 
            text="Start Training", 
            fg_color="#2196f3", 
            hover_color="#1976d2",
            command=self.toggle_training
        )
        
        self.capture_button = ctk.CTkButton(
            self.control_buttons_frame, 
            text="Capture Screen", 
            command=self.capture_screen
        )
        
        # Create display widgets
        self.display_canvas = tk.Canvas(
            self.display_frame, 
            bg="#1e1e1e", 
            width=800, 
            height=600,
            highlightthickness=0
        )
        self.display_canvas.bind("<Button-1>", self.on_canvas_click)
        self.display_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.display_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Create target widgets
        self.target_control_frame = ctk.CTkFrame(self.target_tab)
        self.add_target_button = ctk.CTkButton(
            self.target_control_frame, 
            text="Add Target", 
            command=self.add_target
        )
        
        self.target_list_frame = ctk.CTkFrame(self.target_tab)
        self.target_list = ScrollableTargetFrame(
            self.target_list_frame,
            command=self.handle_target_action,
            width=300,
            height=400
        )
        
        # Create configuration widgets (in a tabview)
        self.config_tabview = ctk.CTkTabview(self.config_tab)
        self.screen_tab = self.config_tabview.add("Screen Capture")
        self.detection_tab = self.config_tabview.add("Detection")
        self.cursor_tab = self.config_tabview.add("Cursor")
        
        # Screen capture config
        self.capture_rate_label = ctk.CTkLabel(
            self.screen_tab, 
            text="Capture Rate (FPS):"
        )
        self.capture_rate_var = tk.DoubleVar(value=self.config.get("screen_capture", "capture_rate") or 1.0)
        self.capture_rate_slider = ctk.CTkSlider(
            self.screen_tab, 
            from_=0.1, 
            to=10.0, 
            variable=self.capture_rate_var,
            number_of_steps=99,
            command=self.on_capture_rate_change
        )
        self.capture_rate_value = ctk.CTkLabel(
            self.screen_tab, 
            text=f"{self.capture_rate_var.get():.1f}"
        )
        
        self.use_roi_var = tk.BooleanVar(value=self.config.get("screen_capture", "use_roi") or False)
        self.use_roi_check = ctk.CTkCheckBox(
            self.screen_tab, 
            text="Use Region of Interest", 
            variable=self.use_roi_var, 
            command=self.on_use_roi_change
        )
        
        # ROI settings
        self.roi_frame = ctk.CTkFrame(self.screen_tab)
        roi_config = self.config.get("screen_capture", "roi") or [0, 0, 800, 600]
        
        self.roi_x_label = ctk.CTkLabel(self.roi_frame, text="X:")
        self.roi_x_var = tk.IntVar(value=roi_config[0])
        self.roi_x_entry = ctk.CTkEntry(self.roi_frame, textvariable=self.roi_x_var, width=60)
        
        self.roi_y_label = ctk.CTkLabel(self.roi_frame, text="Y:")
        self.roi_y_var = tk.IntVar(value=roi_config[1])
        self.roi_y_entry = ctk.CTkEntry(self.roi_frame, textvariable=self.roi_y_var, width=60)
        
        self.roi_width_label = ctk.CTkLabel(self.roi_frame, text="Width:")
        self.roi_width_var = tk.IntVar(value=roi_config[2])
        self.roi_width_entry = ctk.CTkEntry(self.roi_frame, textvariable=self.roi_width_var, width=60)
        
        self.roi_height_label = ctk.CTkLabel(self.roi_frame, text="Height:")
        self.roi_height_var = tk.IntVar(value=roi_config[3])
        self.roi_height_entry = ctk.CTkEntry(self.roi_frame, textvariable=self.roi_height_var, width=60)
        
        self.roi_apply_button = ctk.CTkButton(
            self.roi_frame, 
            text="Apply ROI", 
            command=self.apply_roi
        )
        
        # Feature extraction config
        self.method_label = ctk.CTkLabel(
            self.detection_tab, 
            text="Detection Method:"
        )
        
        self.method_var = tk.StringVar(value=self.config.get("feature_extraction", "method") or "template_matching")
        methods = [(name, desc) for name, desc in FeatureExtractor.METHODS.items()]
        
        method_options = [m[0] for m in methods]
        method_descriptions = {m[0]: m[1] for m in methods}
        
        self.method_option_menu = ctk.CTkOptionMenu(
            self.detection_tab,
            values=method_options,
            variable=self.method_var,
            command=self.on_method_change
        )
        
        self.threshold_label = ctk.CTkLabel(
            self.detection_tab, 
            text="Confidence Threshold:"
        )
        
        self.threshold_var = tk.DoubleVar(value=self.config.get("feature_extraction", "threshold") or 0.8)
        self.threshold_slider = ctk.CTkSlider(
            self.detection_tab, 
            from_=0.1, 
            to=1.0, 
            variable=self.threshold_var,
            number_of_steps=90,
            command=self.on_threshold_change
        )
        
        self.threshold_value = ctk.CTkLabel(
            self.detection_tab, 
            text=f"{self.threshold_var.get():.2f}"
        )
        
        # Cursor control config
        self.speed_label = ctk.CTkLabel(
            self.cursor_tab, 
            text="Cursor Speed:"
        )
        
        self.speed_var = tk.DoubleVar(value=self.config.get("cursor_control", "speed") or 5.0)
        self.speed_slider = ctk.CTkSlider(
            self.cursor_tab, 
            from_=1.0, 
            to=10.0, 
            variable=self.speed_var,
            number_of_steps=90,
            command=self.on_speed_change
        )
        
        self.speed_value = ctk.CTkLabel(
            self.cursor_tab, 
            text=f"{self.speed_var.get():.1f}"
        )
        
        self.smooth_var = tk.BooleanVar(value=self.config.get("cursor_control", "smooth") or True)
        self.smooth_check = ctk.CTkCheckBox(
            self.cursor_tab, 
            text="Smooth Movement", 
            variable=self.smooth_var, 
            command=self.on_smooth_change
        )
        
        # Update target list
        self.update_target_list()
    
    def layout_widgets(self):
        """Arrange all widgets in the UI."""
        # Main layout
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.status_bar.pack(fill="x", side="bottom")
        
        # Layout main sections
        self.control_frame.pack(fill="x", padx=5, pady=5)
        
        # Split the main area into display and right panel
        self.display_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.right_panel.pack(side="right", fill="y", padx=5, pady=5)
        
        # Layout control buttons
        self.control_buttons_frame.pack(pady=5)
        self.run_button.pack(side="left", padx=5)
        self.train_button.pack(side="left", padx=5)
        self.capture_button.pack(side="left", padx=5)
        
        # Layout display canvas
        self.display_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Layout right panel
        self.right_tabview.pack(fill="both", expand=True)
        
        # Target tab layout
        self.target_control_frame.pack(fill="x", padx=5, pady=5)
        self.add_target_button.pack(side="left", padx=5, pady=5)
        
        self.target_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.target_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Config tab layout
        self.config_tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Screen capture config layout
        self.capture_rate_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.capture_rate_slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.capture_rate_value.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        self.use_roi_check.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="w")
        
        self.roi_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.roi_x_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.roi_x_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self.roi_y_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.roi_y_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        self.roi_width_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.roi_width_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        self.roi_height_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.roi_height_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        self.roi_apply_button.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        
        # Feature extraction config layout
        self.method_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.method_option_menu.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.threshold_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.threshold_slider.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.threshold_value.grid(row=1, column=2, padx=10, pady=10, sticky="e")
        
        # Cursor control config layout
        self.speed_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.speed_slider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.speed_value.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        self.smooth_check.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="w")
        
        # Set grid weights
        for tab in [self.screen_tab, self.detection_tab, self.cursor_tab]:
            tab.grid_columnconfigure(1, weight=1)
        
        # Enable/disable ROI widgets based on checkbox state
        self.on_use_roi_change()
    
    def update_display(self):
        """Update the display canvas with the current screen capture."""
        # Capture the screen
        frame = self.screen_capture.capture()
        
        if frame is not None:
            # Resize frame to fit the canvas
            canvas_width = self.display_canvas.winfo_width()
            canvas_height = self.display_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:  # Ensure valid dimensions
                # Calculate aspect ratio and resize while preserving ratio
                frame_h, frame_w = frame.shape[:2]
                aspect = frame_w / frame_h
                
                if canvas_width / canvas_height > aspect:
                    # Canvas is wider than frame
                    target_height = canvas_height
                    target_width = int(aspect * target_height)
                else:
                    # Canvas is taller than frame
                    target_width = canvas_width
                    target_height = int(target_width / aspect)
                
                # Resize the frame
                display_frame = cv2.resize(frame, (target_width, target_height))
                
                # If we're in detection mode, find active targets
                if self.running and not self.training_mode:
                    matches = {}
                    
                    for target_id in self.active_targets:
                        target = self.target_manager.get_target(target_id)
                        if target and target.features_method == self.feature_extractor.method:
                            target_matches = self.feature_extractor.find_matches(target.features, frame)
                            if target_matches:
                                matches[target_id] = target_matches
                                # Update detection stats
                                self.target_manager.update_target_detection(target_id)
                    
                    # Process the best match
                    if matches:
                        # Find the best match across all targets (highest confidence)
                        best_target_id = None
                        best_match = None
                        best_confidence = 0.0
                        
                        for target_id, target_matches in matches.items():
                            for match in target_matches:
                                x, y, w, h, confidence = match
                                if confidence > best_confidence:
                                    best_confidence = confidence
                                    best_match = match
                                    best_target_id = target_id
                        
                        if best_match:
                            # Move cursor to the best match
                            self.cursor_controller.move_to_target(best_match)
                            
                            # Draw best match with thick outline
                            x, y, w, h, _ = best_match
                            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                            
                            # Update status
                            target_name = self.target_manager.get_target(best_target_id).name
                            self.status_var.set(f"Detected {target_name} with confidence {best_confidence:.2f}")
                
                # Draw selection box if in training mode
                if self.training_mode and self.selection_box:
                    x1, y1, x2, y2 = self.selection_box
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 120, 255), 2)
                
                # Convert to PhotoImage and update canvas
                img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                img_tk = ImageTk.PhotoImage(image=img)
                
                # Update canvas
                self.display_canvas.config(width=target_width, height=target_height)
                self.display_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
                self.display_canvas.image = img_tk  # Keep reference to prevent garbage collection
        
        # Schedule next update
        self.after(50, self.update_display)
    
    def toggle_detection(self):
        """Start or stop the detection process."""
        self.running = not self.running
        
        if self.running:
            self.run_button.configure(text="Stop Detection", fg_color="#d32f2f", hover_color="#b71c1c")
            self.train_button.configure(state="disabled")
            self.status_var.set("Detection active")
            
            # Save active targets to config
            self.config.set("application", "active_target_ids", self.active_targets)
            self.config.save_config()
        else:
            self.run_button.configure(text="Start Detection", fg_color="#4caf50", hover_color="#388e3c")
            self.train_button.configure(state="normal")
            self.status_var.set("Detection stopped")
    
    def toggle_training(self):
        """Start or stop the training mode."""
        self.training_mode = not self.training_mode
        
        if self.training_mode:
            self.train_button.configure(text="Stop Training", fg_color="#d32f2f", hover_color="#b71c1c")
            self.run_button.configure(state="disabled")
            self.selection_box = None
            self.status_var.set("Training mode: Select targets on screen")
        else:
            self.train_button.configure(text="Start Training", fg_color="#2196f3", hover_color="#1976d2")
            self.run_button.configure(state="normal")
            self.selection_box = None
            self.status_var.set("Training mode stopped")
    
    def capture_screen(self):
        """Capture the current screen."""
        frame = self.screen_capture.capture(force=True)
        if frame is not None:
            self.status_var.set("Screen captured")
        else:
            self.status_var.set("Screen capture failed")
    
    def update_target_list(self):
        """Update the target listbox with current targets."""
        # Clear the listbox
        self.target_list.clear_targets()
        
        # Add all targets
        targets = self.target_manager.get_all_targets()
        for target_id, target in targets.items():
            is_active = target_id in self.active_targets
            self.target_list.add_target(target_id, target.name, is_active)
    
    def handle_target_action(self, action, target_id, *args):
        """Handle target list actions."""
        if action == "toggle_active":
            is_active = args[0]
            if is_active and target_id not in self.active_targets:
                self.active_targets.append(target_id)
                self.status_var.set(f"Target activated")
            elif not is_active and target_id in self.active_targets:
                self.active_targets.remove(target_id)
                self.status_var.set(f"Target deactivated")
        
        elif action == "rename":
            self.rename_target(target_id)
        
        elif action == "delete":
            self.remove_target(target_id)
    
    def add_target(self):
        """Add a new target based on the current selection box."""
        if not self.training_mode and not self.selection_box:
            messagebox.showwarning("Add Target", "Please enter training mode and select a region first.")
            return
        
        # Use current selection box
        sel_box = self.selection_box
        if not sel_box:
            messagebox.showwarning("Add Target", "Please select a region on the screen first.")
            return
        
        # Get the current frame
        frame = self.screen_capture.get_last_frame()
        if frame is None:
            messagebox.showwarning("Add Target", "Please capture a screen first.")
            return
        
        # Calculate the bounding box in the full frame
        x1, y1, x2, y2 = sel_box
        x = min(x1, x2)
        y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Extract the region from the frame
        region = frame[y:y+height, x:x+width]
        
        # Get name from user
        dialog = ctk.CTkInputDialog(text="Enter a name for this target:", title="Target Name")
        name = dialog.get_input()
        
        if not name:
            return  # User cancelled
        
        # Extract features using the current method
        features = self.feature_extractor.extract_features(region)
        
        # Add the target
        target_id = self.target_manager.add_target(
            name=name,
            features=features,
            features_method=self.feature_extractor.method,
            bounding_box=(x, y, width, height),
            image=region
        )
        
        # Activate the new target
        self.active_targets.append(target_id)
        
        # Update the list
        self.update_target_list()
        self.status_var.set(f"Added new target: {name}")
        
        # Clear selection box
        self.selection_box = None
    
    def remove_target(self, target_id):
        """Remove the selected target."""
        target = self.target_manager.get_target(target_id)
        if not target:
            return
        
        target_name = target.name
        
        # Confirm with user
        if messagebox.askyesno("Remove Target", f"Are you sure you want to remove the target '{target_name}'?"):
            # Remove from active targets if it's there
            if target_id in self.active_targets:
                self.active_targets.remove(target_id)
            
            # Remove the target
            success = self.target_manager.remove_target(target_id)
            if success:
                self.update_target_list()
                self.status_var.set(f"Removed target: {target_name}")
    
    def rename_target(self, target_id):
        """Rename the selected target."""
        target = self.target_manager.get_target(target_id)
        if not target:
            return
        
        # Get new name from user
        dialog = ctk.CTkInputDialog(
            text="Enter a new name for this target:", 
            title="Rename Target",
            default_value=target.name
        )
        new_name = dialog.get_input()
        
        if new_name:
            success = self.target_manager.rename_target(target_id, new_name)
            if success:
                self.update_target_list()
                self.status_var.set(f"Renamed target to: {new_name}")
    
    def on_canvas_click(self, event):
        """Handle mouse click on the canvas."""
        if self.training_mode:
            # Start selection box
            self.selection_box = [event.x, event.y, event.x, event.y]
    
    def on_canvas_drag(self, event):
        """Handle mouse drag on the canvas."""
        if self.training_mode and self.selection_box:
            # Update end coordinates
            self.selection_box[2] = event.x
            self.selection_box[3] = event.y
    
    def on_canvas_release(self, event):
        """Handle mouse release on the canvas."""
        if self.training_mode and self.selection_box:
            # Finalize selection box
            self.selection_box[2] = event.x
            self.selection_box[3] = event.y
            
            # Ensure valid dimensions
            if abs(self.selection_box[2] - self.selection_box[0]) < 10 or \
               abs(self.selection_box[3] - self.selection_box[1]) < 10:
                self.selection_box = None
                self.status_var.set("Selection too small, please try again")
            else:
                self.status_var.set("Region selected. Click 'Add Target' to create a new target.")
    
    def on_capture_rate_change(self, value):
        """Handle capture rate slider changes."""
        self.capture_rate_value.configure(text=f"{float(value):.1f}")
        self.screen_capture.set_capture_rate(float(value))
        self.config.set("screen_capture", "capture_rate", float(value))
        self.config.save_config()
    
    def on_use_roi_change(self):
        """Handle ROI checkbox changes."""
        use_roi = self.use_roi_var.get()
        self.config.set("screen_capture", "use_roi", use_roi)
        
        # Enable or disable ROI frame widgets
        if use_roi:
            for child in self.roi_frame.winfo_children():
                child.configure(state="normal")
            
            # Apply current ROI settings
            self.apply_roi()
        else:
            for child in self.roi_frame.winfo_children():
                if child != self.roi_apply_button:
                    child.configure(state="disabled")
            
            # Clear ROI
            self.screen_capture.set_roi(None)
        
        self.config.save_config()
    
    def apply_roi(self):
        """Apply the current ROI settings."""
        try:
            roi = [
                self.roi_x_var.get(),
                self.roi_y_var.get(),
                self.roi_width_var.get(),
                self.roi_height_var.get()
            ]
            
            self.screen_capture.set_roi(roi)
            self.config.set("screen_capture", "roi", roi)
            self.config.save_config()
            self.status_var.set(f"ROI applied: {roi}")
        except Exception as e:
            logger.error(f"Error applying ROI: {e}", exc_info=True)
            self.status_var.set("Error applying ROI")
    
    def on_method_change(self, method):
        """Handle feature extraction method changes."""
        self.feature_extractor.set_method(method)
        self.config.set("feature_extraction", "method", method)
        self.config.save_config()
        self.status_var.set(f"Feature extraction method changed to: {method}")
    
    def on_threshold_change(self, value):
        """Handle threshold slider changes."""
        value = float(value)
        self.threshold_value.configure(text=f"{value:.2f}")
        self.feature_extractor.set_threshold(value)
        self.config.set("feature_extraction", "threshold", value)
        self.config.save_config()
    
    def on_speed_change(self, value):
        """Handle speed slider changes."""
        value = float(value)
        self.speed_value.configure(text=f"{value:.1f}")
        self.cursor_controller.set_speed(value)
        self.config.set("cursor_control", "speed", value)
        self.config.save_config()
    
    def on_smooth_change(self):
        """Handle smooth movement checkbox changes."""
        smooth = self.smooth_var.get()
        self.cursor_controller.set_smooth(smooth)
        self.config.set("cursor_control", "smooth", smooth)
        self.config.save_config()