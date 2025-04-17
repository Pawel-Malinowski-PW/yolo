import tkinter as tk
from tkinter import filedialog, messagebox
import os

class NavigationControls:
    def __init__(self, master, app):
        self.master = master
        self.app = app
        
        self.frame = tk.Frame(master)
        self.frame.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
        
        self.folder_btn = tk.Button(master, text="Select Folder", command=self.select_folder)
        self.folder_btn.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
        
        self.nav_frame = tk.Frame(master)
        self.nav_frame.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
        
        self.prev_btn = tk.Button(self.nav_frame, text="< Previous", command=self.prev_image)
        self.prev_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.next_btn = tk.Button(self.nav_frame, text="Next >", command=self.next_image)
        self.next_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Select image folder")
        self.status_label = tk.Label(master, textvariable=self.status_var, wraplength=280)
        self.status_label.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
        
        self.scale_info_var = tk.StringVar()
        self.scale_info_label = tk.Label(master, textvariable=self.scale_info_var, wraplength=280)
        self.scale_info_label.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
        
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.app.set_image_folder(folder)
            
    def prev_image(self):
        self.app.prev_image()
        
    def next_image(self):
        self.app.next_image()
        
    def update_status(self, text):
        self.status_var.set(text)
        
    def update_scale_info(self, original_w, original_h, display_w, display_h, scale_factor):
        self.scale_info_var.set(
            f"Scale: {scale_factor:.2f} (Original: {original_w}x{original_h}px, "
            f"Display: {display_w}x{display_h}px)"
        )