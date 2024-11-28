import argparse
import os
import sys
import tkinter as tk
from queue import Queue
from tkinter import ttk
from tkinter.font import Font
from tkinter import filedialog
from typing import Callable, Any, Union

from PIL import Image, ImageTk


class TaskQueue:
    """
    A centralized queueing system for managing sequential execution of tasks.

    Attributes:
        root (tk.Tk): The root Tkinter window for managing the event loop.
        task_queues (dict): A dictionary mapping task names to their respective queues.
        running_tasks (dict): A dictionary tracking whether a task is currently running.

    Methods:
        enqueue_task(func_name, task):
            Adds a task to the queue for the given function name and starts processing if idle.
        process_queue(func_name):
            Executes the next task in the queue for the given function name.
        finish_task(func_name):
            Marks the current task for the given function name as complete and processes the next task.

    Decorators:
        task():
            A decorator to enqueue a function as a task. This ensures the function executes sequentially
            and only after all previously enqueued tasks for the same function have completed.

            Usage:
                @task_queue.task()
                def my_task():
                    # Task logic here
                    pass

            Returns:
                Callable: The wrapped function, which will automatically be added to the task queue when called.
    """
    def __init__(self, root: Union[None, tk.Tk]=None) -> None:
        self.root: tk.Tk = root
        self.task_queues: dict[str, Queue[Callable[..., Any]]] = {}  # Dictionary to store queues for each function
        self.running_tasks: dict[str, bool] = {}  # Dictionary to track running states for each function

    def set_root(self, root: tk.Tk) -> None:
        self.root = root

    def enqueue_task(self, func_name: str, task: Callable[..., Any]) -> None:
        """Add a task to the queue for the given function."""
        if func_name not in self.task_queues:
            self.task_queues[func_name] = Queue()
            self.running_tasks[func_name] = False

        self.task_queues[func_name].put(task)
        self.process_queue(func_name)

    def process_queue(self, func_name: str) -> None:
        """Process the queue for a given function."""
        if not self.running_tasks[func_name] and not self.task_queues[func_name].empty():
            self.running_tasks[func_name] = True

            task: Callable[..., Any] = self.task_queues[func_name].get()
            task()  # Execute the task

            if self.root is None:
                self.finish_task(func_name)
                return

            # noinspection PyTypeChecker
            self.root.after(10, lambda: self.finish_task(func_name))

    def finish_task(self, func_name: str) -> None:
        """Mark the current task as complete and process the next one."""
        self.running_tasks[func_name] = False
        self.process_queue(func_name)

    def task(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to enqueue tasks using the function's name."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args, **kwargs) -> None:
                func_name: str = func.__name__
                self.enqueue_task(func_name, lambda: func(*args, **kwargs))

            return wrapper

        return decorator


class DependencyManager:
    """
    A centralized system for managing dependencies between functions.

    Attributes:
        dependency_states (dict): A dictionary tracking dependencies for follow-up functions.

    Methods:
        add_dependencies(follow_up_func, dependencies):
            Registers a follow-up function with a list of dependent functions.
        mark_complete(func_name):
            Marks a dependent function as completed and triggers the follow-up function if all dependencies are satisfied.

    Decorators:
        dependency():
            A decorator to mark a function as complete after it is executed. This ensures that
            the function is registered as completed within the dependency tracking system.

            Usage:
                @dependency_manager.dependency()
                def my_dependent_function():
                    # Function logic here
                    pass

            Returns:
                Callable: The wrapped function, which automatically registers itself as completed upon execution.
    """
    def __init__(self) -> None:
        # Dictionary to track dependencies and their completion states
        self.dependency_states: dict[Callable[..., Any], dict[str, set]] = {}

    def add_dependencies(self, follow_up_func: Callable[..., Any], dependencies: Union[tuple[str, ...], list[str]]) -> None:
        """Register dependencies for a follow-up function."""
        self.dependency_states[follow_up_func] = {
            'dependencies': set(dependencies),  # Functions that must complete
            'completed': set()  # Functions that have completed
        }

    def mark_complete(self, func_name: str):
        """Mark a dependent function as completed and check for follow-up execution."""
        for follow_up_func, state in self.dependency_states.items():
            if func_name in state['dependencies']:
                state['completed'].add(func_name)

                # If all dependencies are completed, execute the follow-up function
                if state['dependencies'] == state['completed']:
                    follow_up_func()

                    # Clear the state to prevent repeated execution
                    self.dependency_states[follow_up_func]['completed'].clear()

    def dependency(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to mark functions as complete using the function's name."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args, **kwargs) -> None:
                result: Any = func(*args, **kwargs)
                func_name: str = func.__name__

                self.mark_complete(func_name)
                return result

            return wrapper

        return decorator


class FiniteStateMachine:
    """
    A generic Finite State Machine (FSM) for managing states and transitions.

    Attributes:
        current_state (str): The current state of the FSM.
        transitions (dict): A dictionary mapping states to their valid transitions.
        state_actions (dict): A dictionary mapping states to their respective actions.

    Methods:
        add_state(state, transitions, action=None):
            Adds a state to the FSM with its valid transitions and optional action.
        set_state(state):
            Sets the current state of the FSM if the state exists.
        add_transition(from_state, to_state):
            Adds a valid transition between two states.
        change_state(new_state):
            Changes the state if the transition is valid and executes the action for the new state.
    """
    def __init__(self, initial_state: Union[None, str]=None):
        self.current_state: Union[None, str] = initial_state
        self.transitions: dict = {}
        self.state_actions: dict = {}

    def add_state(self, state: str, transitions: Union[None, list[str]]=None, action: Callable[[str, str, ...], Any]=None):
        """Adds a state to the FSM with valid transitions and an optional action."""
        self.transitions[state] = transitions or []
        self.state_actions[state] = action

    def set_state(self, state: str):
        """Sets the current state of the FSM."""
        if state not in self.transitions:
            raise ValueError(f"State '{state}' is not defined in the FSM.")

        self.current_state = state

    def add_transition(self, from_state: str, to_state: str):
        """Adds a valid transition between two states."""
        if from_state not in self.transitions:
            raise ValueError(f"State '{from_state}' is not defined in the FSM.")

        self.transitions[from_state].append(to_state)

    def change_state(self, new_state: str):
        """Changes the state if the transition is valid and executes the state's action."""
        if new_state not in self.transitions.get(self.current_state, []):
            print(f'Invalid transition: {self.current_state} → {new_state}')
            return

        print(f'Transitioning from {self.current_state} to {new_state}')

        prev_state: str = self.current_state
        self.current_state = new_state

        # Execute the action for the new state
        if action := self.state_actions.get(new_state):
            action(new_state, prev_state)


# noinspection PyTypedDict,PyCallingNonCallable,DuplicatedCode,PyTypeChecker
class App:
    APP_WIDTH = 640
    APP_HEIGHT = 400
    APP_NAME = 'GalleryPy'
    APP_GEOMETRY = str(APP_WIDTH) + 'x' + str(APP_HEIGHT)

    APP_MIN_WIDTH = APP_WIDTH // 2

    APP_RESOURCES_PATH = os.path.abspath('resources/')
    APP_IMAGES_PATH = os.path.join(APP_RESOURCES_PATH, 'images')

    APP_SUPPORTED_IMAGE_FILE_EXTENSIONS = [
        'bmp', 'dib', 'eps', 'gif', 'icns', 'ico', 'im', 'jpeg', 'jpe', 'jpg',
        'msp', 'pcx', 'png', 'ppm', 'pgm', 'pbm', 'pnm', 'sgi', 'rgb', 'bw',
        'spider', 'tga', 'tif', 'tiff', 'webp', 'xbm', 'pdf', 'psd', 'fits',
        'fit', 'pcd', 'dds'
    ]

    APP_PAGES = ['home', 'img', 'img_error', 'dirs_files']

    EMPTY_FOLDER_IMAGE_SIZE_MIN = 60
    EMPTY_FOLDER_IMAGE_SIZE_MAX = 120

    EMPTY_FOLDER_LABEL_FONT_SIZE_MIN = 8
    EMPTY_FOLDER_LABEL_FONT_SIZE_MAX = 11

    task_queue = TaskQueue()
    dependency_manager = DependencyManager()
    window_fsm = FiniteStateMachine()

    def __init__(self, arguments: dict[str, Union[bool, None, str]]) -> None:
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
        self.root_style_canvas_params: dict[str, Union[bool, int, float, None, str]] = {}

        self.menubar = tk.Menu(master=self.root)
        self.container = ttk.Frame(master=self.root)
        self.windowing_system = self.root.tk.call('tk', 'windowingsystem')
        self.page_wise_data = {}
        self.menu_items = {}
        self.current_page = None
        self.timeout_callbacks = {}

        for page_name in self.APP_PAGES:
            self.page_wise_data[page_name] = {
                'main_frame': None,
                'page_item_loader': None,
                'other_frames': {},
                'canvases': {},
                'fonts': {},
                'labels': {},
                'buttons': {},
                'images': {},
                'photos': {},
                'string_vars': {},
                'kwargs': {}
            }

        self._is_initial_sizing_complete = False
        self._is_initial_dims = True
        self._is_resizing = False
        self._is_restoring_after_fullscreen = False
        self._is_fullscreen_after_maximized = False
        self._is_restoring_after_fullscreen_in_img = False
        self._is_first_menubar_resize_after_fullscreen = False
        self._is_first_statusbar_resize_after_fullscreen = False

        self.is_window_minimized = False
        self.is_window_maximized = False
        self.was_window_maximized_before = False
        self.is_window_fullscreen = False

        self.is_menubar_hidden = False
        self.is_alt_key_menubar_hidden = False
        self.is_alt_key_statusbar_hidden = False

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.app_width = self.root.winfo_width()
        self.app_height = self.root.winfo_height()
        self.app_geometry_before_maximize = self.root.winfo_geometry()
        self.app_width_before_maximize = self.app_width
        self.app_height_before_maximize = self.app_height
        self.current_image_width = 0
        self.current_image_height = 0

        self.dialog_filetypes = (
            ('Image Files', ' '.join([f'*.{ext}' for ext in self.APP_SUPPORTED_IMAGE_FILE_EXTENSIONS])),
        )

        self.current_image_file_idx = None
        self.current_image_file_path = None
        self.current_image_file_paths = []

    def init_app(self):
        self.task_queue.set_root(self.root)
        self.set_min_width_height()
        self.apply_platform_themes_styles()
        self.root_style.theme_use('gallerypy_light')
        self.create_menubar_items()
        self.create_page_home()
        self.create_page_img()
        self.create_page_img_error()
        self.create_page_dirs_files()

        self.root.title(self.APP_NAME)
        self.root.geometry(self.APP_GEOMETRY)
        self.root.config(menu=self.menubar)

        self.root.bind_all('<Unmap>', self.on_minimize)
        self.root.bind_all('<Map>', self.on_restore)
        self.root.bind_all('<Configure>', self.on_configure)
        self.root.bind_all('<Enter>', self.on_enter)
        self.root.bind_all('<Leave>', self.on_leave)

        self.root.bind_all('<F11>', self.on_f11_keypress)
        self.root.bind_all('<Escape>', self.on_esc_keypress)
        self.root.bind_all('<Alt_L>', self.on_alt_keypress)
        self.root.bind_all('<Alt_R>', self.on_alt_keypress)

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

    def apply_platform_themes_styles(self):
        settings = {}

        if self.windowing_system == 'aqua':
            # macOS specific styling
            settings['TButton'] = {
                'configure': {
                    'foreground': 'blue',
                    'background': '#1E1F22',
                    'font': ('Helvetica', 10),
                    'padding': 10
                },
                'map': {
                    'background': [('active', 'skyblue'), ('pressed', 'deepskyblue')],
                    'foreground': [('disabled', 'gray')]
                }
            }

            settings['TLabel'] = {
                'configure': {
                    'foreground': 'dark green',
                    'font': ('Helvetica', 10)
                }
            }

            self.root_style.theme_create("gallerypy_light", parent='clam', settings=settings)
        elif self.windowing_system == 'win32':
            # Windows specific styling
            # self.root_style.configure('TButton', foreground='dark red', font=('Arial', 10, 'bold'))
            # self.root_style.configure('TLabel', foreground='purple', font=('Arial', 10, 'italic'))

            settings['TFrame'] = {
                'configure': {
                    'foreground': '#212529',
                    'background': '#EBECF0',
                    'font': ('Arial', 9)
                }
            }

            settings['TLabel'] = {
                'configure': {
                    'foreground': '#212529',
                    'background': '#EBECF0',
                    'font': ('Arial', 9)
                }
            }

            settings['TButton'] = {
                'configure': {
                    'foreground': 'blue',
                    'background': '#EBECF0',
                    'font': ('Arial', 8),
                    'padding': (2, 5, 2, 5)
                },
                'map': {
                    'background': [
                        ('active', 'skyblue'),
                        ('pressed', 'deepskyblue')
                    ],
                    'foreground': [
                        ('disabled', 'gray')
                    ]
                }
            }

            self.root_style_canvas_params = {
                'background': settings['TFrame']['configure']['background'],
                'borderwidth': 0,
                'bd': 0,
                'highlightthickness': 0,
                'relief': 'groove'
            }

            self.root_style.theme_create("gallerypy_light", parent='default', settings=settings)
        elif self.windowing_system == 'x11':
            # Linux specific styling
            # self.root_style.configure('TButton', foreground='dark blue', font=('Courier', 10))
            # self.root_style.configure('TLabel', foreground='brown', font=('Courier', 10))

            settings['TButton'] = {
                'configure': {
                    'foreground': 'blue',
                    'background': '#1E1F22',
                    'font': ('Helvetica', 10),
                    'padding': 10
                },
                'map': {
                    'background': [('active', 'skyblue'), ('pressed', 'deepskyblue')],
                    'foreground': [('disabled', 'gray')]
                }
            }

            settings['TLabel'] = {
                'configure': {
                    'foreground': 'dark green',
                    'font': ('Helvetica', 10)
                }
            }

            self.root_style.theme_create("gallerypy_light", parent='alt', settings=settings)
        else:
            # Default styling for other systems
            # self.root_style.configure('TButton', foreground='black', font=('TkDefaultFont', 10))
            # self.root_style.configure('TLabel', foreground='black', font=('TkDefaultFont', 10))

            settings['TButton'] = {
                'configure': {
                    'foreground': 'blue',
                    'background': '#1E1F22',
                    'font': ('Helvetica', 10),
                    'padding': 10
                },
                'map': {
                    'background': [('active', 'skyblue'), ('pressed', 'deepskyblue')],
                    'foreground': [('disabled', 'gray')]
                }
            }

            settings['TLabel'] = {
                'configure': {
                    'foreground': 'dark green',
                    'font': ('Helvetica', 10)
                }
            }

            self.root_style.theme_create("gallerypy_light", parent='default', settings=settings)

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

        # The 'Window' submenu
        window_submenu = tk.Menu(view_menu, tearoff=False)
        window_submenu.add_command(label='Minimize', command=lambda: self.minimize_window())
        window_submenu.add_command(label='Maximize', command=lambda: self.maximize_window())
        window_submenu.add_command(label='Fullscreen', command=lambda: self.fullscreen_window())
        window_submenu.add_command(label='Restore', state=tk.DISABLED, command=lambda: self.restore_window())
        view_menu.add_cascade(label='Window', menu=window_submenu)
        self.menu_items['view__window'] = window_submenu

        view_menu.add_command(label='Slideshow', state=tk.DISABLED, command=lambda: '')

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
        frame = ttk.Frame(master=self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        center_frame = ttk.Frame(master=frame, width=50, height=50)
        center_frame.place(relx=0.5, rely=0.475, anchor=tk.CENTER)

        empty_folder_canvas = tk.Canvas(master=center_frame, cursor='hand2', **self.root_style_canvas_params)
        empty_folder_canvas.pack(side=tk.TOP, anchor=tk.S, fill=tk.BOTH, expand=True)

        empty_folder_label_font = Font(size=self.EMPTY_FOLDER_LABEL_FONT_SIZE_MIN, weight='bold')

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
        frame = ttk.Frame(master=self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        main_img_view_canvas = tk.Canvas(master=frame, **self.root_style_canvas_params)
        main_img_view_canvas.grid(row=0, column=0, sticky=tk.NSEW)

        status_frame = ttk.Frame(master=frame)
        status_frame.grid(row=1, column=0, sticky=tk.EW)

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=0)
        frame.grid_columnconfigure(0, weight=1)

        current_img_dir_path = tk.StringVar(master=status_frame, value='[NIL]')
        current_img_idx = tk.StringVar(master=status_frame, value='0/0')
        current_img_dim = tk.StringVar(master=status_frame, value='0x0')
        current_img_file_size = tk.StringVar(master=status_frame, value='0 Bytes')
        current_img_format = tk.StringVar(master=status_frame, value='[UNKNOWN]')

        current_img_dir_label = ttk.Label(master=status_frame, textvariable=current_img_dir_path)
        current_img_idx_label = ttk.Label(master=status_frame, textvariable=current_img_idx)
        current_img_dim_label = ttk.Label(master=status_frame, textvariable=current_img_dim)
        current_img_file_size_label = ttk.Label(master=status_frame, textvariable=current_img_file_size)
        current_img_format_label = ttk.Label(master=status_frame, textvariable=current_img_format)

        current_img_dir_label.grid(row=0, column=0, sticky=tk.W, padx=4)
        current_img_idx_label.grid(row=0, column=2, padx=4)
        current_img_dim_label.grid(row=0, column=3, padx=4)
        current_img_file_size_label.grid(row=0, column=4, padx=4)
        current_img_format_label.grid(row=0, column=5, padx=4)

        status_frame.grid_columnconfigure(0, weight=0)
        status_frame.grid_columnconfigure(1, weight=1)
        status_frame.grid_columnconfigure(2, weight=0)
        status_frame.grid_columnconfigure(3, weight=0)
        status_frame.grid_columnconfigure(4, weight=0)
        status_frame.grid_columnconfigure(5, weight=0)

        self.page_wise_data['img']['string_vars']['current_img_dir_path'] = current_img_dir_path
        self.page_wise_data['img']['string_vars']['current_img_idx'] = current_img_idx
        self.page_wise_data['img']['string_vars']['current_img_dim'] = current_img_dim
        self.page_wise_data['img']['string_vars']['current_img_file_size'] = current_img_file_size
        self.page_wise_data['img']['string_vars']['current_img_format'] = current_img_format

        self.page_wise_data['img']['labels']['current_img_dir'] = current_img_dir_label
        self.page_wise_data['img']['labels']['current_img_idx'] = current_img_idx_label
        self.page_wise_data['img']['labels']['current_img_dim'] = current_img_dim_label
        self.page_wise_data['img']['labels']['current_img_file_size'] = current_img_file_size_label
        self.page_wise_data['img']['labels']['current_img_format'] = current_img_format_label

        self.page_wise_data['img']['canvases']['main_img_view'] = main_img_view_canvas
        self.page_wise_data['img']['other_frames']['status'] = status_frame
        self.page_wise_data['img']['page_item_loader'] = self.load_page_img_items
        self.page_wise_data['img']['main_frame'] = frame

        frame.bind('<Left>', lambda _: self.show_prev_img())
        frame.bind('<Right>', lambda _: self.show_next_img())

    def create_page_img_error(self):
        frame = ttk.Frame(self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        label = ttk.Label(frame, text='Could not show image.', background='red', foreground='#FFFFFF')
        label.pack(side=tk.TOP, anchor=tk.N, fill=tk.X, expand=True)

        self.page_wise_data['img_error']['page_item_loader'] = self.load_page_img_error_items
        self.page_wise_data['img_error']['main_frame'] = frame

    def create_page_dirs_files(self):
        frame = ttk.Frame(self.container)
        frame.grid(row=0, column=0, sticky=tk.NSEW)

        label = ttk.Label(frame, text="Welcome", background="red", foreground="white")
        label.pack(side=tk.BOTTOM, anchor=tk.S, fill=tk.X, expand=True)

        self.page_wise_data['dirs_files']['page_item_loader'] = self.load_page_dirs_files_items
        self.page_wise_data['dirs_files']['main_frame'] = frame

    def show_page(self, page_name: str):
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
                self._is_restoring_after_fullscreen_in_img = True
                page_data = self.page_wise_data.get('img')

                if self.is_window_fullscreen:
                    self.hide_menubar()
                    page_data['other_frames']['status'].grid_remove()

                self.show_current_img()

                main_frame = page_data['main_frame']

                left_arrow_image_path = os.path.join(self.APP_IMAGES_PATH, 'left-arrow.png')
                right_arrow_image_path = os.path.join(self.APP_IMAGES_PATH, 'right-arrow.png')
                left_arrow_image = Image.open(left_arrow_image_path)
                right_arrow_image = Image.open(right_arrow_image_path)
                left_arrow_photo = ImageTk.PhotoImage(left_arrow_image)
                right_arrow_photo = ImageTk.PhotoImage(right_arrow_image)

                left_button_kwargs = { 'relx': 0, 'rely': 0.5, 'anchor': tk.W, 'x': 10 }
                right_button_kwargs = { 'relx': 1, 'rely': 0.5, 'anchor': tk.E, 'x': -10 }

                left_button = ttk.Button(master=main_frame, image=left_arrow_photo, command=lambda: self.show_prev_img())
                left_button.place(**left_button_kwargs)

                right_button = ttk.Button(master=main_frame, image=right_arrow_photo, command=lambda: self.show_next_img())
                right_button.place(**right_button_kwargs)

                self.menu_items['file'].entryconfig('Close image', state=tk.ACTIVE)
                self.menu_items['file'].entryconfig('Delete image', state=tk.ACTIVE)

                self.menu_items['edit'].entryconfig('Copy image', state=tk.ACTIVE)
                self.menu_items['edit'].entryconfig('Copy path', state=tk.ACTIVE)
                self.menu_items['edit'].entryconfig('Resize image', state=tk.ACTIVE)

                current_image_dir_name = os.path.dirname(self.current_image_file_path)

                page_data['string_vars']['current_img_dir_path'].set(current_image_dir_name)
                page_data['string_vars']['current_img_idx'].set('1/?')

                page_data['images']['left_arrow'] = left_arrow_image
                page_data['images']['right_arrow'] = right_arrow_image

                page_data['photos']['left_arrow'] = left_arrow_photo
                page_data['photos']['right_arrow'] = right_arrow_photo

                page_data['buttons']['left'] = left_button
                page_data['buttons']['right'] = right_button

                page_data['kwargs']['left_button'] = left_button_kwargs
                page_data['kwargs']['right_button'] = right_button_kwargs
            except Exception as e:
                print(e, file=sys.stderr)
                self.show_page('img_error')

    def load_page_img_error_items(self):
        pass

    def load_page_dirs_files_items(self):
        pass

    def resize_menubar_items(self):
        if self.is_window_maximized:
            self.menu_items['view__window'].entryconfig('Maximize', state=tk.DISABLED)
            self.menu_items['view__window'].entryconfig('Fullscreen', state=tk.ACTIVE)
            self.menu_items['view__window'].entryconfig('Restore', state=tk.ACTIVE)
        elif self.is_window_fullscreen:
            if self.current_page == 'img':
                if not self._is_first_menubar_resize_after_fullscreen:
                    self._is_first_menubar_resize_after_fullscreen = True
                    self.hide_menubar()

            self.menu_items['view__window'].entryconfig('Maximize', state=tk.ACTIVE)
            self.menu_items['view__window'].entryconfig('Fullscreen', state=tk.DISABLED)
            self.menu_items['view__window'].entryconfig('Restore', state=tk.ACTIVE)
        else:
            if self.current_page == 'img':
                self.show_menubar()

            self.menu_items['view__window'].entryconfig('Maximize', state=tk.ACTIVE)
            self.menu_items['view__window'].entryconfig('Fullscreen', state=tk.ACTIVE)
            self.menu_items['view__window'].entryconfig('Restore', state=tk.DISABLED)

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

        if self.is_window_fullscreen:
            if not self._is_first_statusbar_resize_after_fullscreen:
                self._is_first_statusbar_resize_after_fullscreen = True
                self.is_alt_key_statusbar_hidden = True
                page_data['other_frames']['status'].grid_remove()
        else:
            self.is_alt_key_statusbar_hidden = False
            page_data['other_frames']['status'].grid()

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

            new_width = min(new_width, self.current_image_width)
            new_height = min(new_height, self.current_image_height)

            resized_current_image = current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_current_photo = ImageTk.PhotoImage(resized_current_image)

            main_img_view_canvas.delete('all')

            main_img_view_canvas.create_image(
                main_img_view_canvas_width // 2,
                main_img_view_canvas_height // 2,
                anchor=tk.CENTER,
                image=resized_current_photo
            )
            main_img_view_canvas.image = resized_current_photo

            page_data['photos']['current'] = resized_current_photo

    def show_img_page_arrow_buttons(self, left=True, right=True):
        page_data = self.page_wise_data.get('img')

        try:
            if left:
                left_button = page_data['buttons']['left']
                left_button_kwargs = page_data['kwargs']['left_button']
                left_button.place(**left_button_kwargs)

            if right:
                right_button = page_data['buttons']['right']
                right_button_kwargs = page_data['kwargs']['right_button']
                right_button.place(**right_button_kwargs)

        except Exception as e:
            pass

    def hide_img_page_arrow_buttons(self, left=True, right=True):
        page_data = self.page_wise_data.get('img')

        try:
            cur_x, cur_y = self.root.winfo_pointerxy()
            main_img_view_canvas = page_data['canvases']['main_img_view']

            canvas_x1 = main_img_view_canvas.winfo_rootx()
            canvas_y1 = main_img_view_canvas.winfo_rooty()
            canvas_x2 = canvas_x1 + main_img_view_canvas.winfo_width()
            canvas_y2 = canvas_y1 + main_img_view_canvas.winfo_height()

            if canvas_x1 <= cur_x <= canvas_x2 and canvas_y1 <= cur_y <= canvas_y2:
                return

            if left:
                left_button = page_data['buttons']['left']
                left_button.place_forget()

            if right:
                right_button = page_data['buttons']['right']
                right_button.place_forget()
        except Exception as e:
            pass

    def open_choose_img_files_dialog_and_show(self):
        selected_image_files = filedialog.askopenfilenames(
            title='Select image file(s)/directory',
            initialdir='/',
            filetypes=self.dialog_filetypes
        )

        if len(selected_image_files) > 0:
            self.current_image_file_path = os.path.abspath(selected_image_files[0])
            self.set_timeout(self.load_other_img_files, 'load_other_img_files')
            self.show_page('img')

    def hide_menubar(self):
        if not self.is_menubar_hidden:
            self.is_alt_key_menubar_hidden = True
            self.root.config(menu='')
            # self.root['menu'] = None

        self.is_menubar_hidden = True

    def show_menubar(self):
        if self.is_menubar_hidden:
            self.is_alt_key_menubar_hidden = False
            # self.root['menu'] = self.menubar
            self.root.config(menu=self.menubar)

        self.is_menubar_hidden = False

    def show_current_img(self, resizeframe=True):
        page_data = self.page_wise_data.get('img')

        main_img_view_canvas = page_data['canvases']['main_img_view']
        current_image = Image.open(self.current_image_file_path)
        current_photo = ImageTk.PhotoImage(current_image)

        current_image_file_base_name = os.path.basename(self.current_image_file_path)
        current_image_file_name = os.path.splitext(current_image_file_base_name)[0]
        self.root.title(self.APP_NAME + ' - ' + current_image_file_name)

        main_img_view_canvas.create_image(
            main_img_view_canvas.winfo_width() // 2,
            main_img_view_canvas.winfo_height() // 2,
            anchor=tk.CENTER,
            image=current_photo
        )
        main_img_view_canvas.image = current_photo

        self.current_image_width = current_image.width
        self.current_image_height = current_image.height

        if resizeframe and self._is_initial_dims:
            screen_width = self.screen_width * 0.9
            screen_height = self.screen_height * 0.8

            app_width = self.root.winfo_width()
            app_height = self.root.winfo_height() + page_data['labels']['current_img_file_size'].winfo_reqheight()

            if (screen_width >= self.current_image_width > app_width and
                    screen_height >= self.current_image_height > app_height):
                self.root.geometry(str(self.current_image_width) + 'x' + str(self.current_image_height))
            elif self.current_image_width > app_width or self.current_image_height > app_height:
                new_size_ratio = self.current_image_width / self.current_image_height

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

        current_img_dim = str(current_image.size[0]) + 'x' + str(current_image.size[1])
        current_imd_file_size = self.get_readable_file_size(self.current_image_file_path)

        page_data['string_vars']['current_img_dim'].set(current_img_dim)
        page_data['string_vars']['current_img_file_size'].set(current_imd_file_size)
        page_data['string_vars']['current_img_format'].set(current_image.format)

        page_data['string_vars']['current_img_idx'].set(
            (str(self.current_image_file_idx + 1) if self.current_image_file_idx is not None else '1') +
            '/' +
            (str(len(self.current_image_file_paths)) if len(self.current_image_file_paths) > 0 else '?')
        )

        page_data['images']['current'] = current_image
        page_data['photos']['current'] = current_photo

        page_data['main_frame'].focus_set()
        self.resize_img_page_items()

    def show_idx_img(self):
        self.current_image_file_path = self.current_image_file_paths[self.current_image_file_idx]
        self.show_current_img(resizeframe=False)

    def show_prev_img(self):
        if self.current_image_file_paths is not None and len(self.current_image_file_paths) > 0:
            self.current_image_file_idx -= 1

            if self.current_image_file_idx < 0:
                self.current_image_file_idx = len(self.current_image_file_paths) - 1

            self.show_img_page_arrow_buttons(right=False)
            self.set_timeout(self.hide_img_page_arrow_buttons, 'hide_img_page_arrow_buttons')
            self.show_idx_img()

    def show_next_img(self):
        if self.current_image_file_paths is not None and len(self.current_image_file_paths) > 0:
            self.current_image_file_idx += 1

            if self.current_image_file_idx == len(self.current_image_file_paths):
                self.current_image_file_idx = 0

            self.show_img_page_arrow_buttons(left=False)
            self.set_timeout(self.hide_img_page_arrow_buttons, 'hide_img_page_arrow_buttons')
            self.show_idx_img()

    def load_other_img_files(self):
        page_data = self.page_wise_data.get('img')
        current_image_dir_name = os.path.dirname(self.current_image_file_path)

        if not os.path.isdir(current_image_dir_name):
            raise ValueError(f"The provided path '{current_image_dir_name}' is not a valid directory.")

        file_extensions = tuple(self.APP_SUPPORTED_IMAGE_FILE_EXTENSIONS)
        file_paths = []

        for entry in os.scandir(current_image_dir_name):
            if entry.is_file():
                if entry.name.lower().endswith(file_extensions):
                    file_paths.append(entry.path)

        self.current_image_file_paths = file_paths
        current_image_file_idx = file_paths.index(self.current_image_file_path)

        if current_image_file_idx >= 0:
            self.current_image_file_idx = current_image_file_idx

            page_data['string_vars']['current_img_idx'].set(
                str(current_image_file_idx + 1) +
                '/' +
                str(len(file_paths))
            )
        else:
            self.current_image_file_idx = None

    def close_current_img(self):
        page_data = self.page_wise_data.get('img')

        page_data['images']['current'] = None
        page_data['photos']['current'] = None

        page_data['string_vars']['current_img_dir_path'].set('[NIL]')
        page_data['string_vars']['current_img_idx'].set('0/0')
        page_data['string_vars']['current_img_dim'].set('0x0')
        page_data['string_vars']['current_img_file_size'].set('0 B')
        page_data['string_vars']['current_img_format'].set('[NIL]')

        self.show_page('home')

    def minimize_window(self):
        self.root.state('iconic')  # Minimize the window

    def maximize_window(self):
        if self.is_window_fullscreen:
            self._is_restoring_after_fullscreen = False
            self._is_fullscreen_after_maximized = False
            self.root.attributes('-fullscreen', False)

        self.root.state('zoomed')  # Maximize the window

    def fullscreen_window(self):
        self.is_window_fullscreen = True
        self.is_window_minimized = False
        self.is_window_maximized = False
        self._is_restoring_after_fullscreen = True
        self._is_fullscreen_after_maximized = self.was_window_maximized_before

        self.root.attributes('-fullscreen', True)
        self.root.event_generate('<Configure>')

    def restore_window(self):
        if self.is_window_fullscreen:
            self._is_restoring_after_fullscreen = False
            self._is_first_menubar_resize_after_fullscreen = False
            self._is_first_statusbar_resize_after_fullscreen = False
            self.root.attributes('-fullscreen', False)

            if self._is_fullscreen_after_maximized:
                self.maximize_window()
                return

        self._is_restoring_after_fullscreen_in_img = False

        self.root.state('normal')

    def on_f11_keypress(self, event):
        if self.is_window_fullscreen:
            self.restore_window()
        else:
            self.fullscreen_window()

    def on_esc_keypress(self, event):
        if self.is_window_fullscreen:
            self.restore_window()

    def on_alt_keypress(self, event):
        if self.is_window_fullscreen:
            if self.current_page == 'home':
                if self.is_alt_key_menubar_hidden:
                    self.show_menubar()
                return

            if self.is_alt_key_menubar_hidden:
                self.is_alt_key_menubar_hidden = False
                self.show_menubar()
            else:
                self.is_alt_key_menubar_hidden = True
                self.hide_menubar()

            if self.current_page == 'img':
                if self.is_alt_key_statusbar_hidden:
                    self.is_alt_key_statusbar_hidden = False
                    self.page_wise_data['img']['other_frames']['status'].grid()
                else:
                    self.is_alt_key_statusbar_hidden = True
                    self.page_wise_data['img']['other_frames']['status'].grid_remove()

    @task_queue.task()
    def on_minimize(self, event):
        if self.root.state() == 'iconic':
            self.is_window_minimized = True

    @task_queue.task()
    def on_restore(self, event):
        if self.root.state() == 'normal':
            if self.is_window_minimized:
                return

            if self._is_restoring_after_fullscreen:
                self._is_restoring_after_fullscreen = False
                return

            if self._is_restoring_after_fullscreen_in_img:
                return
            else:
                self._is_restoring_after_fullscreen_in_img = self.current_page == 'img'

            if self.was_window_maximized_before:
                pos_x, pos_y = self.get_window_pos()

                self.root.geometry(
                    str(self.app_width_before_maximize) +
                    'x' +
                    str(self.app_height_before_maximize) +
                    f'+{pos_x}+{pos_y}'
                )

            self.is_window_minimized = False
            self.was_window_maximized_before = self.is_window_maximized
            self.is_window_maximized = False
            self.is_window_fullscreen = False
            self.on_resize_callback()

    @task_queue.task()
    def on_configure(self, event):
        if not ((self.app_width != event.width) or (self.app_height != event.height)):
            return

        self.app_width = event.width
        self.app_height = event.height

        if self.root.state() == 'zoomed':
            if self._is_resizing:
                return

            self._is_resizing = True

            if self.is_window_fullscreen and not self._is_fullscreen_after_maximized:
                self.is_window_fullscreen = False

            self.was_window_maximized_before = self.is_window_maximized
            self.is_window_maximized = not self.is_window_fullscreen
            self.is_window_minimized = False

            self.root.after(100, lambda: setattr(self, '_is_resizing', False))
            self.on_resize_callback()
        elif self.root.state() == 'normal':
            if not self.is_window_minimized:
                self.is_window_minimized = False
                self.was_window_maximized_before = self.is_window_maximized
                self.is_window_maximized = False

                if not self.is_window_fullscreen:
                    self.app_geometry_before_maximize = self.root.winfo_geometry()
                    self.app_width_before_maximize = self.app_width
                    self.app_height_before_maximize = self.app_height

            self.on_resize_callback()

        if self._is_initial_sizing_complete:
            if self.app_width != self.APP_WIDTH or self.app_height != self.APP_HEIGHT:
                self._is_initial_dims = False
        else:
            self.set_timeout(
                lambda: setattr(self, '_is_initial_sizing_complete', True),
                'set_is_initial_sizing_complete',
                750
            )

    @task_queue.task()
    def on_enter(self, event):
        if self.current_page == 'img':
            self.show_img_page_arrow_buttons()

    @task_queue.task()
    def on_leave(self, event):
        if self.current_page == 'img':
            self.hide_img_page_arrow_buttons()

    def on_resize_callback(self):
        self.set_timeout(self.resize_menubar_items, 'resize_menubar_items')

        if self.current_page == 'home':
            self.set_timeout(self.resize_home_page_items, 'resize_home_page_items')
        elif self.current_page == 'img':
            self.set_timeout(self.resize_img_page_items, 'resize_img_page_items')

    def on_home_page_click(self, event):
        self.open_choose_img_files_dialog_and_show()

    def run(self):
        self.init_app()
        self.show_page('home')
        self.root.mainloop()

    def set_timeout(self, func, funcid, ms=300):
        if self.timeout_callbacks.get(funcid) is None:
            self.timeout_callbacks[funcid] = True

            def callback():
                del self.timeout_callbacks[funcid]
                func()

            self.root.after(ms, callback)

    def get_window_pos(self):
        _, position = self.app_geometry_before_maximize.split('+', 1)
        x, y = map(int, position.split('+'))
        return x, y

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
