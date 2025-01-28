import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")
        self.root.geometry("1000x600")

        self.image = None
        self.temp_image = None
        self.cropped_image = None
        self.rect_start = None
        self.rect_end = None
        self.crop_rect_id = None
        self.undo_stack = []

        self.create_widgets()
        self.bind_shortcuts()

    def create_widgets(self):
        # Frames for layout
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Original Image Canvas
        self.canvas_original = tk.Canvas(self.top_frame, bg="gray", width=500, height=400)
        self.canvas_original.pack(side=tk.LEFT, padx=10, pady=10)

        # Cropped Image Canvas
        self.canvas_cropped = tk.Canvas(self.top_frame, bg="lightgray", width=500, height=400)
        self.canvas_cropped.pack(side=tk.RIGHT, padx=10, pady=10)

        # Buttons
        self.load_btn = tk.Button(self.bottom_frame, text="Load Image", command=self.load_image)
        self.load_btn.pack(side=tk.LEFT, padx=10)

        self.save_btn = tk.Button(self.bottom_frame, text="Save Image", command=self.save_image, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=10)

        self.undo_btn = tk.Button(self.bottom_frame, text="Undo", command=self.undo, state=tk.DISABLED)
        self.undo_btn.pack(side=tk.LEFT, padx=10)

        self.grayscale_btn = tk.Button(self.bottom_frame, text="Grayscale", command=self.apply_grayscale, state=tk.DISABLED)
        self.grayscale_btn.pack(side=tk.LEFT, padx=10)

        self.blur_btn = tk.Button(self.bottom_frame, text="Blur", command=self.apply_blur, state=tk.DISABLED)
        self.blur_btn.pack(side=tk.LEFT, padx=10)

        self.edge_btn = tk.Button(self.bottom_frame, text="Edge Detection", command=self.apply_edge_detection, state=tk.DISABLED)
        self.edge_btn.pack(side=tk.LEFT, padx=10)

        self.resize_slider = tk.Scale(
            self.bottom_frame, from_=10, to=100, orient=tk.HORIZONTAL, label="Resize %", command=self.resize_image
        )
        self.resize_slider.set(100)
        self.resize_slider.pack(side=tk.RIGHT, padx=10)

        self.canvas_original.bind("<Button-1>", self.start_crop)
        self.canvas_original.bind("<B1-Motion>", self.update_crop)
        self.canvas_original.bind("<ButtonRelease-1>", self.finish_crop)

    def bind_shortcuts(self):
        self.root.bind("<Control-o>", lambda event: self.load_image())
        self.root.bind("<Control-s>", lambda event: self.save_image())
        self.root.bind("<Control-z>", lambda event: self.undo())

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")]
        )
        if file_path:
            self.image = cv2.imread(file_path)
            self.cropped_image = None
            self.display_image_on_canvas(self.image, self.canvas_original)
            self.canvas_cropped.delete("all")
            self.undo_stack = []
            self.save_btn.config(state=tk.DISABLED)
            self.undo_btn.config(state=tk.DISABLED)
            self.grayscale_btn.config(state=tk.NORMAL)
            self.blur_btn.config(state=tk.NORMAL)
            self.edge_btn.config(state=tk.NORMAL)

    def display_image_on_canvas(self, img, canvas):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil = img_pil.resize((500, 400), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_pil)
        canvas.image = img_tk  
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

    def start_crop(self, event):
        self.rect_start = (event.x, event.y)

    def update_crop(self, event):
        if self.crop_rect_id:
            self.canvas_original.delete(self.crop_rect_id)
        self.rect_end = (event.x, event.y)
        self.crop_rect_id = self.canvas_original.create_rectangle(
            self.rect_start[0], self.rect_start[1], event.x, event.y, outline="red", dash=(4, 2)
        )

    def finish_crop(self, event):
        x1, y1 = self.rect_start
        x2, y2 = self.rect_end
        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))

        if self.image is not None:
            h, w, _ = self.image.shape
            scale_x = w / 500
            scale_y = h / 400

            x1, x2 = int(x1 * scale_x), int(x2 * scale_x)
            y1, y2 = int(y1 * scale_y), int(y2 * scale_y)

          
            self.cropped_image = self.image[y1:y2, x1:x2].copy()

        
            self.display_image_on_canvas(self.cropped_image, self.canvas_cropped)

            self.save_btn.config(state=tk.NORMAL)

         
            self.undo_stack.append(self.image.copy())
            self.undo_btn.config(state=tk.NORMAL)

    def resize_image(self, value):
        if self.cropped_image is not None:
            scale = int(value) / 100
            width = int(self.cropped_image.shape[1] * scale)
            height = int(self.cropped_image.shape[0] * scale)
            resized = cv2.resize(self.cropped_image, (width, height), interpolation=cv2.INTER_LINEAR)
            self.display_image_on_canvas(resized, self.canvas_cropped)

    def save_image(self):
        if self.cropped_image is not None:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
            )
            if save_path:
                cv2.imwrite(save_path, self.cropped_image)
                messagebox.showinfo("Success", "Image saved successfully!")

    def undo(self):
        if self.undo_stack:
            last_state = self.undo_stack.pop()
            self.image = last_state
            self.cropped_image = None
            self.display_image_on_canvas(self.image, self.canvas_original)
            self.canvas_cropped.delete("all")
            if not self.undo_stack:
                self.undo_btn.config(state=tk.DISABLED)

    def apply_grayscale(self):
        target_image = self.cropped_image if self.cropped_image is not None else self.image
        if target_image is not None:
            self.undo_stack.append(target_image.copy())
            target_image = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)
            target_image = cv2.cvtColor(target_image, cv2.COLOR_GRAY2BGR) 
            if self.cropped_image is not None:
                self.cropped_image = target_image
                self.display_image_on_canvas(self.cropped_image, self.canvas_cropped)
            else:
                self.image = target_image
                self.display_image_on_canvas(self.image, self.canvas_original)
            self.undo_btn.config(state=tk.NORMAL)

    def apply_blur(self):
        target_image = self.cropped_image if self.cropped_image is not None else self.image
        if target_image is not None:
            self.undo_stack.append(target_image.copy())
            target_image = cv2.GaussianBlur(target_image, (15, 15), 0)
            if self.cropped_image is not None:
                self.cropped_image = target_image
                self.display_image_on_canvas(self.cropped_image, self.canvas_cropped)
            else:
                self.image = target_image
                self.display_image_on_canvas(self.image, self.canvas_original)
            self.undo_btn.config(state=tk.NORMAL)

    def apply_edge_detection(self):
        target_image = self.cropped_image if self.cropped_image is not None else self.image
        if target_image is not None:
            self.undo_stack.append(target_image.copy())
            gray = cv2.cvtColor(target_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            target_image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)  
            if self.cropped_image is not None:
                self.cropped_image = target_image
                self.display_image_on_canvas(self.cropped_image, self.canvas_cropped)
            else:
                self.image = target_image
                self.display_image_on_canvas(self.image, self.canvas_original)
            self.undo_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditor(root)
    root.mainloop()
