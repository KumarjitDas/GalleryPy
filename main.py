import argparse
import os
import platform
import sys
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

    APP_MIN_WIDTH = APP_WIDTH // 2

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

    APP_PAGES = ['home', 'img', 'img_error', 'dirs_files']

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
        self.menubar = tk.Menu(master=self.root)
        self.container = tk.Frame(master=self.root)
        self.windowing_system = self.root.tk.call('tk', 'windowingsystem')
        self.page_wise_data = {}
        self.menu_items = {}
        self.current_page = None

        for page_name in self.APP_PAGES:
            self.page_wise_data[page_name] = {
                'main_frame': None,
                'page_item_loader': None,
                'other_frames': {},
                'canvases': {},
                'fonts': {},
                'labels': {},
                'images': {},
                'photos': {},
                'string_vars': {}
            }

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
        self.root_style.theme_use('clam')
        self.set_min_width_height()
        self.apply_platform_styles()
        self.create_menubar_items()
        self.create_page_home()
        self.create_page_img()
        self.create_page_img_error()
        self.create_page_dirs_files()

        self.root.title(self.APP_NAME)
        self.root.geometry(self.APP_GEOMETRY)
        self.root.config(menu=self.menubar)

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

    def create_menubar_items(self):
        # The 'File' menu
        file_menu = tk.Menu(self.menubar, tearoff=False)
        file_menu.add_command(label='Open file(s)...', command=lambda: self.open_choose_img_files_dialog_and_show())
        file_menu.add_command(label='Open directory...', command=lambda: '')
        file_menu.add_command(label='Close image', state=tk.DISABLED, command=lambda: self.close_current_img())
        file_menu.add_command(label='Delete image', state=tk.DISABLED, command=lambda: '')
        file_menu.add_separator()

        # The 'Export' submenu
        export_submenu = tk.Menu(file_menu, tearoff=False)

        for file_ext in self.APP_SUPPORTED_IMAGE_FILE_EXTENSIONS:
            export_submenu.add_command(label=file_ext, command=lambda: '')

        file_menu.add_cascade(label='Export', state=tk.DISABLED, menu=export_submenu)

        file_menu.add_command(label='Print', state=tk.DISABLED, command=lambda: '')
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.destroy)
        self.menubar.add_cascade(label='File', menu=file_menu, underline=0)
        self.menu_items['file'] = file_menu

        # The 'Edit' menu
        edit_menu = tk.Menu(self.menubar, tearoff=False)
        edit_menu.add_command(label='Copy image', state=tk.DISABLED, command=lambda: '')
        edit_menu.add_command(label='Copy path', state=tk.DISABLED, command=lambda: '')
        edit_menu.add_command(label='Resize image', state=tk.DISABLED, command=lambda: '')
        edit_menu.add_separator()
        edit_menu.add_command(label='Settings', command=lambda: '')
        self.menubar.add_cascade(label='Edit', menu=edit_menu, underline=0)
        self.menu_items['edit'] = edit_menu

        # The 'View' menu
        view_menu = tk.Menu(self.menubar, tearoff=False)

        # The 'Appearance' submenu
        appearance_submenu = tk.Menu(view_menu, tearoff=False)
        appearance_submenu.add_radiobutton(label='Light', command=lambda: '')
        appearance_submenu.add_radiobutton(label='Dark', command=lambda: '')
        view_menu.add_cascade(label='Appearance', menu=appearance_submenu)

        # The 'Language' submenu
        language_submenu = tk.Menu(view_menu, tearoff=False)
        language_submenu.add_radiobutton(label='English', command=lambda: '')
        language_submenu.add_radiobutton(label='Bangla', command=lambda: '')
        view_menu.add_cascade(label='Language', menu=language_submenu)

        view_menu.add_command(label='Image info', state=tk.DISABLED, command=lambda: '')
        self.menubar.add_cascade(label='View', menu=view_menu, underline=0)
        self.menu_items['view'] = view_menu

        # The 'Help' menu
        help_menu = tk.Menu(self.menubar, tearoff=False)
        help_menu.add_command(label='Help', command=lambda: '')
        help_menu.add_command(label='About...', command=lambda: '')
        self.menubar.add_cascade(label='Help', menu=help_menu, underline=0)
        self.menu_items['help'] = help_menu

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

        self.page_wise_data['home']['canvases']['empty_folder'] = empty_folder_canvas
        self.page_wise_data['home']['fonts']['empty_folder'] = empty_folder_label_font
        self.page_wise_data['home']['labels']['empty_folder'] = empty_folder_label
        self.page_wise_data['home']['page_item_loader'] = self.load_page_home_items
        self.page_wise_data['home']['main_frame'] = frame

        empty_folder_canvas.bind('<Button-1>', self.on_home_page_click)
        empty_folder_label.bind('<Button-1>', self.on_home_page_click)
        # frame.bind('<Configure>', self.on_home_page_frame_resize)

    def create_page_img(self):
        frame = tk.Frame(master=self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        main_img_view_canvas = tk.Canvas(master=frame)
        main_img_view_canvas.pack(side=tk.TOP, anchor=tk.N, fill=tk.BOTH, expand=True)

        status_frame = tk.Frame(master=frame)
        status_frame.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X, padx=2, pady=2)

        current_img_dir_path = tk.StringVar(master=status_frame, value='[NIL]')
        current_img_dim = tk.StringVar(master=status_frame, value='0x0')
        current_img_file_size = tk.StringVar(master=status_frame, value='0 Bytes')
        current_img_format = tk.StringVar(master=status_frame, value='[UNKNOWN]')

        current_img_dir_label = ttk.Label(master=status_frame, textvariable=current_img_dir_path)
        current_img_format_label = ttk.Label(master=status_frame, textvariable=current_img_format)
        current_img_file_size_label = ttk.Label(master=status_frame, textvariable=current_img_file_size)
        current_img_dim_label = ttk.Label(master=status_frame, textvariable=current_img_dim)

        current_img_dir_label.pack(side=tk.LEFT, anchor=tk.W)
        current_img_format_label.pack(side=tk.RIGHT, anchor=tk.E)
        current_img_file_size_label.pack(side=tk.RIGHT, anchor=tk.E, padx=2)
        current_img_dim_label.pack(side=tk.RIGHT, anchor=tk.E)

        self.page_wise_data['img']['string_vars']['current_img_dir_path'] = current_img_dir_path
        self.page_wise_data['img']['string_vars']['current_img_dim'] = current_img_dim
        self.page_wise_data['img']['string_vars']['current_img_file_size'] = current_img_file_size
        self.page_wise_data['img']['string_vars']['current_img_format'] = current_img_format

        self.page_wise_data['img']['labels']['current_img_dir'] = current_img_dir_label
        self.page_wise_data['img']['labels']['current_img_dim'] = current_img_dim_label
        self.page_wise_data['img']['labels']['current_img_file_size'] = current_img_file_size_label
        self.page_wise_data['img']['labels']['current_img_format'] = current_img_format_label

        self.page_wise_data['img']['canvases']['main_img_view'] = main_img_view_canvas
        self.page_wise_data['img']['page_item_loader'] = self.load_page_img_items
        self.page_wise_data['img']['main_frame'] = frame

    def create_page_img_error(self):
        frame = tk.Frame(self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        label = ttk.Label(frame, text='Could not show image.', background='red', foreground='#FFFFFF')
        label.pack(side=tk.TOP, anchor=tk.N, fill=tk.X, expand=True)

        self.page_wise_data['img_error']['page_item_loader'] = self.load_page_img_error_items
        self.page_wise_data['img_error']['main_frame'] = frame

    def create_page_dirs_files(self):
        frame = tk.Frame(self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        label = ttk.Label(frame, text="Welcome", background="red", foreground="white")
        label.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X, expand=True)

        self.page_wise_data['dirs_files']['page_item_loader'] = self.load_page_dirs_files_items
        self.page_wise_data['dirs_files']['main_frame'] = frame

    def show_page(self, page_name):
        page_data = self.page_wise_data.get(page_name)

        if page_data:
            frame = page_data.get('main_frame')
            page_item_loader = page_data.get('page_item_loader')

            frame.tkraise()
            page_item_loader()

            self.current_page = page_name
        else:
            print(f"Page '{page_name}' does not exist.")

    def load_page_home_items(self):
        page_data = self.page_wise_data.get('home')

        image_size = self.EMPTY_FOLDER_IMAGE_SIZE_MAX
        empty_folder_image_path = os.path.join(self.APP_IMAGES_PATH, 'empty-folder.png')
        empty_folder_image = Image.open(empty_folder_image_path).resize((image_size, image_size), Image.Resampling.LANCZOS)
        empty_folder_photo = ImageTk.PhotoImage(empty_folder_image)

        empty_folder_canvas = page_data['canvases']['empty_folder']
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

        page_data['canvases']['empty_folder'] = empty_folder_canvas
        page_data['images']['empty_folder'] = empty_folder_image
        page_data['photos']['empty_folder'] = empty_folder_photo

        self.root.title(self.APP_NAME)

        self.menu_items['file'].entryconfig('Close image', state=tk.DISABLED)
        self.menu_items['file'].entryconfig('Delete image', state=tk.DISABLED)

        self.menu_items['edit'].entryconfig('Copy image', state=tk.DISABLED)
        self.menu_items['edit'].entryconfig('Copy path', state=tk.DISABLED)
        self.menu_items['edit'].entryconfig('Resize image', state=tk.DISABLED)

        self.resize_home_page_items()

    def load_page_img_items(self):
        if self.current_image_file_path is None:
            self.show_page('img_error')
        else:
            try:
                page_data = self.page_wise_data.get('img')

                main_img_view_canvas = page_data['canvases']['main_img_view']
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

                page_data['images']['current'] = current_image
                page_data['photos']['current'] = current_photo

                current_image_file_base_name = os.path.basename(self.current_image_file_path)
                current_image_file_name = os.path.splitext(current_image_file_base_name)[0]
                self.root.title(self.APP_NAME + ' - ' + current_image_file_name)

                self.menu_items['file'].entryconfig('Close image', state=tk.ACTIVE)
                self.menu_items['file'].entryconfig('Delete image', state=tk.ACTIVE)

                self.menu_items['edit'].entryconfig('Copy image', state=tk.ACTIVE)
                self.menu_items['edit'].entryconfig('Copy path', state=tk.ACTIVE)
                self.menu_items['edit'].entryconfig('Resize image', state=tk.ACTIVE)

                current_image_dir_name = os.path.dirname(self.current_image_file_path)
                current_img_dim = str(current_image.size[0]) + 'x' + str(current_image.size[1])
                current_imd_file_size = self.get_readable_file_size(self.current_image_file_path)

                page_data['string_vars']['current_img_dir_path'].set(current_image_dir_name)
                page_data['string_vars']['current_img_dim'].set(current_img_dim)
                page_data['string_vars']['current_img_file_size'].set(current_imd_file_size)
                page_data['string_vars']['current_img_format'].set(current_image.format)

                self.resize_img_page_items()
            except Exception as e:
                print(e, file=sys.stderr)
                self.show_page('img_error')

    def load_page_img_error_items(self):
        pass

    def load_page_dirs_files_items(self):
        pass

    def resize_home_page_items(self):
        page_data = self.page_wise_data.get('home')

        empty_folder_image = page_data['images']['empty_folder']
        empty_folder_photo = page_data['photos']['empty_folder']

        if empty_folder_image is None or empty_folder_photo is None:
            return

        empty_folder_canvas = page_data['canvases']['empty_folder']
        empty_folder_font = page_data['fonts']['empty_folder']

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

        page_data['photos']['empty_folder'] = empty_folder_photo

    def resize_img_page_items(self):
        page_data = self.page_wise_data.get('img')

        current_image = page_data['images']['current']
        current_photo = page_data['photos']['current']

        if current_image is None or current_photo is None:
            return

        main_img_view_canvas = page_data['canvases']['main_img_view']
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

            page_data['photos']['current'] = resized_current_photo

    def open_choose_img_files_dialog_and_show(self):
        selected_image_files = filedialog.askopenfilenames(
            title='Select image file(s)/directory',
            initialdir='/',
            filetypes=self.dialog_filetypes
        )

        if len(selected_image_files) > 0:
            self.current_image_file_path = os.path.abspath(selected_image_files[0])
            self.show_page('img')

    def close_current_img(self):
        page_data = self.page_wise_data.get('img')

        page_data['images']['current'] = None
        page_data['photos']['current'] = None

        page_data['string_vars']['current_img_dir_path'].set('[NIL]')
        page_data['string_vars']['current_img_dim'].set('0x0')
        page_data['string_vars']['current_img_file_size'].set('0 B')
        page_data['string_vars']['current_img_format'].set('[NIL]')

        self.show_page('home')

    def on_minimize(self, event):
        if self.root.state() == 'iconic':
            pass

    def on_restore(self, event):
        if self.root.state() == 'normal':
            self.on_resize_callback()

    def on_configure(self, event):
        if self.root.state() == 'zoomed':
            self.on_resize_callback()
        elif self.root.state() == 'normal':
            if (self.app_width != event.width) or (self.app_height != event.height):
                self.app_width = event.width
                self.app_height = event.height
                self.on_resize_callback()

    def on_resize_callback(self):
        if self.current_page == 'home':
            self.resize_home_page_items()
        elif self.current_page == 'img':
            self.resize_img_page_items()

    def on_home_page_click(self, event):
        self.open_choose_img_files_dialog_and_show()

    def run(self):
        self.init_app()
        self.show_page('home')
        self.root.mainloop()

    @staticmethod
    def get_readable_file_size(file_path):
        size_bytes = os.path.getsize(file_path)

        if size_bytes < 1024:
            return f'{size_bytes} B'
        elif size_bytes < 1024 ** 2:
            size_kb = size_bytes / 1024
            return f'{size_kb:.2f} KB'
        elif size_bytes < 1024 ** 3:
            size_mb = size_bytes / (1024 ** 2)
            return f'{size_mb:.2f} MB'
        else:
            size_gb = size_bytes / (1024 ** 3)
            return f'{size_gb:.2f} GB'

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
