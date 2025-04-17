import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import filedialog, messagebox
import os 

from .components.image_canvas import ImageCanvas
from .components.annotation_list import AnnotationList
from .components.class_controls import ClassControls
from .components.navigation import NavigationControls
from utils.image_utils import ImageHandler
from utils.annotation_utils import AnnotationHandler

class YOLOAnnotationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Annotation Tool - Single Class")
        
        # Initialize handlers
        self.image_handler = ImageHandler()
        self.annotation_handler = AnnotationHandler()
        
        # Create main container
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left side - image canvas
        self.left_frame = tk.Frame(self.main_paned)
        self.image_canvas = ImageCanvas(self.left_frame, self.image_handler, self.annotation_handler)
        self.image_canvas.master = self  # Pass reference to main app
        
        # Right side - control panel
        self.right_frame = tk.Frame(self.main_paned, width=300)
        
        # Create components
        self.navigation = NavigationControls(self.right_frame, self)
        self.class_controls = ClassControls(self.right_frame, self.annotation_handler)
        self.annotation_list = AnnotationList(self.right_frame, self.annotation_handler)
        
        # Save button
        self.save_btn = tk.Button(self.right_frame, text="Save Annotations", command=self.save_annotations)
        self.save_btn.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
        
        # Add frames to main panel
        self.main_paned.add(self.left_frame, minsize=1200)
        self.main_paned.add(self.right_frame, minsize=250, width=300)
        
        # Set minimum window size
        self.root.minsize(800, 600)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-z>', lambda e: self.undo_annotation())
        self.root.bind('<Control-Z>', lambda e: self.undo_annotation())
        
        # Initialize state
        self.image_folder = ""
        self.image_list = []
        self.current_image_index = 0
        
    def set_image_folder(self, folder):
        self.image_folder = folder
        self.image_list = [f for f in os.listdir(self.image_folder) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        self.current_image_index = 0
        
        if self.image_list:
            self.load_current_image()
            self.navigation.update_status(f"Image {self.current_image_index+1}/{len(self.image_list)}")
        else:
            messagebox.showwarning("No Images", "No JPG/PNG images found in selected folder.")
            
    def load_current_image(self):
        if not self.image_list:
            return
            
        image_path = os.path.join(self.image_folder, self.image_list[self.current_image_index])
        self.image_handler.load_image(image_path)
        self.annotation_handler.load_annotations(image_path)
        
        # Update UI
        display_w, display_h = self.image_handler.scale_image_to_fit()
        self.image_canvas.set_scroll_region(display_w, display_h)
        self.image_canvas.update_display()
        self.annotation_list.update_list()
        
        # Update scale info
        orig_w, orig_h = self.image_handler.get_original_dimensions()
        self.navigation.update_scale_info(
            orig_w, orig_h, 
            display_w, display_h,
            self.image_handler.scale_factor
        )
        
    def save_annotations(self):
        if self.image_handler.image_path:
            if self.annotation_handler.save_annotations(self.image_handler.image_path):
                self.navigation.update_status(f"Annotations saved: {self.image_handler.image_path}")
                
    def prev_image(self):
        if self.current_image_index > 0:
            self.save_annotations()
            self.current_image_index -= 1
            self.load_current_image()
            self.navigation.update_status(f"Image {self.current_image_index+1}/{len(self.image_list)}")
            
    def next_image(self):
        if self.current_image_index < len(self.image_list) - 1:
            self.save_annotations()
            self.current_image_index += 1
            self.load_current_image()
            self.navigation.update_status(f"Image {self.current_image_index+1}/{len(self.image_list)}")
            
    def undo_annotation(self):
        if self.annotation_handler.undo():
            self.image_canvas.update_display()
            self.annotation_list.update_list()