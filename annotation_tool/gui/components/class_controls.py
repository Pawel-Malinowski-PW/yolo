import tkinter as tk
from tkinter import messagebox

class ClassControls:
    def __init__(self, master, annotation_handler):
        self.master = master
        self.annotation_handler = annotation_handler
        
        self.frame = tk.LabelFrame(master, text="Class Name", padx=5, pady=5)
        self.frame.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
        
        self.class_entry = tk.Entry(self.frame)
        self.class_entry.pack(side=tk.TOP, padx=5, pady=2, fill=tk.X)
        
        self.save_class_btn = tk.Button(self.frame, text="Save Class Name", command=self.save_class_name)
        self.save_class_btn.pack(side=tk.TOP, padx=5, pady=2, fill=tk.X)
        
        # Load existing class name if available
        loaded_name = self.annotation_handler.load_class_name()
        if loaded_name:
            self.class_entry.delete(0, tk.END)
            self.class_entry.insert(0, loaded_name)
            
    def save_class_name(self):
        new_name = self.class_entry.get().strip()
        if new_name:
            self.annotation_handler.save_class_name(new_name)
            messagebox.showinfo("Success", f"Class name saved as: {new_name}")