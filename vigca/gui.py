"""
User Interface Module for ViGCA

Provides a graphical user interface for interacting with the ViGCA application.
"""
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk

from vigca.screen_capture import ScreenCapture
from vigca.feature_extraction import FeatureExtractor
from vigca.target_manager import TargetManager
from vigca.cursor_control import CursorController
from vigca.configuration import Configuration

import logging
logger = logging.getLogger(__name__)

class VigcaGUI(ttk.Frame):
    """
    Main application GUI for Vision-Guided Cursor Automation.
    """
    
    def __init__(self, parent):
        """
        Initialize the GUI.
        
        Args:
            parent (tk.Tk): Parent window
        """
        super().__init__(parent)
        self.parent = parent
        
        # Initialize the modules
        self.config = Configuration()
        self.screen_capture = ScreenCapture(
            capture_rate=self.config.get("screen_capture", "capture_rate"),
            roi=self.config.get("screen_capture", "use_roi") and self.config.get("screen_capture", "roi") or None
        )
        self.feature_extractor = FeatureExtractor(
            method=self.config.get("feature_extraction", "method")
        )
        self.feature_extractor.set_threshold(self.config.get("feature_extraction", "threshold"))
        self.target_manager = TargetManager()
        self.cursor_controller = CursorController(
            speed=self.config.get("cursor_control", "speed"),
            smooth=self.config.get("cursor_control", "smooth")
        )
        
        # State variables
        self.running = False
        self.training_mode = False
        self.selection_box = None
        self.active_targets = []
        
        # Set up the application state
        for target_id in self.config.get("application", "active_target_ids"):
            target = self.target_manager.get_target(target_id)
            if target:
                self.active_targets.append(target_id)
        
        # Set up the UI
        self.create_widgets()
        self.layout_widgets()
        
        # Start the display loop
        self.after(100, self.update_display)
        
        logger.debug("GUI initialized")
    
    def create_widgets(self):
        """Create all the widgets for the UI."""
        # Create style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5)
        self.style.configure("Run.TButton", foreground="green")
        self.style.configure("Stop.TButton", foreground="red")
        self.style.configure("Train.TButton", foreground="blue")
        
        # Create main frames
        self.control_frame = ttk.LabelFrame(self, text="Controls")
        self.display_frame = ttk.LabelFrame(self, text="Screen Display")
        self.target_frame = ttk.LabelFrame(self, text="Targets")
        self.config_frame = ttk.LabelFrame(self, text="Configuration")
        
        # Create control widgets
        self.run_button = ttk.Button(self.control_frame, text="Start Detection", style="Run.TButton", 
                                     command=self.toggle_detection)
        self.train_button = ttk.Button(self.control_frame, text="Start Training", style="Train.TButton", 
                                       command=self.toggle_training)
        self.capture_button = ttk.Button(self.control_frame, text="Capture Screen", 
                                         command=self.capture_screen)
        
        # Create display widgets
        self.display_canvas = tk.Canvas(self.display_frame, bg="black", 
                                        width=800, height=600)
        self.display_canvas.bind("<Button-1>", self.on_canvas_click)
        self.display_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.display_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Create target widgets
        self.target_listbox = tk.Listbox(self.target_frame, selectmode=tk.SINGLE, 
                                         height=10, width=40)
        self.target_listbox.bind("<<ListboxSelect>>", self.on_target_select)
        self.target_scrollbar = ttk.Scrollbar(self.target_frame, orient=tk.VERTICAL, 
                                             command=self.target_listbox.yview)
        self.target_listbox.config(yscrollcommand=self.target_scrollbar.set)
        
        self.target_buttons_frame = ttk.Frame(self.target_frame)
        self.add_target_button = ttk.Button(self.target_buttons_frame, text="Add Target", 
                                           command=self.add_target)
        self.remove_target_button = ttk.Button(self.target_buttons_frame, text="Remove Target", 
                                              command=self.remove_target)
        self.rename_target_button = ttk.Button(self.target_buttons_frame, text="Rename Target", 
                                              command=self.rename_target)
        self.toggle_active_button = ttk.Button(self.target_buttons_frame, text="Toggle Active", 
                                              command=self.toggle_target_active)
        
        # Create configuration widgets
        self.config_notebook = ttk.Notebook(self.config_frame)
        
        # Screen capture config
        self.capture_config_frame = ttk.Frame(self.config_notebook)
        self.config_notebook.add(self.capture_config_frame, text="Screen Capture")
        
        self.capture_rate_label = ttk.Label(self.capture_config_frame, text="Capture Rate (FPS):")
        self.capture_rate_var = tk.DoubleVar(value=self.config.get("screen_capture", "capture_rate"))
        self.capture_rate_scale = ttk.Scale(self.capture_config_frame, from_=0.1, to=10.0, 
                                          variable=self.capture_rate_var, 
                                          orient=tk.HORIZONTAL, length=200)
        self.capture_rate_scale.bind("<ButtonRelease-1>", self.on_capture_rate_change)
        self.capture_rate_value = ttk.Label(self.capture_config_frame, 
                                          text=str(self.capture_rate_var.get()))
        
        self.use_roi_var = tk.BooleanVar(value=self.config.get("screen_capture", "use_roi"))
        self.use_roi_check = ttk.Checkbutton(self.capture_config_frame, text="Use Region of Interest", 
                                           variable=self.use_roi_var, 
                                           command=self.on_use_roi_change)
        
        self.roi_frame = ttk.Frame(self.capture_config_frame)
        roi_config = self.config.get("screen_capture", "roi")
        self.roi_x_label = ttk.Label(self.roi_frame, text="X:")
        self.roi_x_var = tk.IntVar(value=roi_config[0])
        self.roi_x_entry = ttk.Entry(self.roi_frame, textvariable=self.roi_x_var, width=5)
        
        self.roi_y_label = ttk.Label(self.roi_frame, text="Y:")
        self.roi_y_var = tk.IntVar(value=roi_config[1])
        self.roi_y_entry = ttk.Entry(self.roi_frame, textvariable=self.roi_y_var, width=5)
        
        self.roi_width_label = ttk.Label(self.roi_frame, text="Width:")
        self.roi_width_var = tk.IntVar(value=roi_config[2])
        self.roi_width_entry = ttk.Entry(self.roi_frame, textvariable=self.roi_width_var, width=5)
        
        self.roi_height_label = ttk.Label(self.roi_frame, text="Height:")
        self.roi_height_var = tk.IntVar(value=roi_config[3])
        self.roi_height_entry = ttk.Entry(self.roi_frame, textvariable=self.roi_height_var, width=5)
        
        self.roi_apply_button = ttk.Button(self.roi_frame, text="Apply ROI", 
                                          command=self.apply_roi)
        
        # Feature extraction config
        self.feature_config_frame = ttk.Frame(self.config_notebook)
        self.config_notebook.add(self.feature_config_frame, text="Feature Extraction")
        
        self.method_label = ttk.Label(self.feature_config_frame, text="Detection Method:")
        self.method_var = tk.StringVar(value=self.config.get("feature_extraction", "method"))
        
        methods = [(name, desc) for name, desc in FeatureExtractor.METHODS.items()]
        self.method_menu = ttk.OptionMenu(
            self.feature_config_frame, 
            self.method_var, 
            methods[0][0], 
            *[m[0] for m in methods],
            command=self.on_method_change
        )
        
        self.threshold_label = ttk.Label(self.feature_config_frame, text="Confidence Threshold:")
        self.threshold_var = tk.DoubleVar(value=self.config.get("feature_extraction", "threshold"))
        self.threshold_scale = ttk.Scale(self.feature_config_frame, from_=0.1, to=1.0, 
                                       variable=self.threshold_var, 
                                       orient=tk.HORIZONTAL, length=200)
        self.threshold_scale.bind("<ButtonRelease-1>", self.on_threshold_change)
        self.threshold_value = ttk.Label(self.feature_config_frame, 
                                       text=str(self.threshold_var.get()))
        
        # Cursor control config
        self.cursor_config_frame = ttk.Frame(self.config_notebook)
        self.config_notebook.add(self.cursor_config_frame, text="Cursor Control")
        
        self.speed_label = ttk.Label(self.cursor_config_frame, text="Cursor Speed:")
        self.speed_var = tk.DoubleVar(value=self.config.get("cursor_control", "speed"))
        self.speed_scale = ttk.Scale(self.cursor_config_frame, from_=1.0, to=10.0, 
                                   variable=self.speed_var, 
                                   orient=tk.HORIZONTAL, length=200)
        self.speed_scale.bind("<ButtonRelease-1>", self.on_speed_change)
        self.speed_value = ttk.Label(self.cursor_config_frame, 
                                   text=str(self.speed_var.get()))
        
        self.smooth_var = tk.BooleanVar(value=self.config.get("cursor_control", "smooth"))
        self.smooth_check = ttk.Checkbutton(self.cursor_config_frame, text="Smooth Movement", 
                                          variable=self.smooth_var, 
                                          command=self.on_smooth_change)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        
        # Update target list
        self.update_target_list()
    
    def layout_widgets(self):
        """Arrange all widgets in the UI."""
        # Layout control frame
        self.run_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.train_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.capture_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Layout display frame
        self.display_canvas.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Layout target frame
        self.target_listbox.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.target_scrollbar.pack(side=tk.LEFT, pady=5, fill=tk.Y)
        
        self.target_buttons_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        self.add_target_button.pack(pady=2, fill=tk.X)
        self.remove_target_button.pack(pady=2, fill=tk.X)
        self.rename_target_button.pack(pady=2, fill=tk.X)
        self.toggle_active_button.pack(pady=2, fill=tk.X)
        
        # Layout configuration frame
        # Screen capture config
        self.capture_rate_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.capture_rate_scale.grid(row=0, column=1, padx=5, pady=5)
        self.capture_rate_value.grid(row=0, column=2, padx=5, pady=5)
        
        self.use_roi_check.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        self.roi_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        self.roi_x_label.grid(row=0, column=0, padx=2, pady=2)
        self.roi_x_entry.grid(row=0, column=1, padx=2, pady=2)
        self.roi_y_label.grid(row=0, column=2, padx=2, pady=2)
        self.roi_y_entry.grid(row=0, column=3, padx=2, pady=2)
        self.roi_width_label.grid(row=0, column=4, padx=2, pady=2)
        self.roi_width_entry.grid(row=0, column=5, padx=2, pady=2)
        self.roi_height_label.grid(row=0, column=6, padx=2, pady=2)
        self.roi_height_entry.grid(row=0, column=7, padx=2, pady=2)
        self.roi_apply_button.grid(row=0, column=8, padx=2, pady=2)
        
        # Feature extraction config
        self.method_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.method_menu.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        self.threshold_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.threshold_scale.grid(row=1, column=1, padx=5, pady=5)
        self.threshold_value.grid(row=1, column=2, padx=5, pady=5)
        
        # Cursor control config
        self.speed_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.speed_scale.grid(row=0, column=1, padx=5, pady=5)
        self.speed_value.grid(row=0, column=2, padx=5, pady=5)
        
        self.smooth_check.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # Layout config notebook
        self.config_notebook.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Layout main frames
        self.control_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky=tk.EW)
        self.display_frame.grid(row=1, column=0, padx=10, pady=5, sticky=tk.NSEW)
        self.target_frame.grid(row=1, column=1, padx=10, pady=5, sticky=tk.NSEW)
        self.config_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky=tk.EW)
        self.status_bar.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky=tk.EW)
        
        # Configure grid weights
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
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
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                
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
            self.run_button.config(text="Stop Detection", style="Stop.TButton")
            self.train_button.config(state=tk.DISABLED)
            self.status_var.set("Detection active")
            
            # Save active targets to config
            self.config.set("application", "active_target_ids", self.active_targets)
            self.config.save_config()
        else:
            self.run_button.config(text="Start Detection", style="Run.TButton")
            self.train_button.config(state=tk.NORMAL)
            self.status_var.set("Detection stopped")
    
    def toggle_training(self):
        """Start or stop the training mode."""
        self.training_mode = not self.training_mode
        
        if self.training_mode:
            self.train_button.config(text="Stop Training", style="Stop.TButton")
            self.run_button.config(state=tk.DISABLED)
            self.selection_box = None
            self.status_var.set("Training mode: Select targets on screen")
        else:
            self.train_button.config(text="Start Training", style="Train.TButton")
            self.run_button.config(state=tk.NORMAL)
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
        self.target_listbox.delete(0, tk.END)
        
        # Add all targets
        targets = self.target_manager.get_all_targets()
        for target_id, target in targets.items():
            # Mark active targets with an asterisk
            active_marker = " [A]" if target_id in self.active_targets else ""
            self.target_listbox.insert(tk.END, f"{target.name}{active_marker}")
            # Store the target ID in the listbox item
            self.target_listbox.itemconfig(tk.END, {'target_id': target_id})
    
    def on_target_select(self, event):
        """Handle target selection in the listbox."""
        selection = self.target_listbox.curselection()
        if selection:
            index = selection[0]
            # Get the target ID from the listbox item
            target_id = self.target_listbox.itemcget(index, 'target_id')
            # Get the target
            target = self.target_manager.get_target(target_id)
            if target:
                self.status_var.set(f"Selected target: {target.name}")
    
    def add_target(self, name=None, selection=None):
        """Add a new target based on the current selection box."""
        if not self.training_mode and not selection:
            messagebox.showwarning("Add Target", "Please enter training mode and select a region first.")
            return
        
        # Use provided selection or current selection box
        sel_box = selection or self.selection_box
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
        
        # Get name from user if not provided
        if not name:
            name = tk.simpledialog.askstring("Target Name", "Enter a name for this target:")
        
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
        
        # Update the list
        self.update_target_list()
        self.status_var.set(f"Added new target: {name}")
        
        # Clear selection box
        self.selection_box = None
    
    def remove_target(self):
        """Remove the selected target."""
        selection = self.target_listbox.curselection()
        if not selection:
            messagebox.showwarning("Remove Target", "Please select a target to remove.")
            return
        
        index = selection[0]
        target_id = self.target_listbox.itemcget(index, 'target_id')
        target_name = self.target_manager.get_target(target_id).name
        
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
    
    def rename_target(self):
        """Rename the selected target."""
        selection = self.target_listbox.curselection()
        if not selection:
            messagebox.showwarning("Rename Target", "Please select a target to rename.")
            return
        
        index = selection[0]
        target_id = self.target_listbox.itemcget(index, 'target_id')
        target = self.target_manager.get_target(target_id)
        
        # Get new name from user
        new_name = tk.simpledialog.askstring("Rename Target", 
                                            "Enter a new name for this target:", 
                                            initialvalue=target.name)
        
        if new_name:
            success = self.target_manager.rename_target(target_id, new_name)
            if success:
                self.update_target_list()
                self.status_var.set(f"Renamed target to: {new_name}")
    
    def toggle_target_active(self):
        """Toggle the active state of the selected target."""
        selection = self.target_listbox.curselection()
        if not selection:
            messagebox.showwarning("Toggle Active", "Please select a target to toggle.")
            return
        
        index = selection[0]
        target_id = self.target_listbox.itemcget(index, 'target_id')
        target = self.target_manager.get_target(target_id)
        
        if target_id in self.active_targets:
            self.active_targets.remove(target_id)
            self.status_var.set(f"Target '{target.name}' deactivated")
        else:
            self.active_targets.append(target_id)
            self.status_var.set(f"Target '{target.name}' activated")
        
        self.update_target_list()
    
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
    
    def on_capture_rate_change(self, event):
        """Handle capture rate slider changes."""
        value = self.capture_rate_var.get()
        self.capture_rate_value.config(text=f"{value:.1f}")
        self.screen_capture.set_capture_rate(value)
        self.config.set("screen_capture", "capture_rate", value)
        self.config.save_config()
    
    def on_use_roi_change(self):
        """Handle ROI checkbox changes."""
        use_roi = self.use_roi_var.get()
        self.config.set("screen_capture", "use_roi", use_roi)
        
        if use_roi:
            # Enable ROI frame
            for child in self.roi_frame.winfo_children():
                child.configure(state=tk.NORMAL)
            
            # Apply current ROI settings
            self.apply_roi()
        else:
            # Disable ROI frame
            for child in self.roi_frame.winfo_children():
                if child != self.roi_apply_button:
                    child.configure(state=tk.DISABLED)
            
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
    
    def on_threshold_change(self, event):
        """Handle threshold slider changes."""
        value = self.threshold_var.get()
        self.threshold_value.config(text=f"{value:.2f}")
        self.feature_extractor.set_threshold(value)
        self.config.set("feature_extraction", "threshold", value)
        self.config.save_config()
    
    def on_speed_change(self, event):
        """Handle speed slider changes."""
        value = self.speed_var.get()
        self.speed_value.config(text=f"{value:.1f}")
        self.cursor_controller.set_speed(value)
        self.config.set("cursor_control", "speed", value)
        self.config.save_config()
    
    def on_smooth_change(self):
        """Handle smooth movement checkbox changes."""
        smooth = self.smooth_var.get()
        self.cursor_controller.set_smooth(smooth)
        self.config.set("cursor_control", "smooth", smooth)
        self.config.save_config()