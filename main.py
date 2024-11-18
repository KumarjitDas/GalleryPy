import argparse
import os
import platform
from pathlib import Path
import tkinter as tk
from tkinter import ttk
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
        self.frames = {}
        self.canvases = {}
        self.images = {}
        self.photos = {}
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.dialog_filetypes = (
            ('Image Files', ' '.join([f'*.{ext}' for ext in self.APP_SUPPORTED_IMAGE_FILE_EXTENSIONS])),
        )

        self.current_image_file_path = None

    def init_app(self):
        self.set_min_width_height()
        self.apply_platform_styles()
        self.create_page_home()
        self.create_page_img()
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

    @staticmethod
    def get_photo_from_image_path(image_file_path):
        image_file_abs_path = os.path.abspath(image_file_path)
        image = Image.open(image_file_abs_path)
        return ImageTk.PhotoImage(image)

    def create_page_home(self):
        frame = tk.Frame(master=self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        center_frame = ttk.Frame(master=frame)
        center_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        image_size = 160
        empty_folder_image_path = os.path.join(self.APP_IMAGES_PATH, 'empty-folder.png')
        empty_folder_image = Image.open(empty_folder_image_path).resize((image_size, image_size), Image.Resampling.LANCZOS)
        empty_folder_photo = ImageTk.PhotoImage(empty_folder_image)

        empty_folder_canvas = tk.Canvas(master=center_frame, width=image_size, height=image_size)
        empty_folder_canvas.pack(fill=tk.BOTH, expand=True)

        canvas_width = empty_folder_canvas.winfo_width()
        canvas_height = empty_folder_canvas.winfo_height()
        canvas_width = image_size if canvas_width < image_size else canvas_width
        canvas_height = image_size if canvas_height < image_size else canvas_height

        empty_folder_canvas.create_image(canvas_width // 2, canvas_height // 2, anchor=tk.CENTER, image=empty_folder_photo)
        empty_folder_canvas.image = empty_folder_photo

        self.canvases['empty_folder'] = empty_folder_canvas
        self.images['empty_folder'] = empty_folder_image
        self.photos['empty_folder'] = empty_folder_photo

        self.resize_home_page_items()

        label2 = ttk.Label(
            master=center_frame,
            text="Label 2 as fasd fjsldfsdlfk asdfasdf asfd asdf jalskfdjs",
            anchor=tk.CENTER,
            justify=tk.CENTER,
            wraplength=240,
            padding=2,
            # foreground='#212121',
            # background='#FFFFFF',
        )
        label2.pack(fill=tk.BOTH, expand=True)

        empty_folder_canvas.configure(cursor='hand2')
        label2.configure(cursor='hand2')

        empty_folder_canvas.bind('<Button-1>', self.on_home_page_click)
        label2.bind('<Button-1>', self.on_home_page_click)
        frame.bind('<Configure>', self.on_home_page_frame_resize)

        self.pages['home'] = frame
        self.frames['home'] = frame

    def create_page_img(self):
        frame = tk.Frame(self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        if self.current_image_file_path is None:
            print('No image')
        else:
            pass
            # current_photo = self.get_photo_from_image_path(self.current_image_file_path);
            # current_canvas = tk.Canvas(master=center_frame, width=image_size, height=image_size)
            # current_canvas.pack(fill=tk.BOTH, expand=True)
            #
            # canvas_width = current_canvas.winfo_width()
            # canvas_height = current_canvas.winfo_height()
            # canvas_width = image_size if canvas_width < image_size else canvas_width
            # canvas_height = image_size if canvas_height < image_size else canvas_height
            #
            # current_canvas.create_image(canvas_width // 2, canvas_height // 2, anchor=tk.CENTER, image=current_photo)
            # current_canvas.image = current_photo
            #
            # self.canvases['empty_folder'] = current_canvas
            # self.images['empty_folder'] = empty_folder_image
            # self.photos['empty_folder'] = current_photo
            #
            # self.resize_home_page_items()

        self.pages['img'] = frame
        self.frames['img'] = frame

    def create_page_dirs_files(self):
        frame = tk.Frame(self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        label = ttk.Label(frame, text="Welcome", background="red", foreground="white")
        label.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X, expand=True)

        self.pages['dirs_files'] = frame
        self.frames['dirs_files'] = frame

    def show_page(self, page_name):
        frame = self.pages.get(page_name)

        if frame:
            frame.tkraise()
        else:
            print(f"Page '{page_name}' does not exist.")

    def resize_home_page_items(self):
        empty_folder_image = self.images['empty_folder']
        empty_folder_photo = self.photos['empty_folder']

        if empty_folder_image is None or empty_folder_photo is None:
            return

        empty_folder_canvas = self.canvases['empty_folder']

        if empty_folder_canvas.winfo_width() > 0 and empty_folder_canvas.winfo_height() > 0:
            empty_folder_canvas_width = empty_folder_canvas.winfo_width()
            empty_folder_canvas_height = empty_folder_canvas.winfo_height()

            empty_folder_image_ratio = empty_folder_image.width / empty_folder_image.height
            empty_folder_canvas_ratio = empty_folder_canvas_width / empty_folder_canvas_height

            if empty_folder_image_ratio > empty_folder_canvas_ratio:
                new_width = empty_folder_canvas_width
                new_height = new_width / empty_folder_image_ratio
            else:
                new_height = empty_folder_canvas_height
                new_width = new_height * empty_folder_image_ratio

            new_width = int(new_width)
            new_height = int(new_height)

            if new_width <= 0 or new_height <= 0:
                return

            resized_image = empty_folder_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            empty_folder_photo = ImageTk.PhotoImage(resized_image)

            empty_folder_canvas.delete("all")

            center_x = empty_folder_canvas_width // 2
            center_y = empty_folder_canvas_height // 2

            empty_folder_canvas.create_image(center_x, center_y, image=empty_folder_photo, anchor=tk.CENTER)
            self.photos['empty_folder'] = empty_folder_photo

    def on_minimize(self, event):
        if self.root.state() == 'iconic':
            print("Window minimized")

    def on_restore(self, event):
        if self.root.state() == 'normal':
            print("Window restored")

    def on_configure(self, event):
        if self.root.state() == 'zoomed':
            print("Window maximized")
        elif self.root.state() == 'normal':
            pass

    def on_home_page_frame_resize(self, event):
        self.resize_home_page_items()

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
