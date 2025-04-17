import os
import cv2
import numpy as np
from PIL import Image, ImageTk

class ImageHandler:
    def __init__(self, max_display_width=1500, max_display_height=900):
        self.max_display_width = max_display_width
        self.max_display_height = max_display_height
        self.original_image = None
        self.display_image = None
        self.scale_factor = 1.0
        self.image_path = ""
        
    def load_image(self, image_path):
        self.image_path = image_path
        self.original_image = cv2.imread(image_path)
        self.scale_image_to_fit()
        return self.display_image
        
    def scale_image_to_fit(self):
        if self.original_image is None:
            return
            
        h, w = self.original_image.shape[:2]
        
        # Calculate scale factor
        width_ratio = self.max_display_width / w
        height_ratio = self.max_display_height / h
        self.scale_factor = min(width_ratio, height_ratio)
        
        # Resize image
        new_width = int(w * self.scale_factor)
        new_height = int(h * self.scale_factor)
        self.display_image = cv2.resize(self.original_image, (new_width, new_height))
        
        return new_width, new_height
        
    def get_tk_image(self, image=None):
        if image is None:
            if self.display_image is None:
                return None
            image = self.display_image
            
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(image)
        return ImageTk.PhotoImage(img_pil)
        
    def get_original_dimensions(self):
        if self.original_image is None:
            return 0, 0
        return self.original_image.shape[1], self.original_image.shape[0]