from gui.main_window import YOLOAnnotationApp
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = YOLOAnnotationApp(root)
    root.mainloop()