import tkinter as tk
from tkinter import ttk
print(f"Initializing AnnotationList from {__file__}")
class AnnotationList:
    def __init__(self, master, annotation_handler):
        self.master = master
        self.annotation_handler = annotation_handler
        
        self.frame = tk.LabelFrame(master, text="Annotations", padx=5, pady=5)
        self.frame.pack(side=tk.TOP, padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        self.listbox = tk.Listbox(self.frame, height=10)
        self.listbox.pack(side=tk.TOP, padx=5, pady=2, fill=tk.BOTH, expand=True)
        
        self.btn_frame = tk.Frame(self.frame)
        self.btn_frame.pack(side=tk.TOP, padx=5, pady=2, fill=tk.X)
        
        self.delete_btn = tk.Button(self.btn_frame, text="Delete Selected", command=self.delete_annotation)
        self.delete_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.undo_btn = tk.Button(self.btn_frame, text="Undo (Ctrl+Z)", command=self.undo_annotation)
        self.undo_btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
    def update_list(self):
        self.listbox.delete(0, tk.END)
        print("Updating annotation list:", self.annotation_handler.annotations)  # Debug log
        for i, ann in enumerate(self.annotation_handler.annotations):
            self.listbox.insert(tk.END, 
                f"{i}: {self.annotation_handler.class_name} - x: {ann['x_center']:.3f}, y: {ann['y_center']:.3f}, "
                f"w: {ann['width']:.3f}, h: {ann['height']:.3f}")
                
    def delete_annotation(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if self.annotation_handler.delete_annotation(index):
                self.update_list()
                
    def undo_annotation(self):
        if self.annotation_handler.undo():
            self.update_list()