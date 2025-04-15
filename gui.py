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

from screen_capture import ScreenCapture
from feature_extraction import FeatureExtractor
from target_manager import TargetManager
from cursor_control import CursorController
from configuration import Configuration

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
                                # Update detection statistics
                                self.target_manager.update_target_detection(target_id)
                                
                                # Move cursor to the highest confidence match
                                best_match = max(target_matches, key=lambda m: m[4])
                                self.cursor_controller.move_to_target(best_match)
                                
                                # Draw matches on display frame
                                for match in target_matches:
                                    x, y, w, h, conf = match
                                    # Scale coordinates to display frame size
                                    x_scaled = int(x * target_width / frame_w)
                                    y_scaled = int(y * target_height / frame_h)
                                    w_scaled = int(w * target_width / frame_w)
                                    h_scaled = int(h * target_height / frame_h)
                                    
                                    # Draw rectangle
                                    cv2.rectangle(display_frame, (x_scaled, y_scaled), 
                                                 (x_scaled + w_scaled, y_scaled + h_scaled), 
                                                 (0, 255, 0), 2)
                                    
                                    # Draw confidence value
                                    conf_text = f"{conf:.2f}"
                                    cv2.putText(display_frame, conf_text, (x_scaled, y_scaled - 5), 
                                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    # Update status bar
                    if matches:
                        total_matches = sum(len(m) for m in matches.values())
                        self.status_var.set(f"Running - Found {total_matches} matches for {len(matches)} targets")
                    else:
                        self.status_var.set("Running - No matches found")
                
                # Draw selection box if we're in training mode
                if self.training_mode and self.selection_box:
                    start_x, start_y, end_x, end_y = self.selection_box
                    
                    # Scale coordinates to display frame size
                    start_x_scaled = int(start_x * target_width / canvas_width)
                    start_y_scaled = int(start_y * target_height / canvas_height)
                    end_x_scaled = int(end_x * target_width / canvas_width)
                    end_y_scaled = int(end_y * target_height / canvas_height)
                    
                    # Draw rectangle
                    cv2.rectangle(display_frame, (start_x_scaled, start_y_scaled), 
                                 (end_x_scaled, end_y_scaled), (0, 0, 255), 2)
                
                # Convert for tkinter
                image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(image)
                photo = ImageTk.PhotoImage(image=image)
                
                # Update canvas
                self.display_canvas.config(width=target_width, height=target_height)
                self.display_canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                self.display_canvas.image = photo  # Keep a reference to prevent garbage collection
            
        # Schedule the next update
        self.after(50, self.update_display)
    
    def toggle_detection(self):
        """Start or stop the detection process."""
        if not self.running:
            # Check if we have active targets
            if not self.active_targets:
                messagebox.showwarning("No Active Targets", 
                                      "Please add and activate at least one target before starting detection.")
                return
            
            # Start detection
            self.running = True
            self.training_mode = False
            self.run_button.config(text="Stop Detection", style="Stop.TButton")
            self.train_button.config(state=tk.DISABLED)
            self.status_var.set("Running - Detecting targets...")
        else:
            # Stop detection
            self.running = False
            self.run_button.config(text="Start Detection", style="Run.TButton")
            self.train_button.config(state=tk.NORMAL)
            self.status_var.set("Ready")
    
    def toggle_training(self):
        """Start or stop the training mode."""
        if not self.training_mode:
            # Start training mode
            self.training_mode = True
            self.running = False
            self.train_button.config(text="Stop Training", style="Stop.TButton")
            self.run_button.config(state=tk.DISABLED)
            self.status_var.set("Training Mode - Select a region to add a target")
        else:
            # Stop training mode
            self.training_mode = False
            self.selection_box = None
            self.train_button.config(text="Start Training", style="Train.TButton")
            self.run_button.config(state=tk.NORMAL)
            self.status_var.set("Ready")
    
    def capture_screen(self):
        """Capture the current screen."""
        self.screen_capture.capture(force=True)
        self.status_var.set("Screen captured")
    
    def update_target_list(self):
        """Update the target listbox with current targets."""
        self.target_listbox.delete(0, tk.END)
        
        targets = self.target_manager.get_all_targets()
        for target_id, target in targets.items():
            active_mark = "✓ " if target_id in self.active_targets else "  "
            self.target_listbox.insert(tk.END, f"{active_mark}{target.name}")
            # Store target ID as item data
            self.target_listbox.itemconfig(tk.END, {"target_id": target_id})
    
    def on_target_select(self, event):
        """Handle target selection in the listbox."""
        selection = self.target_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        target_id = self.target_listbox.itemconfig(index).get("target_id")
        
        if target_id:
            target = self.target_manager.get_target(target_id)
            if target:
                self.status_var.set(f"Selected target: {target.name}")
    
    def add_target(self, name=None, selection=None):
        """Add a new target based on the current selection box."""
        if not name:
            name = tk.simpledialog.askstring("Target Name", "Enter a name for the target:")
        
        if not name:
            return  # User canceled
        
        # Get selection box or use provided selection
        if selection:
            start_x, start_y, end_x, end_y = selection
        elif self.selection_box:
            start_x, start_y, end_x, end_y = self.selection_box
        else:
            messagebox.showwarning("No Selection", 
                                  "Please select a region on the screen first.")
            return
        
        # Ensure start coordinates are smaller than end coordinates
        if start_x > end_x:
            start_x, end_x = end_x, start_x
        if start_y > end_y:
            start_y, end_y = end_y, start_y
        
        # Get the current frame
        frame = self.screen_capture.get_last_frame()
        if frame is None:
            messagebox.showerror("Error", "No screen capture available.")
            return
        
        # Calculate selection in original image coordinates
        canvas_width = self.display_canvas.winfo_width()
        canvas_height = self.display_canvas.winfo_height()
        frame_h, frame_w = frame.shape[:2]
        
        x1 = int(start_x * frame_w / canvas_width)
        y1 = int(start_y * frame_h / canvas_height)
        x2 = int(end_x * frame_w / canvas_width)
        y2 = int(end_y * frame_h / canvas_height)
        
        # Extract region of interest
        x1 = max(0, min(x1, frame_w - 1))
        y1 = max(0, min(y1, frame_h - 1))
        x2 = max(0, min(x2, frame_w - 1))
        y2 = max(0, min(y2, frame_h - 1))
        
        roi_width = x2 - x1
        roi_height = y2 - y1
        
        if roi_width < 10 or roi_height < 10:
            messagebox.showwarning("Selection Too Small", 
                                  "Please select a larger region.")
            return
        
        roi = frame[y1:y2, x1:x2]
        
        # Extract features
        features = self.feature_extractor.extract_features(roi)
        
        if features is None:
            messagebox.showerror("Error", "Failed to extract features from selection.")
            return
        
        # Add the target
        target_id = self.target_manager.add_target(
            name, 
            features, 
            self.feature_extractor.method, 
            (x1, y1, roi_width, roi_height), 
            roi
        )
        
        # Add to active targets
        self.active_targets.append(target_id)
        
        # Save active targets to config
        self.config.set("application", "active_target_ids", self.active_targets)
        self.config.save_config()
        
        # Update target list
        self.update_target_list()
        
        # Clear selection box
        self.selection_box = None
        
        self.status_var.set(f"Added new target: {name}")
    
    def remove_target(self):
        """Remove the selected target."""
        selection = self.target_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Target Selected", 
                                  "Please select a target to remove.")
            return
        
        index = selection[0]
        target_id = self.target_listbox.itemconfig(index).get("target_id")
        
        if not target_id:
            return
        
        target = self.target_manager.get_target(target_id)
        if not target:
            return
        
        if messagebox.askyesno("Confirm Remove", 
                              f"Are you sure you want to remove the target '{target.name}'?"):
            # Remove from active targets
            if target_id in self.active_targets:
                self.active_targets.remove(target_id)
            
            # Remove from manager
            self.target_manager.remove_target(target_id)
            
            # Save active targets to config
            self.config.set("application", "active_target_ids", self.active_targets)
            self.config.save_config()
            
            # Update target list
            self.update_target_list()
            
            self.status_var.set(f"Removed target: {target.name}")
    
    def rename_target(self):
        """Rename the selected target."""
        selection = self.target_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Target Selected", 
                                  "Please select a target to rename.")
            return
        
        index = selection[0]
        target_id = self.target_listbox.itemconfig(index).get("target_id")
        
        if not target_id:
            return
        
        target = self.target_manager.get_target(target_id)
        if not target:
            return
        
        new_name = tk.simpledialog.askstring("Rename Target", 
                                            "Enter a new name for the target:", 
                                            initialvalue=target.name)
        
        if not new_name:
            return  # User canceled
        
        self.target_manager.rename_target(target_id, new_name)
        
        # Update target list
        self.update_target_list()
        
        self.status_var.set(f"Renamed target to: {new_name}")
    
    def toggle_target_active(self):
        """Toggle the active state of the selected target."""
        selection = self.target_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Target Selected", 
                                  "Please select a target to toggle.")
            return
        
        index = selection[0]
        target_id = self.target_listbox.itemconfig(index).get("target_id")
        
        if not target_id:
            return
        
        target = self.target_manager.get_target(target_id)
        if not target:
            return
        
        if target_id in self.active_targets:
            self.active_targets.remove(target_id)
            state = "inactive"
        else:
            self.active_targets.append(target_id)
            state = "active"
        
        # Save active targets to config
        self.config.set("application", "active_target_ids", self.active_targets)
        self.config.save_config()
        
        # Update target list
        self.update_target_list()
        
        self.status_var.set(f"Target '{target.name}' is now {state}")
    
    def on_canvas_click(self, event):
        """Handle mouse click on the canvas."""
        if not self.training_mode:
            return
        
        self.selection_box = (event.x, event.y, event.x, event.y)
    
    def on_canvas_drag(self, event):
        """Handle mouse drag on the canvas."""
        if not self.training_mode or not self.selection_box:
            return
        
        self.selection_box = (self.selection_box[0], self.selection_box[1], event.x, event.y)
    
    def on_canvas_release(self, event):
        """Handle mouse release on the canvas."""
        if not self.training_mode or not self.selection_box:
            return
        
        # Finalize the selection box
        self.selection_box = (self.selection_box[0], self.selection_box[1], event.x, event.y)
        
        # Ask for target name and add target
        self.add_target()
    
    def on_capture_rate_change(self, event):
        """Handle capture rate slider changes."""
        value = self.capture_rate_var.get()
        self.capture_rate_value.config(text=f"{value:.1f}")
        
        # Update screen capture rate
        self.screen_capture.set_capture_rate(value)
        
        # Save to config
        self.config.set("screen_capture", "capture_rate", value)
        self.config.save_config()
    
    def on_use_roi_change(self):
        """Handle ROI checkbox changes."""
        use_roi = self.use_roi_var.get()
        
        # Update screen capture ROI setting
        if use_roi:
            roi = [
                self.roi_x_var.get(),
                self.roi_y_var.get(),
                self.roi_width_var.get(),
                self.roi_height_var.get()
            ]
            self.screen_capture.set_roi(roi)
        else:
            self.screen_capture.set_roi(None)
        
        # Save to config
        self.config.set("screen_capture", "use_roi", use_roi)
        self.config.save_config()
    
    def apply_roi(self):
        """Apply the current ROI settings."""
        roi = [
            self.roi_x_var.get(),
            self.roi_y_var.get(),
            self.roi_width_var.get(),
            self.roi_height_var.get()
        ]
        
        # Update screen capture ROI
        if self.use_roi_var.get():
            self.screen_capture.set_roi(roi)
        
        # Save to config
        self.config.set("screen_capture", "roi", roi)
        self.config.save_config()
        
        self.status_var.set(f"Applied ROI: {roi}")
    
    def on_method_change(self, method):
        """Handle feature extraction method changes."""
        # Update feature extractor method
        self.feature_extractor.set_method(method)
        
        # Save to config
        self.config.set("feature_extraction", "method", method)
        self.config.save_config()
        
        self.status_var.set(f"Changed detection method to: {FeatureExtractor.METHODS.get(method, method)}")
    
    def on_threshold_change(self, event):
        """Handle threshold slider changes."""
        value = self.threshold_var.get()
        self.threshold_value.config(text=f"{value:.2f}")
        
        # Update feature extractor threshold
        self.feature_extractor.set_threshold(value)
        
        # Save to config
        self.config.set("feature_extraction", "threshold", value)
        self.config.save_config()
    
    def on_speed_change(self, event):
        """Handle speed slider changes."""
        value = self.speed_var.get()
        self.speed_value.config(text=f"{value:.1f}")
        
        # Update cursor controller speed
        self.cursor_controller.set_speed(value)
        
        # Save to config
        self.config.set("cursor_control", "speed", value)
        self.config.save_config()
    
    def on_smooth_change(self):
        """Handle smooth movement checkbox changes."""
        smooth = self.smooth_var.get()
        
        # Update cursor controller smooth setting
        self.cursor_controller.set_smooth(smooth)
        
        # Save to config
        self.config.set("cursor_control", "smooth", smooth)
        self.config.save_config()
