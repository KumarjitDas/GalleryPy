import platform
from pathlib import Path
import tkinter as tk
from tkinter import ttk


class App:
    APP_NAME = "GalleryPy"
    APP_GEOMETRY = "640x400"

    def __init__(self):
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
        self.determine_pictures_directory()
        self.set_status_bar_path(self.pictures_directory)
        self.root.mainloop()

    def __str__(self):
        return """
        GalleryPy
        
        A sleek and intuitive Image Viewer GUI application. Easily view, navigate, and explore images with smooth
        performance and a user-friendly interface.
        """


def main():
    app = App()
    print(app)
    app.run()


if __name__ == '__main__':
    main()
