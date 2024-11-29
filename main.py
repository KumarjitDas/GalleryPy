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

APP_WIDTH = 640
APP_HEIGHT = 400
APP_NAME = 'GalleryPy'
APP_GEOMETRY = str(APP_WIDTH) + 'x' + str(APP_HEIGHT)

APP_MIN_WIDTH = APP_WIDTH // 2

APP_RESOURCES_PATH = os.path.abspath('resources/')
APP_IMAGES_PATH = os.path.join(APP_RESOURCES_PATH, 'images')

APP_READABLE_IMAGE_FILE_EXTENSIONS = [
    'bmp', 'dib', 'eps', 'gif', 'icns', 'ico', 'im', 'jpeg', 'jpe', 'jpg',
    'msp', 'pcx', 'png', 'ppm', 'pgm', 'pbm', 'pnm', 'sgi', 'rgb', 'bw',
    'spider', 'tga', 'tif', 'tiff', 'webp', 'xbm', 'pdf', 'psd', 'fits',
    'fit', 'pcd', 'dds'
]

APP_WRITABLE_IMAGE_FILE_EXTENSIONS = [
    'bmp', 'dds', 'eps', 'gif', 'ico', 'im', 'jpeg', 'jpg', 'jp2', 'pcx',
    'png', 'ppm', 'pgm', 'pbm', 'tiff', 'tif', 'webp', 'xbm', 'pdf'
]

APP_PAGES = ['home', 'img', 'img_error', 'dirs_files']

EMPTY_FOLDER_IMAGE_SIZE_MIN = 60
EMPTY_FOLDER_IMAGE_SIZE_MAX = 120

EMPTY_FOLDER_LABEL_FONT_SIZE_MIN = 8
EMPTY_FOLDER_LABEL_FONT_SIZE_MAX = 11

DEFAULT_TASK_DELAY_MS: int = 100


class TaskQueue:
    """
    A centralized queueing system for managing sequential execution of tasks with support for debouncing.

    Attributes:
        root (tk.Tk): The root Tkinter window for managing the event loop.
        task_queues (dict): A dictionary mapping task names to their respective queues.
        running_tasks (dict): A dictionary tracking whether a task is currently running.
        debounce_tasks (dict): A dictionary tracking the last scheduled task for each function.

    Methods:
        set_root(root):
            Sets the Tkinter root window for managing delays and callbacks.
        enqueue_task(func_name, task, debounce=False, delay=50):
            Adds a task to the queue for the given function name, with optional debouncing.
        process_queue(func_name):
            Executes the next task in the queue for the given function name.
        finish_task(func_name):
            Marks the current task for the given function name as complete and processes the next task.
        task(debounce=False, delay=50):
            A decorator to enqueue a function as a task, with optional debouncing.

    Decorators:
        task():
            A decorator to enqueue a function as a task with optional debouncing. This ensures the function
            executes sequentially or as the last task in a burst of rapid calls.

            Usage:
                @task_queue.task(debounce=True, delay=100)
                def my_task():
                    # Task logic here
                    pass

            Returns:
                Callable: The wrapped function, which will automatically be added to the task queue when called.
    """

    def __init__(self, root: Union[None, tk.Tk]=None) -> None:
        self.root: Union[None, tk.Tk] = root
        self.task_queues: dict[str, Queue[Callable[..., Any]]] = {}  # Task queues for each function
        self.running_tasks: dict[str, bool] = {}  # Track running states for each function
        self.debounce_tasks: dict[str, Union[None, str]] = {}  # Track last scheduled task IDs for debouncing

    def set_root(self, root: tk.Tk) -> None:
        """Set the Tkinter root window."""
        self.root = root

    def enqueue_task(
            self, func_name: str, task: Callable[..., Any], debounce: bool=False, delay: int=50
    ) -> None:
        """
        Add a task to the queue for the given function with optional debouncing.

        Args:
            func_name (str): The name of the function being queued.
            task (Callable[..., Any]): The task to be executed.
            debounce (bool): Whether to enable debouncing for this task.
            delay (int): Delay in milliseconds for debounced tasks.
        """
        if debounce:
            # Cancel the last scheduled task if it exists
            if func_name in self.debounce_tasks and self.debounce_tasks[func_name] is not None:
                self.root.after_cancel(self.debounce_tasks[func_name])

            # Schedule the new task
            # noinspection PyTypeChecker
            self.debounce_tasks[func_name] = self.root.after(delay, lambda: self._add_task_to_queue(func_name, task))
        else:
            self._add_task_to_queue(func_name, task)

    def _add_task_to_queue(self, func_name: str, task: Callable[..., Any]) -> None:
        """Internal method to add a task to the queue."""
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

    def task(self, debounce: bool = False, delay: int = 50) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator to enqueue tasks using the function's name, with optional debouncing.

        Args:
            debounce (bool): Whether to enable debouncing for the task.
            delay (int): Delay in milliseconds for debounced tasks.

        Returns:
            Callable: The wrapped function.
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args, **kwargs) -> None:
                func_name: str = func.__name__
                self.enqueue_task(func_name, lambda: func(*args, **kwargs), debounce=debounce, delay=delay)

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
        self.previous_state: Union[None, str] = None
        self.transitions: dict = {}
        self.state_actions: dict = {}

    def get_state(self):
        """Returns the current state of the FSM."""
        return self.current_state

    def get_previous_state(self):
        """Returns the previous state of the FSM."""
        return self.previous_state

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

        print(f'Transition: {self.current_state} → {new_state}')

        prev_state: str = self.current_state
        self.current_state = new_state
        self.previous_state = prev_state

        # Execute the action for the new state
        if action := self.state_actions.get(new_state):
            action(new_state, prev_state)


# noinspection PyTypedDict,PyCallingNonCallable,DuplicatedCode,PyTypeChecker
class App:
    task_queue = TaskQueue()
    dependency_manager = DependencyManager()

    window_fsm = FiniteStateMachine(initial_state='__init__')
    page_fsm = FiniteStateMachine(initial_state='__init__')
    cursor_fsm = FiniteStateMachine(initial_state='__init__')
    menu_status_fsm = FiniteStateMachine(initial_state='__init__')
    img_nav_fsm = FiniteStateMachine(initial_state='__init__')

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

        for page_name in APP_PAGES:
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

        self.is_window_fullscreen = False
        self.window_fsm.add_state('__init__', ['restored', 'resized', 'maximized', 'minimized', 'fullscreen'], self.on_normal_state)
        self.window_fsm.add_state('restored', ['resized', 'maximized', 'minimized', 'fullscreen'], self.on_normal_state)
        self.window_fsm.add_state('resized', ['restored', 'maximized', 'minimized', 'fullscreen'], self.on_normal_state)
        self.window_fsm.add_state('maximized', ['restored', 'fullscreen'], self.on_maximized_state)
        self.window_fsm.add_state('minimized', ['restored'], self.on_minimized_state)
        self.window_fsm.add_state('fullscreen', ['restored', 'maximized'], self.on_fullscreen_state)

        self.page_fsm.add_state('__init__', ['home', 'img', 'img_error', 'dirs_files'])
        self.page_fsm.add_state('home', ['img', 'img_error', 'dirs_files'], self.on_home_page_state)
        self.page_fsm.add_state('img', ['home', 'img_error', 'dirs_files'], self.on_img_page_state)
        self.page_fsm.add_state('img_error', ['home', 'img', 'dirs_files'], self.on_img_error_page_state)
        self.page_fsm.add_state('dirs_files', ['home', 'img', 'img_error'], self.on_dirs_files_page_state)

        self.cursor_fsm.add_state('__init__', ['enter', 'leave'])
        self.cursor_fsm.add_state('enter', ['leave'], self.on_cursor_enter_state)
        self.cursor_fsm.add_state('leave', ['enter'], self.on_cursor_leave_state)

        self.menu_status_fsm.add_state('__init__', ['hidden', 'shown'])
        self.menu_status_fsm.add_state('hidden', ['shown'], self.on_menu_status_hidden_state)
        self.menu_status_fsm.add_state('shown', ['hidden'], self.on_menu_status_shown_state)

        self.img_nav_fsm.add_state('__init__', ['all_in_dir', 'selected', 'single_zooming'])
        self.img_nav_fsm.add_state('all_in_dir', ['single_zooming'])
        self.img_nav_fsm.add_state('selected', ['all_in_dir', 'single_zooming'])
        self.img_nav_fsm.add_state('single_zooming', ['all_in_dir', 'selected'])

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.app_width = self.root.winfo_width()
        self.app_height = self.root.winfo_height()
        self.app_geometry_before_maximized = self.root.winfo_geometry()

        self.current_image_width = 0
        self.current_image_height = 0

        self.dialog_filetypes = (
            ('Image Files', ' '.join([f'*.{ext}' for ext in APP_READABLE_IMAGE_FILE_EXTENSIONS])),
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

        self.root.title(APP_NAME)
        self.root.geometry(APP_GEOMETRY)
        self.root.config(menu=self.menubar)

        self.root.bind_all('<Unmap>', self.on_minimize_event_handler)
        self.root.bind_all('<Map>', self.on_restore_event_handler)
        self.root.bind_all('<Configure>', self.on_configure_event_handler)
        self.root.bind_all('<Enter>', self.on_cursor_enter_event_handler)
        self.root.bind_all('<Leave>', self.on_cursor_leave_event_handler)

        self.root.bind_all('<F11>', self.on_f11_keypress)
        self.root.bind_all('<Escape>', self.on_esc_keypress)
        self.root.bind_all('<Alt_L>', self.on_alt_keypress)
        self.root.bind_all('<Alt_R>', self.on_alt_keypress)

        self.container.pack(side=tk.TOP, anchor=tk.N, fill=tk.BOTH, expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def set_min_width_height(self):
        min_width = APP_MIN_WIDTH

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

        for file_ext in APP_WRITABLE_IMAGE_FILE_EXTENSIONS:
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

        empty_folder_label_font = Font(size=EMPTY_FOLDER_LABEL_FONT_SIZE_MIN, weight='bold')

        empty_folder_label = ttk.Label(
            master=center_frame,
            text="No image file(s)/directory have been chosen.\nOpen file(s)  Ctrl + O",
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

    def load_page_home_items(self):
        page_data = self.page_wise_data.get('home')

        image_size = EMPTY_FOLDER_IMAGE_SIZE_MAX
        empty_folder_image_path = os.path.join(APP_IMAGES_PATH, 'empty-folder.png')
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

        self.root.title(APP_NAME)

        self.menu_items['file'].entryconfig('Close image', state=tk.DISABLED)
        self.menu_items['file'].entryconfig('Delete image', state=tk.DISABLED)

        self.menu_items['edit'].entryconfig('Copy image', state=tk.DISABLED)
        self.menu_items['edit'].entryconfig('Copy path', state=tk.DISABLED)
        self.menu_items['edit'].entryconfig('Resize image', state=tk.DISABLED)

        self.handle_home_page_items_on_resize()

    def load_page_img_items(self):
        if self.current_image_file_path is None:
            self.page_fsm.change_state('img_error')
        else:
            try:
                page_data = self.page_wise_data.get('img')
                main_frame = page_data['main_frame']

                left_arrow_image_path = os.path.join(APP_IMAGES_PATH, 'left-arrow.png')
                right_arrow_image_path = os.path.join(APP_IMAGES_PATH, 'right-arrow.png')
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

                self.show_current_img()

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
                self.page_fsm.change_state('img_error')

    def load_page_img_error_items(self):
        pass

    def load_page_dirs_files_items(self):
        pass

    def handle_menubar_items_on_resize(self):
        if self.window_fsm.get_state() == 'maximized':
            self.menu_items['view__window'].entryconfig('Maximize', state=tk.DISABLED)
            self.menu_items['view__window'].entryconfig('Fullscreen', state=tk.ACTIVE)
            self.menu_items['view__window'].entryconfig('Restore', state=tk.ACTIVE)
        elif self.window_fsm.get_state() == 'fullscreen':
            self.menu_items['view__window'].entryconfig('Maximize', state=tk.ACTIVE)
            self.menu_items['view__window'].entryconfig('Fullscreen', state=tk.DISABLED)
            self.menu_items['view__window'].entryconfig('Restore', state=tk.ACTIVE)

            if self.page_fsm.get_state() == 'img':
                self.menu_status_fsm.change_state('hidden')
        else:
            self.menu_items['view__window'].entryconfig('Maximize', state=tk.ACTIVE)
            self.menu_items['view__window'].entryconfig('Fullscreen', state=tk.ACTIVE)
            self.menu_items['view__window'].entryconfig('Restore', state=tk.DISABLED)

        if self.window_fsm.get_state() != 'fullscreen':
            if self.page_fsm.get_state() == 'img':
                self.menu_status_fsm.change_state('shown')

    def handle_home_page_items_on_resize(self):
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
        desired_size = max(EMPTY_FOLDER_IMAGE_SIZE_MIN, min(desired_size, EMPTY_FOLDER_IMAGE_SIZE_MAX))

        desired_font_size = int(min(root_width, root_height) * 0.02)
        desired_font_size = max(EMPTY_FOLDER_LABEL_FONT_SIZE_MIN, min(desired_font_size, EMPTY_FOLDER_LABEL_FONT_SIZE_MAX))

        empty_folder_canvas.config(width=desired_size, height=desired_size)
        empty_folder_font.config(size=desired_font_size)

        resized_image = empty_folder_image.copy()
        resized_image.thumbnail((desired_size, desired_size), Image.Resampling.LANCZOS)
        empty_folder_photo = ImageTk.PhotoImage(resized_image)

        empty_folder_canvas.delete('all')

        empty_folder_canvas.create_image(
            empty_folder_canvas.winfo_width() // 2,
            empty_folder_canvas.winfo_height() // 2,
            image=empty_folder_photo,
            anchor=tk.CENTER
        )

        page_data['photos']['empty_folder'] = empty_folder_photo

    def handle_img_page_items_on_resize(self):
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

            new_width = min(new_width, self.current_image_width)
            new_height = min(new_height, self.current_image_height)

            resized_current_image = current_image.copy()
            resized_current_image.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
            # resized_current_image = current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
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

    def handle_all_items_on_resize(self):
        self.handle_menubar_items_on_resize()

        if self.page_fsm.get_state() == 'home':
            self.handle_home_page_items_on_resize()
        elif self.page_fsm.get_state() == 'img':
            self.handle_img_page_items_on_resize()

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
            if len(selected_image_files) == 1:
                self.current_image_file_path = os.path.abspath(selected_image_files[0])
                self.load_other_img_files_of_current_dir()
            else:
                self.current_image_file_paths = selected_image_files
                self.load_other_img_files()

            self.page_fsm.change_state('img')

    def hide_menubar(self):
        self.root.config(menu='')
        # self.root['menu'] = None

    def show_menubar(self):
        # self.root['menu'] = self.menubar
        self.root.config(menu=self.menubar)

    def show_current_img(self, resizeframe=True):
        page_data = self.page_wise_data.get('img')

        main_img_view_canvas = page_data['canvases']['main_img_view']
        current_image = Image.open(self.current_image_file_path)
        current_photo = ImageTk.PhotoImage(current_image)

        current_image_file_base_name = os.path.basename(self.current_image_file_path)
        current_image_file_name = os.path.splitext(current_image_file_base_name)[0]
        self.root.title(APP_NAME + ' - ' + current_image_file_name)

        main_img_view_canvas.create_image(
            main_img_view_canvas.winfo_width() // 2,
            main_img_view_canvas.winfo_height() // 2,
            anchor=tk.CENTER,
            image=current_photo
        )
        main_img_view_canvas.image = current_photo

        self.current_image_width = current_image.width
        self.current_image_height = current_image.height

        if resizeframe:  # and self._is_initial_dims:
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
                    str(new_width if new_width >= APP_WIDTH else APP_WIDTH) +
                    'x' +
                    str(new_height if new_height >= APP_HEIGHT else APP_HEIGHT)
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
        self.handle_img_page_items_on_resize()

    def show_idx_img(self):
        self.current_image_file_path = self.current_image_file_paths[self.current_image_file_idx]
        self.show_current_img(resizeframe=False)

    def show_prev_img(self):
        if self.current_image_file_paths is not None and len(self.current_image_file_paths) > 0:
            self.current_image_file_idx -= 1

            if self.current_image_file_idx < 0:
                self.current_image_file_idx = len(self.current_image_file_paths) - 1

            self.show_img_page_arrow_buttons(right=False)
            self.show_idx_img()
            self.hide_img_page_arrow_buttons()

    def show_next_img(self):
        if self.current_image_file_paths is not None and len(self.current_image_file_paths) > 0:
            self.current_image_file_idx += 1

            if self.current_image_file_idx == len(self.current_image_file_paths):
                self.current_image_file_idx = 0

            self.show_img_page_arrow_buttons(left=False)
            self.show_idx_img()
            self.hide_img_page_arrow_buttons()

    def load_other_img_files_of_current_dir(self):
        page_data = self.page_wise_data.get('img')
        current_image_dir_name = os.path.dirname(self.current_image_file_path)

        if not os.path.isdir(current_image_dir_name):
            raise ValueError(f"The provided path '{current_image_dir_name}' is not a valid directory.")

        file_extensions = tuple(APP_READABLE_IMAGE_FILE_EXTENSIONS)
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

    def load_other_img_files(self):
        page_data = self.page_wise_data.get('img')
        current_image_dir_name = os.path.dirname(self.current_image_file_paths[0])

        if not os.path.isdir(current_image_dir_name):
            raise ValueError(f"The provided path '{current_image_dir_name}' is not a valid directory.")

        self.current_image_file_path = self.current_image_file_paths[0]
        current_image_file_idx = self.current_image_file_paths.index(self.current_image_file_path)

        if current_image_file_idx >= 0:
            self.current_image_file_idx = current_image_file_idx

            page_data['string_vars']['current_img_idx'].set(
                str(current_image_file_idx + 1) +
                '/' +
                str(len(self.current_image_file_paths))
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

        self.page_fsm.change_state('home')

    def minimize_window(self):
        self.root.attributes('-fullscreen', False)
        self.is_window_fullscreen = False
        self.root.state('iconic')  # Minimize the window

    def maximize_window(self):
        self.root.attributes('-fullscreen', False)
        self.is_window_fullscreen = False
        self.root.state('zoomed')  # Maximize the window

    def fullscreen_window(self):
        self.root.attributes('-fullscreen', True)  # Make the window fullscreen
        self.is_window_fullscreen = True
        self.on_fullscreen_event_handler(None)

    def restore_window(self):
        self.root.attributes('-fullscreen', False)
        self.is_window_fullscreen = False

        if self.window_fsm.get_previous_state() == 'maximized':
            self.root.state('zoomed')  # Maximize the window
        else:
            self.root.state('normal')  # Restore the window

    def on_f11_keypress(self, event):
        if self.window_fsm.get_state() == 'fullscreen':
            self.restore_window()
        else:
            self.fullscreen_window()

    def on_esc_keypress(self, event):
        if self.window_fsm.get_state() == 'fullscreen':
            self.restore_window()

    def on_alt_keypress(self, event):
        if self.window_fsm.get_state() == 'fullscreen':
            if self.page_fsm.get_state() == 'img':
                if self.menu_status_fsm.get_state() == 'shown':
                    self.menu_status_fsm.change_state('hidden')
                else:
                    self.menu_status_fsm.change_state('shown')

    def on_page_state(self, page_name: str, current_state: str, previous_state: str):
        page_data = self.page_wise_data.get(page_name)

        if page_data:
            frame = page_data.get('main_frame')
            page_item_loader = page_data.get('page_item_loader')

            frame.tkraise()
            page_item_loader()
        else:
            print(f"Page '{page_name}' does not exist.")

    def on_home_page_state(self, current_state: str, previous_state: str):
        self.on_page_state('home', current_state, previous_state)

    def on_img_page_state(self, current_state: str, previous_state: str):
        self.on_page_state('img', current_state, previous_state)

    def on_img_error_page_state(self, current_state: str, previous_state: str):
        self.on_page_state('img_error', current_state, previous_state)

    def on_dirs_files_page_state(self, current_state: str, previous_state: str):
        self.on_page_state('dirs_files', current_state, previous_state)

    def on_normal_state(self, current_state: str, previous_state: str):
        self.handle_all_items_on_resize()

    def on_maximized_state(self, current_state: str, previous_state: str):
        self.handle_all_items_on_resize()
        self.root.after(DEFAULT_TASK_DELAY_MS + 100, self.handle_all_items_on_resize)

    def on_minimized_state(self, current_state: str, previous_state: str):
        pass

    def on_fullscreen_state(self, current_state: str, previous_state: str):
        self.handle_all_items_on_resize()
        self.root.after(DEFAULT_TASK_DELAY_MS + 100, self.handle_all_items_on_resize)

    def on_cursor_enter_state(self, current_state: str, previous_state: str):
        if self.page_fsm.get_state() == 'img':
            self.show_img_page_arrow_buttons()

    def on_cursor_leave_state(self, current_state: str, previous_state: str):
        if self.page_fsm.get_state() == 'img':
            self.hide_img_page_arrow_buttons()

    def on_menu_status_hidden_state(self, current_state: str, previous_state: str):
        self.hide_menubar()

        if self.page_fsm.get_state() == 'img':
            self.page_wise_data['img']['other_frames']['status'].grid_remove()

    def on_menu_status_shown_state(self, current_state: str, previous_state: str):
        self.show_menubar()

        if self.page_fsm.get_state() == 'img':
            self.page_wise_data['img']['other_frames']['status'].grid()

    @task_queue.task(debounce=True, delay=DEFAULT_TASK_DELAY_MS)
    def on_minimize_event_handler(self, event):
        if self.root.state() == 'iconic':
            self.window_fsm.change_state('minimized')

    @task_queue.task(debounce=True, delay=DEFAULT_TASK_DELAY_MS)
    def on_restore_event_handler(self, event):
        if self.root.state() == 'normal' and not self.is_window_fullscreen:
            if self.window_fsm.get_state() == 'maximized' and self.window_fsm.get_previous_state() == 'fullscreen':
                pos_x, pos_y = self.get_window_pos(self.app_geometry_before_maximized)
                self.root.geometry(f'{str(self.app_width)}x{str(self.app_height)}+{str(pos_x)}+{str(pos_y)}')

            self.window_fsm.change_state('restored')

    def on_configure_event_handler(self, event):
        if ((self.window_fsm.get_state() == 'restored' or self.window_fsm.get_state() == 'resized') and
                self.root.state() != 'zoomed'):
            self.app_geometry_before_maximized = self.root.winfo_geometry()

        if not ((self.app_width != event.width) or (self.app_height != event.height)):
            return

        if self.root.state() == 'zoomed':
            if self.window_fsm.get_state() != 'maximized' and not self.is_window_fullscreen:
                self.on_maximize_event_handler(event)
        elif self.root.state() == 'normal':
            if self.window_fsm.get_state() == 'restored':
                self.app_width = event.width
                self.app_height = event.height
                self.window_fsm.change_state('resized')
            else:
                self.on_restore_event_handler(event)

    @task_queue.task(debounce=True, delay=DEFAULT_TASK_DELAY_MS)
    def on_maximize_event_handler(self, event):
        self.window_fsm.change_state('maximized')

    @task_queue.task(debounce=True, delay=DEFAULT_TASK_DELAY_MS)
    def on_fullscreen_event_handler(self, event):
        self.window_fsm.change_state('fullscreen')

    @task_queue.task(debounce=True, delay=DEFAULT_TASK_DELAY_MS)
    def on_cursor_enter_event_handler(self, event):
        self.cursor_fsm.change_state('enter')

    @task_queue.task(debounce=True, delay=DEFAULT_TASK_DELAY_MS)
    def on_cursor_leave_event_handler(self, event):
        self.cursor_fsm.change_state('leave')

    def on_home_page_click(self, event):
        self.open_choose_img_files_dialog_and_show()

    def run(self):
        self.init_app()
        self.page_fsm.change_state('home')
        self.root.mainloop()

    def get_window_pos(self, geometry: Union[None, str]=None):
        if geometry is None:
            geometry = self.root.winfo_geometry()

        _, position = geometry.split('+', 1)
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
