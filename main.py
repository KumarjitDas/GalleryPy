import argparse
import os
import platform
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
from tkinter import filedialog
from PIL import Image, ImageTk


class App:
    APP_WIDTH = 640
    APP_HEIGHT = 400
    APP_NAME = 'GalleryPy'
    APP_GEOMETRY = str(APP_WIDTH) + 'x' + str(APP_HEIGHT)

    APP_MIN_WIDTH = 16 * 20

    APP_RESOURCES_PATH = os.path.abspath('resources/')
    APP_IMAGES_PATH = os.path.join(APP_RESOURCES_PATH, 'images')

    APP_SUPPORTED_IMAGE_FILE_EXTENSIONS = [
        'bmp',  # BMP
        'dib',  # BMP
        'eps',  # EPS
        'gif',  # GIF
        'icns',  # ICNS
        'ico',  # ICO
        'im',  # IM
        'jpeg',  # JPEG
        'jpe',  # JPEG
        'jpg',  # JPEG
        'msp',  # MSP
        'pcx',  # PCX
        'png',  # PNG
        'ppm',  # PPM
        'pgm',  # PPM
        'pbm',  # PPM
        'pnm',  # PPM
        'sgi',  # SGI
        'rgb',  # SGI
        'bw',  # SGI
        'spider',  # SPIDER
        'tga',  # TGA
        'tif',  # TIFF
        'tiff',  # TIFF
        'webp',  # WEBP
        'xbm',  # XBM
        'pdf',  # PDF
        'psd',  # PSD
        'fits',  # FITS
        'fit',  # FITS
        'pcd',  # PCD
        'dds',  # DDS
    ]

    EMPTY_FOLDER_IMAGE_SIZE_MIN = 60
    EMPTY_FOLDER_IMAGE_SIZE_MAX = 120

    EMPTY_FOLDER_LABEL_FONT_SIZE_MIN = 8
    EMPTY_FOLDER_LABEL_FONT_SIZE_MAX = 11

    def __init__(self, arguments):
        if arguments is None:
            arguments = {
                'image_file': None,
                'images_dir': None,
                'verbose': False,
                'config': None
            }

        # Global variables
        self.cmd = arguments
        self.root = tk.Tk()
        self.root_style = ttk.Style()
        self.container = tk.Frame(master=self.root)
        self.windowing_system = self.root.tk.call('tk', 'windowingsystem')
        self.pages = {}
        self.current_page = None
        self.page_items = {}
        self.frames = {}
        self.canvases = {}
        self.labels = {}
        self.fonts = {}
        self.images = {}
        self.photos = {}
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.app_width = self.root.winfo_width()
        self.app_height = self.root.winfo_height()
        self.current_image_width = 0
        self.current_image_height = 0

        self.dialog_filetypes = (
            ('Image Files', ' '.join([f'*.{ext}' for ext in self.APP_SUPPORTED_IMAGE_FILE_EXTENSIONS])),
        )

        self.current_image_file_path = None

    def init_app(self):
        self.set_min_width_height()
        self.apply_platform_styles()
        self.create_page_home()
        self.create_page_img()
        self.create_page_img_error()
        self.create_page_dirs_files()

        self.root.title(self.APP_NAME)
        self.root.geometry(self.APP_GEOMETRY)

        self.root.bind('<Unmap>', self.on_minimize)
        self.root.bind('<Map>', self.on_restore)
        self.root.bind('<Configure>', self.on_configure)

        self.container.pack(side=tk.TOP, anchor=tk.N, fill=tk.BOTH, expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def set_min_width_height(self):
        min_width = self.APP_MIN_WIDTH

        if self.screen_width < min_width:
            min_width = self.screen_width

        min_height = (min_width // 16) * 10  # 16:10 ratio

        if self.screen_height < min_height:
            min_height = self.screen_height

        self.root.minsize(width=min_width, height=min_height)

    def apply_platform_styles(self):
        if self.windowing_system == 'aqua':
            # macOS specific styling
            self.root_style.theme_use('clam')
            self.root_style.configure('TButton', foreground='blue', font=('Helvetica', 12))
            self.root_style.configure('TLabel', foreground='dark green', font=('Helvetica', 14))
        elif self.windowing_system == 'win32':
            # Windows specific styling
            self.root_style.theme_use('default')
            self.root_style.configure('TButton', foreground='dark red', font=('Arial', 12, 'bold'))
            self.root_style.configure('TLabel', foreground='purple', font=('Arial', 14, 'italic'))
        elif self.windowing_system == 'x11':
            # Linux specific styling
            self.root_style.theme_use('alt')
            self.root_style.configure('TButton', foreground='dark blue', font=('Courier', 12))
            self.root_style.configure('TLabel', foreground='brown', font=('Courier', 14))
        else:
            # Default styling for other systems
            self.root_style.theme_use('default')
            self.root_style.configure('TButton', foreground='black', font=('TkDefaultFont', 12))
            self.root_style.configure('TLabel', foreground='black', font=('TkDefaultFont', 14))

    def create_page_home(self):
        frame = tk.Frame(master=self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        center_frame = ttk.Frame(master=frame, width=50, height=50)
        center_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        empty_folder_canvas = tk.Canvas(master=center_frame, cursor='hand2')
        empty_folder_canvas.pack(side=tk.TOP, anchor=tk.S, fill=tk.BOTH, expand=True)

        empty_folder_label_font = Font(family='Helvetica', size=self.EMPTY_FOLDER_LABEL_FONT_SIZE_MIN, weight='bold')

        empty_folder_label = ttk.Label(
            master=center_frame,
            text="No image file/directory have been chosen.\nOpen file  Ctrl + O",
            anchor=tk.CENTER,
            justify=tk.CENTER,
            # wraplength=240,
            padding=2,
            font=empty_folder_label_font,
            cursor='hand2'
        )
        empty_folder_label.pack(side=tk.BOTTOM, anchor=tk.N, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvases['empty_folder'] = empty_folder_canvas
        self.fonts['empty_folder'] = empty_folder_label_font
        self.labels['empty_folder'] = empty_folder_label
        self.page_items['home'] = self.load_page_home_items
        self.pages['home'] = frame
        self.frames['home'] = frame

        empty_folder_canvas.bind('<Button-1>', self.on_home_page_click)
        empty_folder_label.bind('<Button-1>', self.on_home_page_click)
        # frame.bind('<Configure>', self.on_home_page_frame_resize)

    def create_page_img(self):
        frame = tk.Frame(master=self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        main_img_view_canvas = tk.Canvas(master=frame)
        main_img_view_canvas.pack(side=tk.TOP, anchor=tk.N, fill=tk.BOTH, expand=True)

        status_frame = tk.Frame(master=frame, bg='red')
        status_frame.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X, padx=2, pady=2)

        self.canvases['main_img_view'] = main_img_view_canvas
        self.page_items['img'] = self.load_page_img_items
        self.pages['img'] = frame
        self.frames['img'] = frame

    def create_page_img_error(self):
        frame = tk.Frame(self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        label = ttk.Label(frame, text="Could not show image.", background="red", foreground="white")
        label.pack(side=tk.TOP, anchor=tk.N, fill=tk.X, expand=True)

        self.page_items['img_error'] = self.load_page_img_error_items
        self.pages['img_error'] = frame
        self.frames['img_error'] = frame

    def create_page_dirs_files(self):
        frame = tk.Frame(self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        label = ttk.Label(frame, text="Welcome", background="red", foreground="white")
        label.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X, expand=True)

        self.page_items['dirs_files'] = self.load_page_dirs_files_items
        self.pages['dirs_files'] = frame
        self.frames['dirs_files'] = frame

    def show_page(self, page_name):
        frame = self.pages.get(page_name)
        page_item_fn = self.page_items.get(page_name)

        if frame:
            self.current_page = page_name
            frame.tkraise()
            page_item_fn()
        else:
            print(f"Page '{page_name}' does not exist.")

    def load_page_home_items(self):
        image_size = self.EMPTY_FOLDER_IMAGE_SIZE_MAX
        empty_folder_image_path = os.path.join(self.APP_IMAGES_PATH, 'empty-folder.png')
        empty_folder_image = Image.open(empty_folder_image_path).resize((image_size, image_size), Image.Resampling.LANCZOS)
        empty_folder_photo = ImageTk.PhotoImage(empty_folder_image)

        empty_folder_canvas = self.canvases.get('empty_folder')
        empty_folder_canvas.config(width=image_size, height=image_size)

        canvas_width = empty_folder_canvas.winfo_width()
        canvas_height = empty_folder_canvas.winfo_height()
        canvas_width = image_size if canvas_width < image_size else canvas_width
        canvas_height = image_size if canvas_height < image_size else canvas_height

        empty_folder_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            anchor=tk.CENTER,
            image=empty_folder_photo
        )
        empty_folder_canvas.image = empty_folder_photo

        self.canvases['empty_folder'] = empty_folder_canvas
        self.images['empty_folder'] = empty_folder_image
        self.photos['empty_folder'] = empty_folder_photo

        self.resize_home_page_items()

    def load_page_img_items(self):
        if self.current_image_file_path is None:
            self.show_page('img_error')
        else:
            try:
                main_img_view_canvas = self.canvases['main_img_view']
                current_image = Image.open(self.current_image_file_path)
                current_photo = ImageTk.PhotoImage(current_image)

                main_img_view_canvas.create_image(
                    main_img_view_canvas.winfo_width() // 2,
                    main_img_view_canvas.winfo_height() // 2,
                    anchor=tk.CENTER,
                    image=current_photo
                )
                main_img_view_canvas.image = current_photo

                self.current_image_width = current_image.width
                self.current_image_height = current_image.height

                screen_width = self.screen_width * 0.9
                screen_height = self.screen_height * 0.8

                app_width = self.root.winfo_width()
                app_height = self.root.winfo_height()

                if (screen_width >= self.current_image_width > app_width and
                        screen_height >= self.current_image_height > app_height):
                    self.root.geometry(str(self.current_image_width) + 'x' + str(self.current_image_height))
                elif self.current_image_width > app_width or self.current_image_height > app_height:
                    new_size_ratio = self.current_image_width / self.current_image_height
                    new_width = 0
                    new_height = 0

                    if self.current_image_width > self.current_image_height:
                        new_width = int(screen_width)
                        new_height = int(new_width / new_size_ratio)
                    else:
                        new_height = int(screen_height)
                        new_width = int(new_height * new_size_ratio)

                    self.root.geometry(
                        str(new_width if new_width >= self.APP_WIDTH else self.APP_WIDTH) +
                        'x' +
                        str(new_height if new_height >= self.APP_HEIGHT else self.APP_HEIGHT)
                    )

                self.images['current'] = current_image
                self.photos['current'] = current_photo

                self.resize_img_page_items()
            except Exception as e:
                print(e, file=sys.stderr)
                self.show_page('img_error')

    def load_page_img_error_items(self):
        pass

    def load_page_dirs_files_items(self):
        pass

    def resize_home_page_items(self, event=None):
        empty_folder_image = self.images.get('empty_folder')
        empty_folder_photo = self.photos.get('empty_folder')

        if empty_folder_image is None or empty_folder_photo is None:
            return

        empty_folder_canvas = self.canvases['empty_folder']
        empty_folder_font = self.fonts['empty_folder']

        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        desired_size = int(min(root_width, root_height) * 0.2)
        desired_size = max(self.EMPTY_FOLDER_IMAGE_SIZE_MIN, min(desired_size, self.EMPTY_FOLDER_IMAGE_SIZE_MAX))

        desired_font_size = int(min(root_width, root_height) * 0.02)
        desired_font_size = max(self.EMPTY_FOLDER_LABEL_FONT_SIZE_MIN, min(desired_font_size, self.EMPTY_FOLDER_LABEL_FONT_SIZE_MAX))

        empty_folder_canvas.config(width=desired_size, height=desired_size)
        empty_folder_font.config(size=desired_font_size)

        resized_image = empty_folder_image.resize((desired_size, desired_size), Image.Resampling.LANCZOS)
        empty_folder_photo = ImageTk.PhotoImage(resized_image)

        empty_folder_canvas.delete('all')

        empty_folder_canvas.create_image(
            empty_folder_canvas.winfo_width() // 2,
            empty_folder_canvas.winfo_height() // 2,
            image=empty_folder_photo,
            anchor=tk.CENTER
        )

        self.photos['empty_folder'] = empty_folder_photo

    def resize_img_page_items(self, event=None):
        current_image = self.images.get('current')
        current_photo = self.photos.get('current')

        if current_image is None or current_photo is None:
            return

        main_img_view_canvas = self.canvases['main_img_view']
        main_img_view_canvas_width = main_img_view_canvas.winfo_width()
        main_img_view_canvas_height = main_img_view_canvas.winfo_height()

        if main_img_view_canvas_width > 0 and main_img_view_canvas_height > 0:
            current_image_ratio = current_image.width / current_image.height
            main_img_view_canvas_ratio = main_img_view_canvas_width / main_img_view_canvas_height

            if current_image_ratio > main_img_view_canvas_ratio:
                new_width = main_img_view_canvas_width
                new_height = new_width / current_image_ratio
            else:
                new_height = main_img_view_canvas_height
                new_width = new_height * current_image_ratio

            new_width = int(new_width)
            new_height = int(new_height)

            if new_width <= 0 or new_height <= 0:
                return

            new_width = self.current_image_width if new_width >= self.current_image_width else new_width
            new_height = self.current_image_height if new_height >= self.current_image_height else new_height

            resized_current_image = current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_current_photo = ImageTk.PhotoImage(resized_current_image)

            main_img_view_canvas.delete('all')

            center_x = main_img_view_canvas_width // 2
            center_y = main_img_view_canvas_height // 2

            main_img_view_canvas.create_image(center_x, center_y, image=resized_current_photo, anchor=tk.CENTER)

            self.photos['current'] = resized_current_photo

    def on_minimize(self, event):
        if self.root.state() == 'iconic':
            print('Window minimized')

    def on_restore(self, event):
        if self.root.state() == 'normal':
            print('Window restored')
            self.on_resize_callback()

    def on_configure(self, event):
        if self.root.state() == 'zoomed':
            print('Window maximized')
            self.on_resize_callback()
        elif self.root.state() == 'normal':
            print('Window size configured')

            if (self.app_width != event.width) or (self.app_height != event.height):
                self.app_width = event.width
                self.app_height = event.height

                print('Resizing...')
                self.on_resize_callback()

    def on_resize_callback(self):
        if self.current_page == 'home':
            self.resize_home_page_items()
        elif self.current_page == 'img':
            self.resize_img_page_items()

    def on_home_page_click(self, event):
        selected_image_file = filedialog.askopenfilename(
            title='Select image file(s)/directory',
            initialdir='/',
            filetypes=self.dialog_filetypes
        )

        if len(selected_image_file) > 0:
            self.current_image_file_path = os.path.abspath(selected_image_file)
            self.show_page('img')

    def run(self):
        self.init_app()
        self.show_page('home')
        self.root.mainloop()

    def __str__(self):
        return """
        GalleryPy
        
        A sleek and intuitive Image Viewer GUI application. Easily view, navigate, and explore images with smooth
        performance and a user-friendly interface.
        """


def main():
    parser = argparse.ArgumentParser(description='GalleryPy')

    parser.add_argument('image-file', nargs='?', help='Path to a image file')
    parser.add_argument('-f', '--image-file', type=str, help='Path to a image file')
    parser.add_argument('-d', '--images-dir', type=str, help='Path to a images directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-c', '--config', type=str, help='Path to the configuration file')

    args = parser.parse_args()

    app = App({
        'image_file': args.image_file,
        'images_dir': args.images_dir,
        'verbose': args.verbose,
        'config': args.config
    })

    print(app)
    app.run()


if __name__ == '__main__':
    main()
