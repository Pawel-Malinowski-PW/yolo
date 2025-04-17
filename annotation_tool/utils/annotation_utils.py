import os

class AnnotationHandler:
    def __init__(self):
        self.annotations = []
        self.annotation_history = []
        self.class_name = "object"
        
    def load_class_name(self):
        if os.path.exists("classes.txt"):
            with open("classes.txt", "r") as f:
                lines = [line.strip() for line in f.readlines()]
                if lines:
                    self.class_name = lines[0]
                    return self.class_name
        return None
        
    def save_class_name(self, class_name):
        self.class_name = class_name
        with open("classes.txt", "w") as f:
            f.write(f"{self.class_name}\n")
            
    def load_annotations(self, image_path):
        annotation_path = os.path.splitext(image_path)[0] + ".txt"
        self.annotations = []
        
        if os.path.exists(annotation_path):
            with open(annotation_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        class_id, x_center, y_center, width, height = map(float, parts)
                        self.annotations.append({
                            "class_id": int(class_id),
                            "x_center": x_center,
                            "y_center": y_center,
                            "width": width,
                            "height": height
                        })
        return self.annotations
        
    def save_annotations(self, image_path):
        if not image_path:
            return False
            
        annotation_path = os.path.splitext(image_path)[0] + ".txt"
        with open(annotation_path, "w") as f:
            for ann in self.annotations:
                f.write(f"{ann['class_id']} {ann['x_center']} {ann['y_center']} {ann['width']} {ann['height']}\n")
        return True
        
    def add_annotation(self, x_center, y_center, width, height, class_id=0):
        self.annotations.append({
            "class_id": class_id,
            "x_center": x_center,
            "y_center": y_center,
            "width": width,
            "height": height
        })
        
    def delete_annotation(self, index):
        if 0 <= index < len(self.annotations):
            del self.annotations[index]
            return True
        return False
        
    def save_to_history(self):
        self.annotation_history.append([anno.copy() for anno in self.annotations])
        
    def undo(self):
        if len(self.annotation_history) > 1:
            self.annotation_history.pop()
            self.annotations = [anno.copy() for anno in self.annotation_history[-1]]
            return True
        return False