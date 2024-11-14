import argparse
import os
import platform
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class App:
    APP_WIDTH = 800
    APP_HEIGHT = 600
    APP_NAME = "GalleryPy"
    APP_GEOMETRY = str(APP_WIDTH) + "x" + str(APP_HEIGHT)

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
                "imageFile": None,
                "imagesDirectory": None,
                "verbose": False,
                "config": None
            }

        self.cmd_imageFile = arguments["imageFile"]
        self.cmd_imagesDirectory = arguments["imagesDirectory"]
        self.cmd_verbose = arguments["verbose"]
        self.cmd_config = arguments["config"]

        self.current_image = None
        self.current_photo = None

        self.root = tk.Tk()
        self.root_style = ttk.Style()

        self.windowing_system = self.root.tk.call("tk", "windowingsystem")
        self.navigation = {}
        self.pictures_directory = str(Path.home())

        self.root.title(self.APP_NAME)
        self.root.geometry(self.APP_GEOMETRY)

        self.root_style.theme_use("clam")
        # self.root_style.configure("MainFrame.TFrame", background="#00FF00")
        # self.root_style.configure("StatusFrame.TFrame", background="#0000FF")

        self.main_frame = ttk.Frame(master=self.root, style="MainFrame.TFrame")
        self.status_frame = ttk.Frame(master=self.root, style="StatusFrame.TFrame")

        self.status_bar_path = tk.StringVar(self.status_frame, "[NIL]")
        status_bar_path_label = ttk.Label(self.status_frame, textvariable=self.status_bar_path)

        self.main_frame.pack(side=tk.TOP, anchor=tk.N, fill=tk.BOTH, expand=True)
        self.status_frame.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X, padx=2, pady=2)

        status_bar_path_label.pack(side=tk.LEFT, anchor=tk.W)

    def determine_pictures_directory(self):
        system = platform.system()

        if system == "Windows":
            try:
                import ctypes
                from ctypes import wintypes, windll

                # Constants from Windows API
                csidl_mypictures = 39
                shgfp_type_current = 0

                buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
                windll.shell32.SHGetFolderPathW(None, csidl_mypictures, None, shgfp_type_current, buf)

                self.pictures_directory = Path(buf.value)
            except Exception as e:
                print(f"Error retrieving Windows Pictures folder via API: {e}")
                self.pictures_directory += "/Pictures"
        elif system == "Darwin":
            # macOS
            self.pictures_directory += "/Pictures"
        else:
            # Linux or other Unix-like
            self.pictures_directory += "/Pictures"

        self.pictures_directory = os.path.abspath(self.pictures_directory)

    def assign_navigation(self, navigation):
        if navigation is None:
            navigation = {}

        for key in navigation:
            self.navigation[key] = navigation[key]

    def set_status_bar_path(self, path):
        self.status_bar_path.set(path)

    def clear_all_pages(self):
        for child in self.root.winfo_children():
            child.destroy()

    def run(self):
        if self.cmd_imagesDirectory is None:
            self.determine_pictures_directory()
        else:
            # noinspection PyTypeChecker
            self.pictures_directory = os.path.abspath(self.cmd_imagesDirectory)

        if self.cmd_imageFile is not None:
            # noinspection PyTypeChecker
            image_file_path = os.path.abspath(self.cmd_imageFile)
            self.pictures_directory = os.path.dirname(image_file_path)
            self.current_image = Image.open(image_file_path)
            self.current_photo = ImageTk.PhotoImage(self.current_image)

            print("Format:", self.current_image.format)
            print("Size:", self.current_image.size)
            print("Mode:", self.current_image.mode)

            canvas = tk.Canvas(self.main_frame, width=self.current_image.width, height=self.current_image.height)
            canvas.pack()
            canvas.create_image(0, 0, anchor=tk.NW, image=self.current_photo)

            self.root.title(self.APP_NAME + " - " + os.path.splitext(os.path.basename(image_file_path))[0])

        self.set_status_bar_path(self.pictures_directory)
        self.root.mainloop()

    def __str__(self):
        return """
        GalleryPy
        
        A sleek and intuitive Image Viewer GUI application. Easily view, navigate, and explore images with smooth
        performance and a user-friendly interface.
        """


def main():
    parser = argparse.ArgumentParser(description="GalleryPy")

    parser.add_argument("image-file", nargs='?', help="Path to a image file")
    parser.add_argument("-f", "--image-file", type=str, help="Path to a image file")
    parser.add_argument("-d", "--images-directory", type=str, help="Path to a images directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-c", "--config", type=str, help="Path to the configuration file")

    args = parser.parse_args()

    app = App({
        "imageFile": args.image_file,
        "imagesDirectory": args.images_directory,
        "verbose": args.verbose,
        "config": args.config
    })

    print(app)
    app.run()


if __name__ == '__main__':
    main()
