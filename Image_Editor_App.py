import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np

class CropResizeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Image Editor")
        self.root.geometry("1150x720")
        self.root.minsize(1100, 650)

        style = ttk.Style()
        style.configure('TButton', font=('Segoe UI', 10), padding=6)

        self.cv_image = None
        self.processed_image = None
        self.original_image = None  # To reset

        self.photo_original = None
        self.photo_cropped = None

        self.crop_coords_from_mouse = False

        self.undo_stack = []
        self.redo_stack = []

        self.display_img_width = 0
        self.display_img_height = 0

        self.aspect_ratio_locked = tk.BooleanVar(value=True)

        self.create_widgets()
        self.bind_shortcuts()

        self.root.update()
        self.root.focus_force()

    def create_widgets(self):
        # Left control frame
        self.control_frame = ttk.Frame(self.root, padding=12, relief=tk.GROOVE)
        self.control_frame.grid(row=0, column=0, sticky="ns", padx=6, pady=6)

        # Right image frame
        self.image_frame = ttk.Frame(self.root, padding=6, relief=tk.SUNKEN)
        self.image_frame.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Actions
        action_frame = ttk.LabelFrame(self.control_frame, text="Actions", padding=8)
        action_frame.grid(row=0, column=0, sticky="ew", pady=(0,12))

        self.load_btn = ttk.Button(action_frame, text="Load Image", command=self.load_image)
        self.load_btn.grid(row=0, column=0, pady=4, sticky="ew")

        self.save_btn = ttk.Button(action_frame, text="Save Cropped Image", command=self.save_cropped_image, state=tk.DISABLED)
        self.save_btn.grid(row=1, column=0, pady=4, sticky="ew")

        self.reset_btn = ttk.Button(action_frame, text="Reset All", command=self.reset_all, state=tk.DISABLED)
        self.reset_btn.grid(row=2, column=0, pady=4, sticky="ew")

        self.exit_btn = ttk.Button(action_frame, text="Exit", command=self.root.destroy)
        self.exit_btn.grid(row=3, column=0, pady=4, sticky="ew")

        self.help_btn = ttk.Button(action_frame, text="Help / Shortcuts", command=self.show_help)
        self.help_btn.grid(row=4, column=0, pady=4, sticky="ew")

        # Filters frame
        filter_frame = ttk.LabelFrame(self.control_frame, text="Basic Filters", padding=8)
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0,12))

        self.grayscale_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="Grayscale", variable=self.grayscale_var, command=self.apply_filters).grid(row=0, column=0, sticky="w", pady=2)

        self.sepia_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="Sepia", variable=self.sepia_var, command=self.apply_filters).grid(row=1, column=0, sticky="w", pady=2)

        self.invert_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="Invert Colors", variable=self.invert_var, command=self.apply_filters).grid(row=2, column=0, sticky="w", pady=2)

        # Advanced filters frame
        adv_filter_frame = ttk.LabelFrame(self.control_frame, text="Advanced Filters", padding=8)
        adv_filter_frame.grid(row=2, column=0, sticky="ew", pady=(0,12))

        self.sketch_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv_filter_frame, text="Sketch Effect", variable=self.sketch_var, command=self.apply_filters).grid(row=0, column=0, sticky="w", pady=2)

        self.cartoon_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv_filter_frame, text="Cartoon Effect", variable=self.cartoon_var, command=self.apply_filters).grid(row=1, column=0, sticky="w", pady=2)

        self.sharpen_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv_filter_frame, text="Sharpen", variable=self.sharpen_var, command=self.apply_filters).grid(row=2, column=0, sticky="w", pady=2)

        # Color adjustments frame
        color_frame = ttk.LabelFrame(self.control_frame, text="Color Adjustments (HSV)", padding=8)
        color_frame.grid(row=3, column=0, sticky="ew", pady=(0,12))

        ttk.Label(color_frame, text="Hue Shift").grid(row=0, column=0, sticky='w')
        self.hue_var = tk.IntVar(value=0)
        ttk.Scale(color_frame, from_=-180, to=180, orient=tk.HORIZONTAL, variable=self.hue_var, command=self.apply_filters, length=180).grid(row=0, column=1, pady=2)

        ttk.Label(color_frame, text="Saturation").grid(row=1, column=0, sticky='w')
        self.sat_var = tk.IntVar(value=0)
        ttk.Scale(color_frame, from_=-100, to=100, orient=tk.HORIZONTAL, variable=self.sat_var, command=self.apply_filters, length=180).grid(row=1, column=1, pady=2)

        ttk.Label(color_frame, text="Value").grid(row=2, column=0, sticky='w')
        self.val_var = tk.IntVar(value=0)
        ttk.Scale(color_frame, from_=-100, to=100, orient=tk.HORIZONTAL, variable=self.val_var, command=self.apply_filters, length=180).grid(row=2, column=1, pady=2)

        # Brightness & Contrast
        bc_frame = ttk.LabelFrame(self.control_frame, text="Brightness & Contrast", padding=8)
        bc_frame.grid(row=4, column=0, sticky="ew", pady=(0,12))

        ttk.Label(bc_frame, text="Brightness").grid(row=0, column=0, sticky='w')
        self.brightness_var = tk.IntVar(value=0)
        ttk.Scale(bc_frame, from_=-100, to=100, orient=tk.HORIZONTAL, variable=self.brightness_var, command=self.apply_filters, length=180).grid(row=0, column=1, pady=2)

        ttk.Label(bc_frame, text="Contrast").grid(row=1, column=0, sticky='w')
        self.contrast_var = tk.DoubleVar(value=1.0)
        ttk.Scale(bc_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL, variable=self.contrast_var, command=self.apply_filters, length=180).grid(row=1, column=1, pady=2)

        # Blur
        blur_frame = ttk.LabelFrame(self.control_frame, text="Blur", padding=8)
        blur_frame.grid(row=5, column=0, sticky="ew", pady=(0,12))

        self.blur_var = tk.IntVar(value=0)
        ttk.Scale(blur_frame, from_=0, to=20, orient=tk.HORIZONTAL, variable=self.blur_var, command=self.apply_filters, length=200).pack()

        # Rotation
        rotate_frame = ttk.LabelFrame(self.control_frame, text="Rotation", padding=8)
        rotate_frame.grid(row=6, column=0, sticky="ew", pady=(0,12))

        self.rotation_var = tk.IntVar(value=0)
        ttk.Scale(rotate_frame, from_=-180, to=180, orient=tk.HORIZONTAL, variable=self.rotation_var, command=self.apply_filters, length=180).pack()

        # Resize frame - by % or by Width/Height with lock toggle
        resize_frame = ttk.LabelFrame(self.control_frame, text="Resize Cropped Image", padding=8)
        resize_frame.grid(row=7, column=0, sticky="ew", pady=(0,12))

        ttk.Label(resize_frame, text="Resize %").grid(row=0, column=0, sticky="w")
        self.resize_var = tk.IntVar(value=100)
        ttk.Scale(resize_frame, from_=10, to=200, orient=tk.HORIZONTAL, variable=self.resize_var, command=self.resize_updated, length=180).grid(row=0, column=1, pady=2)

        ttk.Label(resize_frame, text="Width").grid(row=1, column=0, sticky="w")
        self.width_var = tk.IntVar(value=300)
        self.width_entry = ttk.Entry(resize_frame, textvariable=self.width_var, width=8)
        self.width_entry.grid(row=1, column=1, sticky="w", pady=2)
        self.width_entry.bind("<Return>", self.resize_by_dimensions)

        ttk.Label(resize_frame, text="Height").grid(row=2, column=0, sticky="w")
        self.height_var = tk.IntVar(value=300)
        self.height_entry = ttk.Entry(resize_frame, textvariable=self.height_var, width=8)
        self.height_entry.grid(row=2, column=1, sticky="w", pady=2)
        self.height_entry.bind("<Return>", self.resize_by_dimensions)

        self.lock_aspect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(resize_frame, text="Lock Aspect Ratio", variable=self.lock_aspect_var).grid(row=3, column=0, columnspan=2, sticky="w")

        # Image frames right side (horizontal split)
        self.orig_frame = ttk.Frame(self.image_frame, relief=tk.SUNKEN)
        self.orig_frame.grid(row=0, column=0, sticky="nsew", padx=(6,3), pady=6)

        self.crop_frame = ttk.Frame(self.image_frame, relief=tk.SUNKEN)
        self.crop_frame.grid(row=0, column=1, sticky="nsew", padx=(3,6), pady=6)

        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(1, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)

        self.orig_canvas = tk.Canvas(self.orig_frame, bg='gray')
        self.orig_canvas.pack(fill=tk.BOTH, expand=True)
        self.orig_canvas.create_text(225, 275, text="Original Image\n(Drag to Crop)", fill="white", font=("Arial", 16), tags="placeholder")

        self.crop_canvas = tk.Canvas(self.crop_frame, bg='lightgray')
        self.crop_canvas.pack(fill=tk.BOTH, expand=True)
        self.crop_canvas.create_text(225, 275, text="Cropped + Resized", fill="black", font=("Arial", 14), tags="placeholder")

        self.orig_canvas.bind("<ButtonPress-1>", self.mouse_crop_start)
        self.orig_canvas.bind("<B1-Motion>", self.mouse_crop_drag)
        self.orig_canvas.bind("<ButtonRelease-1>", self.mouse_crop_end)

        self.mouse_start_x = None
        self.mouse_start_y = None
        self.mouse_rect = None

        self.crop_x1 = 0
        self.crop_y1 = 0
        self.crop_x2 = 0
        self.crop_y2 = 0

    def bind_shortcuts(self):
        self.root.bind_all("<Control-o>", self.load_image_event)
        self.root.bind_all("<Control-s>", self.save_cropped_image_event)
        self.root.bind_all("<Control-z>", self.undo_crop_event)
        self.root.bind_all("<Control-y>", self.redo_crop_event)

    def load_image_event(self, event): self.load_image()
    def save_cropped_image_event(self, event): self.save_cropped_image()
    def undo_crop_event(self, event): self.undo_crop()
    def redo_crop_event(self, event): self.redo_crop()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if not file_path:
            return

        self.cv_image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
        self.original_image = self.cv_image.copy()
        self.undo_stack.clear()
        self.redo_stack.clear()

        self.grayscale_var.set(False)
        self.sepia_var.set(False)
        self.invert_var.set(False)
        self.sketch_var.set(False)
        self.cartoon_var.set(False)
        self.sharpen_var.set(False)
        self.hue_var.set(0)
        self.sat_var.set(0)
        self.val_var.set(0)
        self.brightness_var.set(0)
        self.contrast_var.set(1.0)
        self.blur_var.set(0)
        self.rotation_var.set(0)

        h, w = self.cv_image.shape[:2]

        self.crop_x1 = 0
        self.crop_y1 = 0
        self.crop_x2 = w
        self.crop_y2 = h

        self.resize_var.set(100)
        self.width_var.set(w)
        self.height_var.set(h)

        self.save_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.NORMAL)
        self.crop_coords_from_mouse = False

        self.apply_filters()

    def reset_all(self):
        if self.original_image is None:
            return
        self.cv_image = self.original_image.copy()
        self.grayscale_var.set(False)
        self.sepia_var.set(False)
        self.invert_var.set(False)
        self.sketch_var.set(False)
        self.cartoon_var.set(False)
        self.sharpen_var.set(False)
        self.hue_var.set(0)
        self.sat_var.set(0)
        self.val_var.set(0)
        self.brightness_var.set(0)
        self.contrast_var.set(1.0)
        self.blur_var.set(0)
        self.rotation_var.set(0)

        h, w = self.cv_image.shape[:2]
        self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2 = 0, 0, w, h
        self.resize_var.set(100)
        self.width_var.set(w)
        self.height_var.set(h)

        self.apply_filters()

    def show_original_image(self):
        if self.processed_image is None:
            return
        img_pil = Image.fromarray(self.processed_image)
        width = self.orig_canvas.winfo_width()
        height = self.orig_canvas.winfo_height()
        if width < 10 or height < 10:
            width, height = 450, 550
        img_pil.thumbnail((width, height), Image.Resampling.LANCZOS)
        self.display_img_width, self.display_img_height = img_pil.size
        self.photo_original = ImageTk.PhotoImage(img_pil)
        self.orig_canvas.delete("all")
        self.orig_canvas.config(width=self.display_img_width, height=self.display_img_height)
        self.orig_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_original)

    def apply_filters(self, event=None, update=True):
        if self.cv_image is None:
            return

        img = self.cv_image.copy()

        # Rotation
        angle = self.rotation_var.get()
        if angle != 0:
            h, w = img.shape[:2]
            M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1)
            img = cv2.warpAffine(img, M, (w, h))

        # HSV adjustment
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        h, s, v = cv2.split(hsv)
        h = (h + self.hue_var.get()) % 180
        s = np.clip(s + self.sat_var.get() * 2.55, 0, 255)
        v = np.clip(v + self.val_var.get() * 2.55, 0, 255)
        hsv = cv2.merge([h, s, v]).astype(np.uint8)
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        # Brightness and contrast
        brightness = self.brightness_var.get()
        contrast = self.contrast_var.get()
        img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)

        # Filters
        if self.grayscale_var.get():
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        if self.sepia_var.get():
            kernel = np.array([[0.393, 0.769, 0.189],
                               [0.349, 0.686, 0.168],
                               [0.272, 0.534, 0.131]])
            img = cv2.transform(img, kernel)
            img = np.clip(img, 0, 255).astype(np.uint8)

        if self.invert_var.get():
            img = 255 - img

        if self.sharpen_var.get():
            kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
            img = cv2.filter2D(img, -1, kernel)

        if self.blur_var.get() > 0:
            ksize = self.blur_var.get()
            if ksize % 2 == 0:
                ksize += 1
            img = cv2.GaussianBlur(img, (ksize, ksize), 0)

        if self.sketch_var.get():
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            inv = 255 - gray
            blur = cv2.GaussianBlur(inv, (21,21), 0)
            inv_blur = 255 - blur
            sketch = cv2.divide(gray, inv_blur, scale=256.0)
            img = cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)

        if self.cartoon_var.get():
            # Simple cartoon effect
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            img_blur = cv2.medianBlur(img_gray, 7)
            edges = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                          cv2.THRESH_BINARY, 9, 2)
            color = cv2.bilateralFilter(img, 9, 300, 300)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            img = cartoon

        self.processed_image = img
        if update:
            self.show_original_image()
            self.update_cropped_image()

    def resize_updated(self, event=None):
        scale = self.resize_var.get()
        if self.processed_image is None:
            return
        # Update width and height entries maintaining aspect ratio if locked
        x1, x2 = sorted((self.crop_x1, self.crop_x2))
        y1, y2 = sorted((self.crop_y1, self.crop_y2))
        w = x2 - x1
        h = y2 - y1
        if w <= 0 or h <= 0:
            return
        new_w = max(1, int(w * scale / 100))
        new_h = max(1, int(h * scale / 100))
        if self.aspect_ratio_locked.get():
            aspect = w / h
            if new_w / new_h > aspect:
                new_w = int(new_h * aspect)
            else:
                new_h = int(new_w / aspect)
        self.width_var.set(new_w)
        self.height_var.set(new_h)
        self.update_cropped_image()

    def resize_by_dimensions(self, event=None):
        if self.processed_image is None:
            return
        try:
            new_w = int(self.width_var.get())
            new_h = int(self.height_var.get())
        except Exception:
            return
        if new_w <= 0 or new_h <= 0:
            return
        if self.aspect_ratio_locked.get():
            x1, x2 = sorted((self.crop_x1, self.crop_x2))
            y1, y2 = sorted((self.crop_y1, self.crop_y2))
            w = x2 - x1
            h = y2 - y1
            aspect = w / h if h != 0 else 1
            if new_w / new_h > aspect:
                new_w = int(new_h * aspect)
            else:
                new_h = int(new_w / aspect)
            self.width_var.set(new_w)
            self.height_var.set(new_h)
        scale_w = new_w / (self.crop_x2 - self.crop_x1)
        scale_h = new_h / (self.crop_y2 - self.crop_y1)
        scale = int((scale_w + scale_h) / 2 * 100)
        self.resize_var.set(scale)
        self.update_cropped_image()

    def update_cropped_image(self):
        if self.processed_image is None:
            return
        x1, x2 = sorted((self.crop_x1, self.crop_x2))
        y1, y2 = sorted((self.crop_y1, self.crop_y2))

        h, w = self.processed_image.shape[:2]
        x1 = max(0, min(w - 1, x1))
        x2 = max(0, min(w, x2))
        y1 = max(0, min(h - 1, y1))
        y2 = max(0, min(h, y2))

        if x2 <= x1 or y2 <= y1:
            self.crop_canvas.delete("all")
            self.crop_canvas.create_text(225, 275, text="Invalid crop area", fill="red", font=("Arial", 14))
            return

        cropped = self.processed_image[y1:y2, x1:x2]
        scale = self.resize_var.get()
        new_w = max(1, int(cropped.shape[1] * scale / 100))
        new_h = max(1, int(cropped.shape[0] * scale / 100))

        resized = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_AREA)

        img_pil = Image.fromarray(resized)
        self.photo_cropped = ImageTk.PhotoImage(img_pil)

        self.crop_canvas.delete("all")
        self.crop_canvas.config(width=new_w, height=new_h)
        self.crop_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_cropped)

    def mouse_crop_start(self, event):
        if self.processed_image is None:
            return
        self.crop_coords_from_mouse = True
        self.push_undo()
        self.mouse_start_x = event.x
        self.mouse_start_y = event.y
        if self.mouse_rect:
            self.orig_canvas.delete(self.mouse_rect)
        self.mouse_rect = self.orig_canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red')

    def mouse_crop_drag(self, event):
        if self.processed_image is None or self.mouse_rect is None:
            return
        self.orig_canvas.coords(self.mouse_rect, self.mouse_start_x, self.mouse_start_y, event.x, event.y)

    def mouse_crop_end(self, event):
        if self.processed_image is None or self.mouse_rect is None:
            return

        x1, y1 = self.mouse_start_x, self.mouse_start_y
        x2, y2 = event.x, event.y

        x1 = max(0, min(self.display_img_width, x1))
        x2 = max(0, min(self.display_img_width, x2))
        y1 = max(0, min(self.display_img_height, y1))
        y2 = max(0, min(self.display_img_height, y2))

        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        img_h, img_w = self.processed_image.shape[:2]
        scale_x = img_w / self.display_img_width
        scale_y = img_h / self.display_img_height

        self.crop_x1 = int(x1 * scale_x)
        self.crop_x2 = int(x2 * scale_x)
        self.crop_y1 = int(y1 * scale_y)
        self.crop_y2 = int(y2 * scale_y)

        # Update width and height entries based on crop
        crop_w = self.crop_x2 - self.crop_x1
        crop_h = self.crop_y2 - self.crop_y1
        self.width_var.set(crop_w)
        self.height_var.set(crop_h)
        self.resize_var.set(100)

        self.update_cropped_image()

        self.orig_canvas.delete(self.mouse_rect)
        self.mouse_rect = None

    def push_undo(self):
        state = (
            self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2,
            self.resize_var.get(), self.grayscale_var.get(),
            self.sepia_var.get(), self.invert_var.get(),
            self.sketch_var.get(), self.cartoon_var.get(),
            self.sharpen_var.get(), self.hue_var.get(),
            self.sat_var.get(), self.val_var.get(),
            self.brightness_var.get(), self.contrast_var.get(),
            self.blur_var.get(), self.rotation_var.get(),
            self.width_var.get(), self.height_var.get(),
            self.aspect_ratio_locked.get()
        )
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def undo_crop(self):
        if not self.undo_stack:
            return
        current_state = (
            self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2,
            self.resize_var.get(), self.grayscale_var.get(),
            self.sepia_var.get(), self.invert_var.get(),
            self.sketch_var.get(), self.cartoon_var.get(),
            self.sharpen_var.get(), self.hue_var.get(),
            self.sat_var.get(), self.val_var.get(),
            self.brightness_var.get(), self.contrast_var.get(),
            self.blur_var.get(), self.rotation_var.get(),
            self.width_var.get(), self.height_var.get(),
            self.aspect_ratio_locked.get()
        )
        self.redo_stack.append(current_state)
        last_state = self.undo_stack.pop()
        self.apply_state(last_state)

    def redo_crop(self):
        if not self.redo_stack:
            return
        current_state = (
            self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2,
            self.resize_var.get(), self.grayscale_var.get(),
            self.sepia_var.get(), self.invert_var.get(),
            self.sketch_var.get(), self.cartoon_var.get(),
            self.sharpen_var.get(), self.hue_var.get(),
            self.sat_var.get(), self.val_var.get(),
            self.brightness_var.get(), self.contrast_var.get(),
            self.blur_var.get(), self.rotation_var.get(),
            self.width_var.get(), self.height_var.get(),
            self.aspect_ratio_locked.get()
        )
        self.undo_stack.append(current_state)
        next_state = self.redo_stack.pop()
        self.apply_state(next_state)

    def apply_state(self, state):
        (x1, y1, x2, y2, resize, grayscale, sepia, invert, sketch, cartoon, sharpen,
         hue, sat, val, brightness, contrast, blur, rotation, width, height, aspect_lock) = state
        self.crop_coords_from_mouse = True
        self.crop_x1 = x1
        self.crop_y1 = y1
        self.crop_x2 = x2
        self.crop_y2 = y2
        self.resize_var.set(resize)
        self.grayscale_var.set(grayscale)
        self.sepia_var.set(sepia)
        self.invert_var.set(invert)
        self.sketch_var.set(sketch)
        self.cartoon_var.set(cartoon)
        self.sharpen_var.set(sharpen)
        self.hue_var.set(hue)
        self.sat_var.set(sat)
        self.val_var.set(val)
        self.brightness_var.set(brightness)
        self.contrast_var.set(contrast)
        self.blur_var.set(blur)
        self.rotation_var.set(rotation)
        self.width_var.set(width)
        self.height_var.set(height)
        self.aspect_ratio_locked.set(aspect_lock)
        self.apply_filters()
        self.update_cropped_image()

    def show_help(self):
        help_text = (
            "Keyboard Shortcuts:\n"
            "  Ctrl + O : Load Image\n"
            "  Ctrl + S : Save Cropped Image\n"
            "  Ctrl + Z : Undo\n"
            "  Ctrl + Y : Redo\n"
            "  Ctrl + R : Reset All\n"
            "  Ctrl + Q : Exit\n\n"
            "Instructions:\n"
            " - Load an image.\n"
            " - Crop by dragging a rectangle on the original image.\n"
            " - Use sliders and checkboxes to apply filters and adjustments.\n"
            " - Resize cropped image by % or by Width and Height.\n"
            " - Use Undo/Redo to revert changes.\n"
            " - Save the modified image.\n"
            " - Use Reset to revert all changes to original."
        )
        help_window = tk.Toplevel(self.root)
        help_window.title("Help / Instructions")
        help_window.geometry("520x380")
        tk.Label(help_window, text=help_text, justify=tk.LEFT, padx=10, pady=10).pack(fill=tk.BOTH, expand=True)
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=5)

    def save_cropped_image(self):
        if self.processed_image is None:
            messagebox.showwarning("No Image", "Load and crop an image first!")
            return

        x1, x2 = sorted((self.crop_x1, self.crop_x2))
        y1, y2 = sorted((self.crop_y1, self.crop_y2))

        cropped = self.processed_image[y1:y2, x1:x2]
        if cropped.size == 0:
            messagebox.showwarning("Invalid Crop", "Crop area is invalid!")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg *.jpeg")])
        if not file_path:
            return

        scale = self.resize_var.get()
        new_w = max(1, int(cropped.shape[1] * scale / 100))
        new_h = max(1, int(cropped.shape[0] * scale / 100))
        resized = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_AREA)

        cv2.imwrite(file_path, cv2.cvtColor(resized, cv2.COLOR_RGB2BGR))
        messagebox.showinfo("Saved", f"Image saved to {file_path}")

    # Keyboard shortcuts
    def on_keypress(self, event):
        if event.state & 0x4:  # Control key pressed
            if event.keysym.lower() == 'o':
                self.load_image()
            elif event.keysym.lower() == 's':
                self.save_cropped_image()
            elif event.keysym.lower() == 'z':
                self.undo_crop()
            elif event.keysym.lower() == 'y':
                self.redo_crop()
            elif event.keysym.lower() == 'r':
                self.reset_all()
            elif event.keysym.lower() == 'q':
                self.root.destroy()

    # Mouse crop functions and undo/redo unchanged from before

    # Insert previous mouse_crop_start, mouse_crop_drag, mouse_crop_end, push_undo, undo_crop, redo_crop, apply_state here unchanged
    def mouse_crop_start(self, event):
        if self.processed_image is None:
            return
        self.crop_coords_from_mouse = True
        self.push_undo()
        self.mouse_start_x = event.x
        self.mouse_start_y = event.y
        if self.mouse_rect:
            self.orig_canvas.delete(self.mouse_rect)
        self.mouse_rect = self.orig_canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red')

    def mouse_crop_drag(self, event):
        if self.processed_image is None or self.mouse_rect is None:
            return
        self.orig_canvas.coords(self.mouse_rect, self.mouse_start_x, self.mouse_start_y, event.x, event.y)

    def mouse_crop_end(self, event):
        if self.processed_image is None or self.mouse_rect is None:
            return

        x1, y1 = self.mouse_start_x, self.mouse_start_y
        x2, y2 = event.x, event.y

        x1 = max(0, min(self.display_img_width, x1))
        x2 = max(0, min(self.display_img_width, x2))
        y1 = max(0, min(self.display_img_height, y1))
        y2 = max(0, min(self.display_img_height, y2))

        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        img_h, img_w = self.processed_image.shape[:2]
        scale_x = img_w / self.display_img_width
        scale_y = img_h / self.display_img_height

        self.crop_x1 = int(x1 * scale_x)
        self.crop_x2 = int(x2 * scale_x)
        self.crop_y1 = int(y1 * scale_y)
        self.crop_y2 = int(y2 * scale_y)

        # Update width and height entries based on crop
        crop_w = self.crop_x2 - self.crop_x1
        crop_h = self.crop_y2 - self.crop_y1
        self.width_var.set(crop_w)
        self.height_var.set(crop_h)
        self.resize_var.set(100)

        self.update_cropped_image()

        self.orig_canvas.delete(self.mouse_rect)
        self.mouse_rect = None

    def push_undo(self):
        state = (
            self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2,
            self.resize_var.get(), self.grayscale_var.get(),
            self.sepia_var.get(), self.invert_var.get(),
            self.sketch_var.get(), self.cartoon_var.get(),
            self.sharpen_var.get(), self.hue_var.get(),
            self.sat_var.get(), self.val_var.get(),
            self.brightness_var.get(), self.contrast_var.get(),
            self.blur_var.get(), self.rotation_var.get(),
            self.width_var.get(), self.height_var.get(),
            self.aspect_ratio_locked.get()
        )
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def undo_crop(self):
        if not self.undo_stack:
            return
        current_state = (
            self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2,
            self.resize_var.get(), self.grayscale_var.get(),
            self.sepia_var.get(), self.invert_var.get(),
            self.sketch_var.get(), self.cartoon_var.get(),
            self.sharpen_var.get(), self.hue_var.get(),
            self.sat_var.get(), self.val_var.get(),
            self.brightness_var.get(), self.contrast_var.get(),
            self.blur_var.get(), self.rotation_var.get(),
            self.width_var.get(), self.height_var.get(),
            self.aspect_ratio_locked.get()
        )
        self.redo_stack.append(current_state)
        last_state = self.undo_stack.pop()
        self.apply_state(last_state)

    def redo_crop(self):
        if not self.redo_stack:
            return
        current_state = (
            self.crop_x1, self.crop_y1, self.crop_x2, self.crop_y2,
            self.resize_var.get(), self.grayscale_var.get(),
            self.sepia_var.get(), self.invert_var.get(),
            self.sketch_var.get(), self.cartoon_var.get(),
            self.sharpen_var.get(), self.hue_var.get(),
            self.sat_var.get(), self.val_var.get(),
            self.brightness_var.get(), self.contrast_var.get(),
            self.blur_var.get(), self.rotation_var.get(),
            self.width_var.get(), self.height_var.get(),
            self.aspect_ratio_locked.get()
        )
        self.undo_stack.append(current_state)
        next_state = self.redo_stack.pop()
        self.apply_state(next_state)

if __name__ == "__main__":
    root = tk.Tk()
    app = CropResizeApp(root)
    root.mainloop()