import tkinter as tk
import cv2
from PIL import Image, ImageTk

class ImageCanvas:
    def __init__(self, master, image_handler, annotation_handler):
        self.master = master
        self.image_handler = image_handler
        self.annotation_handler = annotation_handler
        
        self.canvas = tk.Canvas(master, bg='gray')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars
        self.v_scroll = tk.Scrollbar(master, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.v_scroll.config(command=self.canvas.yview)
        
        self.h_scroll = tk.Scrollbar(master, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.h_scroll.config(command=self.canvas.xview)
        
        self.canvas.config(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set
        )
        
        # Image frame
        self.image_frame = tk.Frame(self.canvas)
        self.image_panel = tk.Label(self.image_frame)
        self.image_panel.pack()
        
        self.image_frame_id = self.canvas.create_window((0, 0), window=self.image_frame, anchor=tk.NW)
        
        # Drawing state
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.current_x, self.current_y = -1, -1
        self.class_color = (0, 255, 0)  # Green
        
        # Bind events
        self.image_panel.bind("<Button-1>", self.start_bbox)
        self.image_panel.bind("<B1-Motion>", self.draw_bbox)
        self.image_panel.bind("<ButtonRelease-1>", self.end_bbox)
        
        # Dodane: Bind event zmiany rozmiaru canvasu
        self.canvas.bind('<Configure>', self.on_canvas_resize)
    
    def on_canvas_resize(self, event):
        """Handle canvas resize event to keep image centered"""
        self.center_image()
    
    def center_image(self):
        """Center the image in the canvas"""
        self.canvas.update_idletasks()  # Make sure canvas dimensions are up-to-date
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if self.image_handler.display_image is None:
            return
            
        img_width = self.image_handler.display_image.shape[1]
        img_height = self.image_handler.display_image.shape[0]
        
        x_offset = max((canvas_width - img_width) // 2, 0)
        y_offset = max((canvas_height - img_height) // 2, 0)
        
        # Use the canvas object ID to set coordinates
        self.canvas.coords(self.image_frame_id, x_offset, y_offset)
    
    def update_display(self):
        if self.image_handler.display_image is None:
            return
            
        display_img = self.image_handler.display_image.copy()
        h, w = display_img.shape[:2]
        
        # Draw existing bounding boxes
        for ann in self.annotation_handler.annotations:
            x_center = ann["x_center"] * w
            y_center = ann["y_center"] * h
            box_w = ann["width"] * w
            box_h = ann["height"] * h
            
            x1 = int(x_center - box_w/2)
            y1 = int(y_center - box_h/2)
            x2 = int(x_center + box_w/2)
            y2 = int(y_center + box_h/2)
            
            cv2.rectangle(display_img, (x1, y1), (x2, y2), self.class_color, 2)
            cv2.putText(display_img, self.annotation_handler.class_name, (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.class_color, 2)
        
        # Draw currently drawing bounding box
        if self.drawing and self.start_x != -1 and self.start_y != -1:
            cv2.rectangle(display_img, (self.start_x, self.start_y), 
                        (self.current_x, self.current_y), self.class_color, 2)
        
        # Update the displayed image
        img_tk = self.image_handler.get_tk_image(display_img)
        self.image_panel.config(image=img_tk)
        self.image_panel.image = img_tk
        
        # Center the image after update
        self.center_image()
    
    def set_scroll_region(self, width, height):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Calculate centered position
        x_offset = max((canvas_width - width) // 2, 0)
        y_offset = max((canvas_height - height) // 2, 0)
        
        # Set frame size and position
        self.image_frame.config(width=width, height=height)
        self.canvas.create_window((x_offset, y_offset), window=self.image_frame, anchor=tk.NW)
        self.canvas.config(scrollregion=(0, 0, width, height))
    
    def start_bbox(self, event):
        self.drawing = True
        self.start_x = event.x
        self.start_y = event.y
        self.current_x = event.x
        self.current_y = event.y
        
    def draw_bbox(self, event):
        if self.drawing:
            self.current_x = event.x
            self.current_y = event.y
            self.update_display()
            
    def end_bbox(self, event):
        if not self.drawing:
            return
            
        self.drawing = False
        end_x = event.x
        end_y = event.y
        
        # Ensure coordinates are correct (x1 < x2, y1 < y2)
        x1, x2 = sorted([self.start_x, end_x])
        y1, y2 = sorted([self.start_y, end_y])
        
        # Skip too small bboxes
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            self.start_x, self.start_y = -1, -1
            self.update_display()
            return
        
        # Convert to YOLO format (normalized coordinates)
        display_h, display_w = self.image_handler.display_image.shape[:2]
        
        x_center = round(((x1 + x2) / 2) / display_w, 5)
        y_center = round(((y1 + y2) / 2) / display_h, 5)
        width = round((x2 - x1) / display_w, 5)
        height = round((y2 - y1) / display_h, 5)
        
        # Add new annotation
        self.annotation_handler.save_to_history()
        self.annotation_handler.add_annotation(x_center, y_center, width, height)
        
        # Update annotation list
        self.master.master.annotation_list.update_list()  # Ensure the list is updated
        
        self.start_x, self.start_y = -1, -1
        self.update_display()