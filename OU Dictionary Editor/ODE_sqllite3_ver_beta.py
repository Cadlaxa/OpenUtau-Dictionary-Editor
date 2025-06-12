import tkinter as tk
from Assets.modules.sv_ttk import sv_ttk
from tkinter import filedialog, messagebox, ttk, Toplevel, BOTH, scrolledtext, Canvas
import os, sys, re
sys.path.append('.')
from pathlib import Path as P
from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.compat import StringIO
import tkinter.font as tkFont
import configparser
from Assets.modules import requests
import zipfile, colorsys
from zipfile import ZipFile
import shutil, threading, subprocess, copy, platform, gzip, pyglet, pyperclip, io, csv, importlib
import ctypes as ct
import json, pickle, darkdetect, webbrowser, markdown2, glob, chardet
from tkhtmlview import HTMLLabel
from collections import defaultdict, OrderedDict
import onnxruntime as ort
import numpy as np
from tkinterdnd2 import TkinterDnD, DND_FILES
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image, UnidentifiedImageError, ImageFile

import sqlite3 # Import SQLite

# Plugins
from Assets.plugins.generate_yaml_template import read_symbol_types_from_yaml
from Assets.G2p.ExternalG2pModelManager import G2pModelManager
from Assets.plugins.generate_yaml_template import generate_yaml_template_from_reclist
from Assets.plugins.default_phoneme_system import default_csv_content

# Directories
TEMPLATES = P('./Templates')
LOCAL = P('./Templates/Localizations')
ASSETS = P('./Assets')
ICON = P('./Assets/icon.png')
ICON1 = P('./Assets/icon.ico')
CACHE = P('./Cache')
PHONEME_SYSTEMS = TEMPLATES / P('phoneme systems.csv')
TCL_THEME_DIR = os.path.expanduser("./Assets/modules/sv_ttk")
HUE_LUMEN = P("Assets/modules/sv_ttk/theme/luminance.png")
THEME_DIR = os.path.expanduser("./Assets/modules/sv_ttk/theme")
# soon
AUTOSAVES = P('./Autosaves and Backups')

# for treeview only but ruamel.yaml will handle them automatically
def escape_special_characters(phoneme):
        # Check if the first character is a special character that might require quoting
        if phoneme[0] in r"[{}\@#\$%\^&\*\(\)\+=<>\|\[\\\];'\",\./\?・:~]+":
            return f"'{phoneme}'"
        pattern = r"[{}\@#\$%\^&\*\(\)\+=<>\|\[\\\];'\",\./\?・:~]+$"
        if re.search(pattern, phoneme):
            return f"'{phoneme}'"
        return phoneme

def escape_symbols(symbol):
    # Convert symbol to string in case it's not
    symbol_str = str(symbol)
    pattern1 = r"[{}\@#\$%\^&\*\(\)\+=<>\|\[\\\];'\",\./\?・:~]+$"
    pattern2 = r"^[{}\@#\$%\^&\*\(\)\+=<>\|\[\\\];'\",\./\?・:~]+"
    if re.search(pattern1, symbol_str) or re.search(pattern2, symbol_str):
        return f"'{symbol_str}'"
    return symbol_str

def escape_grapheme(grapheme):
        # Check if the first character is a special character that might require quoting
        if grapheme[0] in r"[{}\@#\$%\^&\*\(\)\+=<>\|\[\\\];'\",\./\?・]+":
            return f'"{grapheme}"'
        if re.search(r"\b(true|false|yes|no|on|off)\b", grapheme, re.IGNORECASE):
            return f"'{grapheme}'"
        return grapheme

class CacheHandler(FileSystemEventHandler):
    def __init__(self, update_callback):
        self.update_callback = update_callback

    def on_any_event(self, event):
        # Call the update callback whenever an event occurs
        self.update_callback()

class DownloadProgressDialog:
    def __init__(self, parent, max_value):
        self.parent = parent
        self.progress_window = Toplevel(parent)
        self.progress_window.title("Downloading Update")
        
        self.progress = ttk.Progressbar(self.progress_window, orient="horizontal", length=300, mode='determinate')
        self.progress.pack(padx=20, pady=20)
        self.progress['maximum'] = max_value
        
        self.icon()
        self.center_window()
        self.progress_window.resizable(False, False)

    def set_progress(self, value):
        self.progress['value'] = value
        self.progress_window.update_idletasks()

    def close(self):
        self.progress_window.destroy()
    
    def icon(self, window=None):
        if window is None:
            window = self.progress_window
        if os.path.exists(ICON):
            img = tk.PhotoImage(file=ICON)
            window.tk.call('wm', 'iconphoto', window._w, img)

    def center_window(self):
        self.progress_window.update_idletasks()
        width = self.progress_window.winfo_width()
        height = self.progress_window.winfo_height()
        x = (self.progress_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.progress_window.winfo_screenheight() // 2) - (height // 2) - 30
        self.progress_window.geometry(f'{width}x{height}+{x}+{y}')

class Dictionary(TkinterDnD.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- SQLite Database Setup ---
        self.db_conn = None
        self.cursor = None
        self._setup_database()
        # --- End SQLite Database Setup ---
        config = configparser.ConfigParser()
        self.g2p_manager = G2pModelManager()
        config.read('settings.ini')
        selected_theme = config.get('Settings', 'theme', fallback='System')
        selected_accent = config.get('Settings', 'accent', fallback='#00FFA9')
        self.theme_var = tk.StringVar(value=selected_theme)
        self.accent_var = tk.StringVar(value=selected_accent)
        selected_local = config.get('Settings', 'localization', fallback='English')
        self.localization_var = tk.StringVar(value=selected_local)
        self.current_local = config.get('Settings', 'current_local', fallback='English')
        self.local_var = tk.StringVar(value=self.current_local)
        self.selected_g2p = config.get('Settings', 'g2p', fallback="Arpabet-Plus G2p")
        self.g2p_var = tk.StringVar(value=self.selected_g2p)
        self.current_version = "v1.7.9"

        # Set window title
        self.base_title = "OpenUTAU Dictionary Editor"
        self.title(self.base_title)
        self.current_filename = None
        self.file_modified = False # This flag might need re-evaluation with DB
        self.localizable_widgets = {}
        self.current_entry_widgets = {}
        self.session = requests.Session()
        
        # Template folder directory
        self.Templates = self.read_template_directory()
        self.config_file = "settings.ini"
        self.load_last_theme()

        # Dictionary to hold the data - NO LONGER IN MEMORY FOR ENTRIES!
        self.dictionary = {}
        # self.comments = {} # Comments will also be stored in DB if needed or handled separately
        
        # Symbols and replacements will be fetched from DB
        self.symbols = {} # Used as a temporary cache for the symbol editor, synced with DB
        self.symbols_list = [] # Used for Treeview in symbol editor, populated from self.symbols
        self.replacements = [] # Loaded from DB, used for processing

        # --- Undo/Redo - Temporarily removed due to database backend complexity ---
        # self.undo_stack = []
        # self.redo_stack = []
        # --- End Undo/Redo Removal ---

        self.copy_stack = []
        self.plugin_file = None
        self.phoneme_map = {}
        self.systems = []
        self.file_opened = None
        self.tooltips = []
        self.word_to_item_id = {}  # Dictionary for fast lookup of Treeview items (for visible items)
        self.hue_cache = {}
        self.localization = {}


        self.template_var = tk.StringVar(value="Custom Template")
        self.entries_window = None
        self.text_widget = None
        self.replace_window = None
        self.drag_window = None
        self.drag_window_sym = None
        self.symbol_editor_window = None
        self.g2p_model = None
        self.remove_numbered_accents_var = tk.BooleanVar()
        self.remove_numbered_accents_var.set(False)  # Default is off
        self.lowercase_phonemes_var = tk.BooleanVar()
        self.lowercase_phonemes_var.set(False)  # Default is off
        self.current_order = [] # To store the manual order of entries (will be managed in DB if needed)
        self.styling()
        self.create_widgets()
        self.init_localization()
        t = threading.Thread(target=darkdetect.listener, args=(self.toggle_theme,))
        t.daemon = True
        t.start()
        self.icon()
        # Start update check in a non-blocking way
        threading.Thread(target=self.bg_updates, daemon=True).start()
        threading.Thread(target=self.update_localization_files, daemon=True).start()
        self.load_whats_new_state()
        self.check_and_update_version()
        # Check if "What's New" should be displayed
        if not self.whats_new_opened or self.is_new_version:
            self.whats_new()

    def _setup_database(self):
        """Initializes the SQLite database and creates necessary tables."""
        try:
            self.db_conn = sqlite3.connect('dictionary.db')
            self.cursor = self.db_conn.cursor()

            # Create entries table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grapheme TEXT UNIQUE COLLATE NOCASE, -- Case-insensitive unique grapheme
                    phonemes TEXT, -- Store phonemes as JSON string
                    original_order INTEGER -- To preserve insertion order for full dictionary rebuilds
                )
            ''')
            # Create an index on the grapheme column for faster lookups
            self.cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_grapheme ON entries (grapheme COLLATE NOCASE)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_grapheme_prefix ON entries (grapheme ASC)') # For lazy loading

            # Create symbols table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE COLLATE NOCASE,
                    type TEXT, -- Store type as string
                    rename TEXT -- Store rename as JSON string for list of renames
                )
            ''')
            self.cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_symbol ON symbols (symbol COLLATE NOCASE)')

            # Create replacements table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS replacements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_symbol TEXT,
                    to_symbol TEXT
                )
            ''')
            self.db_conn.commit()
            print("SQLite database initialized successfully.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")
            sys.exit(1) # Exit if database cannot be set up


    def bg_updates(self):
        if not self.is_connected():
            return
        try:
            self.response = requests.get("https://api.github.com/repos/Cadlaxa/OpenUtau-Dictionary-Editor/releases/latest", timeout=5)
            self.response.raise_for_status()
            self.latest_release = self.response.json()
            self.latest_version_tag = self.latest_release['tag_name']
            self.latest_asset = self.latest_release['assets'][0]  # first asset is the zip file

            if self.latest_version_tag > self.current_version:
                self.check_for_updates()
        except requests.RequestException as e:
            messagebox.showerror("Update Error", f"{self.localization.get('update_error', 'Could not check for updates: ')} {str(e)}")
    
    def icon(self, window=None):
        if window is None:
            window = self
        img = tk.PhotoImage(file=ICON)
        window.tk.call('wm', 'iconphoto', window._w, img)

    def styling(self):
        # Load font files
        pyglet.options['win32_gdi_font'] = True
        font_files = {
            'en_bold': 'NotoSans-Bold.ttf',
            'jp_bold': 'NotoSansJP-Bold.ttf',
            'hk_bold': 'NotoSansHK-Bold.ttf',
            'sc_bold': 'NotoSansSC-Bold.ttf',
            'tc_bold': 'NotoSansTC-Bold.ttf',
            'en_reg': 'NotoSans-Regular.ttf',
            'jp_reg': 'NotoSansJP-Regular.ttf',
            'hk_reg': 'NotoSansHK-Regular.ttf',
            'sc_reg': 'NotoSansSC-Regular.ttf',
            'tc_reg': 'NotoSansTC-Regular.ttf',
        }
        # Register fonts
        for key, filename in font_files.items():
            pyglet.font.add_file(os.path.join(ASSETS, f"Fonts/{filename}"))
        # Assign font names
        self.font_en = 'Noto Sans Bold'
        self.font_jp = 'Noto Sans JP Bold'
        self.font_hk = 'Noto Sans HK Bold'
        self.font_sc = 'Noto Sans SC Bold'
        self.font_tc = 'Noto Sans TC Bold'
        self.font_en_R = 'Noto Sans Regular'
        self.font_jp_R = 'Noto Sans JP Regular'
        self.font_hk_R = 'Noto Sans HK Regular'
        self.font_sc_R = 'Noto Sans SC Regular'
        self.font_tc_R = 'Noto Sans TC Regular'

        # Read settings.ini to determine current_local
        config = configparser.ConfigParser()
        config.read('settings.ini')

        # Default to English if settings.ini is missing or does not have a valid section
        if config.has_section('Settings'):
            self.current_local = config.get('Settings', 'current_local', fallback='English')
        else:
            self.current_local = 'English'

        # Define fonts for different languages
        n = 10
        s = 9
        font_mapping = {
            "English": (self.font_en, self.font_en_R),
            "Japanese": (self.font_jp, self.font_jp_R),
            "Chinese (Traditional)": (self.font_tc, self.font_tc_R),
            "Chinese (Simplified)": (self.font_sc, self.font_sc_R),
            "Cantonese": (self.font_hk, self.font_hk_R),
        }

        # Default to English if current_local is not recognized
        font_family, tree_font_family = font_mapping.get(self.current_local, (self.font_en, self.font_en_R))
        # Set fonts
        self.font = tkFont.Font(family=font_family, size=n)
        self.font_s = tkFont.Font(family=font_family, size=s)
        self.tree_font = tkFont.Font(family=tree_font_family, size=n)
        self.tree_font_b = tkFont.Font(family=font_family, size=n)
        self.widget_style()

    def widget_style(self):
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", font=self.font)
        self.style.configure("TButton", font=self.font)
        self.style.configure("TCheckbutton", font=self.font)
        self.style.configure("TRadiobutton", font=self.font)
        if hasattr(self, 'ttk.Button'):
            ttk.Button.config(style="Accent.TButton")

    def change_font_size(self, delta):
        for font in [self.tree_font, self.tree_font_b]:
            current_size = font['size']
            new_size = max(10, current_size + delta)
            font.configure(size=new_size)
    
    # Tooltips
    def load_tooltip_checkbox_state(self):
        # Load tooltip checkbox state from config
        config = configparser.ConfigParser()
        config.read(self.config_file)
        try:
            tooltip_enabled = config.getboolean('Settings', 'Tooltip_Enabled')
            self.tooltip_checkbox_var.set(tooltip_enabled)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.tooltip_checkbox_var.set(True)
            print("tooltip checkbox state not found in config. Using default.")
        self.save_tooltip_config()

    def save_tooltip_config(self):
        # Save the selected G2P model to settings.ini
        config = configparser.ConfigParser()
        config.read(self.config_file)
        if 'Settings' not in config.sections():
            config['Settings'] = {}
        config['Settings']['tooltip_Enabled'] = str(self.tooltip_checkbox_var.get())
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)
        print(f"tooltips are saved to config file.")
    
    def toggle_tooltip(self):
        self.save_tooltip_config()

    def create_tooltip(self, widget, text_key, default_text):
    # Bind the widget-specific variables directly
        def show_tooltip(event=None, widget=widget, text_key=text_key, default_text=default_text):
            if not self.tooltip_checkbox_var.get():  # Tooltips disabled
                return
            # Show tooltip if none exists already
            if not getattr(widget, 'tooltip_window', None):
                text = self.localization.get(text_key, default_text)
                x = widget.winfo_rootx() + 30
                y = widget.winfo_rooty() + widget.winfo_height() - 10
                tooltip_window = tw = tk.Toplevel(widget)
                tw.wm_overrideredirect(True)
                tw.wm_geometry(f"+{x}+{y}")
                # Fetch the correct background color based on the theme
                bg_color = self.update_tooltip_bg()
                label = tk.Label(tw, text=text, background=bg_color, relief="solid", borderwidth=1, wraplength=200)
                label.pack(ipadx=1)
                widget.tooltip_window = tw

                # Reset idle timer and set a safety timer to ensure tooltip is destroyed
                self.reset_idle_timer(widget)
                self.set_safety_timer(widget)  # Set safety timer

        def hide_tooltip(event=None, widget=widget):
            tw = getattr(widget, 'tooltip_window', None)
            if tw:
                widget.tooltip_window = None
                tw.destroy()

        def hide_tooltip_on_focus(event=None, widget=widget):
            # This method hides the tooltip if the widget is focused, especially useful for Combobox
            hide_tooltip(widget=widget)

        def move_tooltip(event=None, widget=widget):
            if getattr(widget, 'tooltip_window', None):
                x = event.x_root + 10
                y = event.y_root + 20
                widget.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Bind tooltip events for each widget separately
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
        widget.bind("<Motion>", move_tooltip)

        # Additional bindings to hide tooltips when widgets gain focus or are clicked
        widget.bind("<FocusIn>", hide_tooltip_on_focus)
        widget.bind("<Button-1>", hide_tooltip_on_focus)  # Hide tooltip on left-click
        widget.bind("<FocusOut>", hide_tooltip)  # Ensure it hides on losing focus

        # Make sure each widget keeps its tooltip timeout behavior
        widget.idle_timer = None
        widget.idle_timeout = 5000  # 5 seconds
        widget.safety_timer = None

    def reset_idle_timer(self, widget):
        # Cancel existing timers
        if widget.idle_timer:
            widget.after_cancel(widget.idle_timer)
        if widget.safety_timer:
            widget.after_cancel(widget.safety_timer)

        # Set idle timer
        widget.idle_timer = widget.after(widget.idle_timeout, lambda: self.hide_tooltip(widget))

    def set_safety_timer(self, widget):
        # Set a safety timer to forcibly destroy the tooltip after the idle timeout, even if it is stuck
        if widget.safety_timer:
            widget.after_cancel(widget.safety_timer)

        # Set a safety timer to forcefully hide the tooltip after idle_timeout + buffer time
        safety_timeout = widget.idle_timeout + 1000  # 1 second buffer after idle timeout
        widget.safety_timer = widget.after(safety_timeout, lambda: self.hide_tooltip(widget))

    def hide_tooltip(self, widget):
        tw = getattr(widget, 'tooltip_window', None)
        if tw:
            widget.tooltip_window = None
            tw.destroy()

    def update_tooltip_bg(self):
        # Check the current theme
        theme_name = self.theme_var.get()
        if theme_name == 'System':
            system_theme = darkdetect.theme()  # Auto-detects system dark/light mode
            theme_key = system_theme
        else:
            theme_key = theme_name

        # Set background color based on the theme
        if theme_key == 'Dark':
            return '#2a2a2a'  # Dark background
        else:
            return '#fafafa'  # Light background (default)

    # Directory for the YAML Templates via settings.ini
    def read_template_directory(self, config_file="settings.ini"):
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file)
            try:
                return config.get('Paths', 'template_location')
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass
        return self.save_directory_to_config(config_file)

    def save_directory_to_config(self, config_file):
        config = configparser.ConfigParser()
        config['Paths'] = {'template_location': TEMPLATES}
        config['Settings'] = {'localization': LOCAL / 'en_US.yaml'}
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        
    def update_title(self):
        if self.current_filename:
            self.title(f"OU DE (editing {self.current_filename})")
        else:
            self.title(self.base_title)
    
    def change_hue_and_save(self, image_path, hue):
        ImageFile.LOAD_TRUNCATED_IMAGES = True  # Prevents crashes from truncated images
        img = Image.open(image_path).convert("RGBA")
        arr = np.array(img, dtype=np.float32) / 255.0  # Normalize pixel values

        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
        
        # Convert RGB to HLS
        h, l, s = np.vectorize(colorsys.rgb_to_hls)(r, g, b)
        h = hue / 360.0
        hue_mask = s > 0.9 # Only modify areas with some color
        
        # Convert HLS back to RGB
        r, g, b = np.vectorize(colorsys.hls_to_rgb)(h, l, s)
        
        # Convert back to 8-bit integer format
        arr[:, :, 0] = (r * 255).astype(np.uint8)
        arr[:, :, 1] = (g * 255).astype(np.uint8)
        arr[:, :, 2] = (b * 255).astype(np.uint8)
        arr[:, :, 3] = (a * 255).astype(np.uint8)  # Preserve alpha channel

        Image.fromarray(arr.astype(np.uint8)).save(image_path)
    
    def apply_hue_to_sv_ttk(self, hue):
        # Apply hue changes in a background thread to prevent UI lag
        def process_images():
            threads = []
            for root, _, files in os.walk(THEME_DIR):
                for file in files:
                    if file.endswith(".png"):
                        file_path = os.path.join(root, file)
                        thread = threading.Thread(target=self.change_hue_and_save, args=(file_path, hue))
                        thread.start()
                        threads.append(thread)

            # Wait for all threads to finish (but now in a background thread)
            for thread in threads:
                thread.join()

            self.update_tcl_foreground_color(HUE_LUMEN)
        threading.Thread(target=process_images, daemon=True).start()
        self.reload_tcl_theme()
        print(f"✅ Updated Sun Valley theme assets with hue {hue}")
    
    def reload_tcl_theme(self):
        messagebox.showinfo("Accent Color Applied", f"{self.localization.get('accent_color_apply', 'Accent color applied to tcl file successfully, please restart OpenUtau Dictionary Editor')}")
        

    def calculate_luminance(self, rgb):
        # Calculates perceived brightness (luminance) from an RGB color
        r, g, b = [x / 255.0 for x in rgb]  # Normalize to 0-1 range
        luminance = (0.299 * r) + (0.587 * g) + (0.114 * b)  # brightness formula
        return luminance

    def detect_best_foreground_color(self, image_path):
        # Detects the best foreground color (black or white) based on background brightness
        try:
            img = Image.open(image_path).convert("RGB")
            img = img.resize((50, 50)) 
            pixels = np.array(img).reshape(-1, 3) 

            # Compute average luminance (perceived brightness)
            avg_luminance = np.mean([self.calculate_luminance(rgb) for rgb in pixels])

            # foreground color
            foreground_color = "#000000" if avg_luminance > 0.5 else "#FFFFFF"
            print(f"🎨 Detected Luminance: {avg_luminance:.2f}, Foreground Color: {foreground_color}")
            return foreground_color

        except Exception as e:
            print(f"❌ Error detecting foreground color: {e}")
            return "#000000"  # Default to black if detection fails
    
    def update_tcl_foreground_color(self, image_path):
        # Finds and updates all TCL theme files except light.tcl and dark.tcl.
        foreground_color = self.detect_best_foreground_color(image_path)
        EXCLUDED_FOLDER = os.path.abspath("./Assets/modules/sv_ttk/theme/backup")

        if not foreground_color:
            print("❌ Error: Foreground color is None, skipping update.")
            return

        # ✅ Modify only the foreground color line in `.tcl` files
        tcl_files = [
            file for file in glob.glob(os.path.join(TCL_THEME_DIR, "**", "*.tcl"), recursive=True)
            if not os.path.abspath(file).startswith(EXCLUDED_FOLDER) 
            and not file.endswith(("sprites_light.tcl", "sprites_dark.tcl"))  # Exclude specific sprite TCL files
        ]
        for tcl_file in tcl_files:
            with open(tcl_file, "r", encoding="utf-8") as file:
                tcl_lines = file.readlines()

            modified = False 
            for i in range(len(tcl_lines)):
                if "ttk::style configure Accent.TButton" in tcl_lines[i]:  
                    if "-foreground" in tcl_lines[i]:  
                        # Update existing foreground color
                        tcl_lines[i] = f'    ttk::style configure Accent.TButton -padding {{8 2 8 3}} -anchor center -foreground "{foreground_color}"\n'
                    else:  
                        # If `-foreground` is missing, add it
                        tcl_lines[i] = tcl_lines[i].strip() + f' -foreground "{foreground_color}"\n'
                    modified = True

            # ✅ Save only if the file was modified
            if modified:
                with open(tcl_file, "w", encoding="utf-8") as file:
                    file.writelines(tcl_lines)
                    print(f"✅ Updated foreground color in {tcl_file} to {foreground_color}")
            else:
                print(f"⚠️ No foreground color found in {tcl_file}, skipping update.")

    def detect_hue_from_image(self, image_path):
        try:
            img = Image.open(image_path).convert("RGB")
            img = img.resize((50, 50)) 
            pixels = np.array(img, dtype=np.float32) / 255.0  # Normalize pixel values
            
            # Convert RGB to HSV and extract hue values with precise calculations
            hues, lightness = np.array([
                (colorsys.rgb_to_hls(r, g, b)[0] * 360, colorsys.rgb_to_hls(r, g, b)[1])
                for r, g, b in pixels.reshape(-1, 3)
            ]).T
            
            # Focus on the most frequent hue for better accuracy
            hist, bin_edges = np.histogram(hues, bins=180, range=(0, 360))
            dominant_hue = np.average(bin_edges[:-1], weights=hist)
            avg_brightness = np.mean(lightness)
            
            # Map hue (0-360) to new slider scale (-180 to 180)
            mapped_hue = self.map_roygbiv_hue(dominant_hue)
            
            print(f"🎨 Detected Hue: {dominant_hue:.2f}° (Mapped: {mapped_hue}), Brightness: {avg_brightness:.2f}")
            return mapped_hue
        
        except Exception as e:
            print(f"❌ Error detecting hue: {e}")
            return 0, 0.5  # Default to 0 hue and 0.5 brightness if detection fails

    def cache_hue(self, hue_path):
        if hue_path not in self.hue_cache:
            self.hue_cache[hue_path] = self.detect_hue_from_image(hue_path)
    
    def map_roygbiv_hue(self, hue):
        return ((hue / 360) * 360)
    
    def update_hue_slider(self):
        detected_hue = self.detect_hue_from_image(HUE_LUMEN)
        self.hue_slider.set(detected_hue)  # Set the slider value to detected hue
    
    def hue_to_hex(self, hue):
        normalized_hue = hue / 360.0
        r, g, b = colorsys.hsv_to_rgb(normalized_hue, 1, 1)  # Convert HSV → RGB (max saturation & brightness)
        return "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))

    def hex_to_hue(self, hex_color):
        if not hex_color or not hex_color.startswith("#"):
            return 160 # Default to 160°
        
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        hue, _, _ = colorsys.rgb_to_hsv(r, g, b)
        return hue * 360  # Convert hue to degrees
    
    def copy_folder_contents(self):
        source_folder = os.path.join("./Assets/default theme")
        destination_folder = THEME_DIR
        if not os.path.exists(source_folder):
            print(f"❌ Source folder not found: {source_folder}")
            return False
        os.makedirs(destination_folder, exist_ok=True)

        # Copy each file
        for filename in os.listdir(source_folder):
            source_path = os.path.join(source_folder, filename)
            destination_path = os.path.join(destination_folder, filename)

            # Copy only files (not subdirectories)
            if os.path.isfile(source_path):
                shutil.copy2(source_path, destination_path)  # Keeps metadata (timestamps)
                print(f"✅ Copied: {source_path} → {destination_path}")
        messagebox.showinfo("Accent Color Reset", f"{self.localization.get('reset_accent_color', 'Accent color was reset to #00FFB2')}")
        detected_hue = self.detect_hue_from_image(HUE_LUMEN)
        self.hue_slider.set(detected_hue)
        self.hex_value()
        self.update_tcl_foreground_color
        return True

    def toggle_theme(self, event=None):
        theme_name = self.theme_var.get() if hasattr(self.theme_var, "get") else self.theme_var
        hue = self.hue_slider.get()
        hex_color = self.hue_to_hex(hue)
        current_theme = ttk.Style().theme_use()

        # Handle "System" theme selection dynamically
        if theme_name == "System":
            system_theme = darkdetect.theme().lower()
        else:
            system_theme = theme_name.lower()

       # Theme mapping based on current theme
        theme_switch = {
            "sun-valley-light": "mint_light",
            "mint_light": "sun-valley-light",
            "sun-valley-dark": "mint_dark",
            "mint_dark": "sun-valley-dark"
        }
        # Determine the new theme
        new_theme = theme_switch.get(current_theme, "sun-valley-light")  # Default fallback

        # Apply the theme only if it changes
        if new_theme != current_theme:
            ttk.Style().theme_use(new_theme)
            sv_ttk.set_theme(system_theme)

        self.widget_style()
        self.save_theme_to_config(hex_color, theme_name)
        print(f"✅ Applied Theme: {new_theme} (System theme: {darkdetect.theme() if theme_name == 'System' else 'Manual'})")

    def hex_value(self, event=None):
        hue = self.hue_slider.get()
        hex_color = self.hue_to_hex(hue)

        if hasattr(self, "theme_combobox"):  # Ensure combobox exists
            self.draw_color_preview(hex_color)
        
        config = configparser.ConfigParser()
        config.read(self.config_file)
        if 'Settings' not in config.sections():
            config['Settings'] = {}
        config['Settings']['accent'] = hex_color
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)
    
    def draw_color_preview(self, hex_color):
        for widget in self.theme_combobox.winfo_children():
            widget.destroy()

        canvas = Canvas(self.theme_combobox, width=40, height=16, bg=hex_color, highlightthickness=1)
        canvas.place(x=5, y=5)

        self.theme_combobox.set(hex_color)

    def save_theme_to_config(self, accent_name, theme_name):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        if 'Settings' not in config.sections():
            config['Settings'] = {}
        config['Settings']['accent'] = accent_name
        config['Settings']['theme'] = theme_name
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)
    
    def load_last_theme(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        try:
            theme_name = config.get('Settings', 'theme')
            theme_name = self.theme_var.get()
            accent_name = config.get('Settings', 'accent')

            accent_hue = self.hex_to_hue(accent_name)
            detected_hue = self.detect_hue_from_image(HUE_LUMEN)

            # If detected hue is different from the accent hue, adjust it
            if abs(detected_hue - accent_hue) > 1:
                threads = [] 
                for root, _, files in os.walk(THEME_DIR):
                    for file in files:
                        if file.endswith(".png"):
                            file_path = os.path.join(root, file)
                            thread = threading.Thread(target=self.change_hue_and_save, args=(file_path, accent_hue))
                            thread.start()
                            threads.append(thread)
                # Wait for all threads to complete before updating TCL foreground color
                for thread in threads:
                    thread.join()
                self.update_tcl_foreground_color(HUE_LUMEN)

            # Apply the theme using sv_ttk
            if theme_name == 'System':
                system_theme = darkdetect.theme().lower()
            else:
                system_theme = theme_name.lower()
            sv_ttk.set_theme(system_theme)
           
        except (configparser.NoSectionError, configparser.NoOptionError):
            system_theme = darkdetect.theme().lower()
            theme_key = (f"mint_{system_theme}")
            sv_ttk.set_theme(system_theme)
            ttk.Style().theme_use(theme_key)
        
    def load_cmudict(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(filetypes=[
                ("All supported text files", "*.txt;*.tsv;*.csv"),
                ("Text files", "*.txt"),
                ("TSV files", "*.tsv"),
                ("CSV files", "*.csv")
            ])
        if not filepath:
            messagebox.showinfo("No File", f"{self.localization.get('cmudict_nofile', 'No file was selected.')}")
            return
        
        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, self.load_process_cmudict_file, filepath)

    def load_process_cmudict_file(self, filepath):
        self.file_opened = True
        self.update_cache_button_text()
        self.update_template_combobox(self.template_combobox)
        
        self.current_filename = filepath
        self.file_modified = False
        self.update_title()

        try:
            # Clear existing entries in the database
            self.cursor.execute("DELETE FROM entries")
            self.db_conn.commit()

            ext = os.path.splitext(filepath)[-1].lower()
            delimiter = ',' if ext == '.csv' else '\t' if ext == '.tsv' else None

            with open(filepath, 'r', encoding='utf-8-sig', newline='') as file:
                if delimiter:
                    reader = csv.reader(file, delimiter=delimiter)
                else:
                    reader = (re.split(r'\s{2,}|\t|,|;', line.strip()) for line in file)

                grapheme_count = defaultdict(int)
                entries_to_insert = []
                
                # Using a separate cursor for batch insert for potentially better performance
                insert_cursor = self.db_conn.cursor()
                current_order = 0

                for line_number, parts in enumerate(reader, start=1):
                    try:
                        if isinstance(parts, str):
                            parts = re.split(r'\s{2,}|\t|,|;', parts.strip())
                        if not parts or len(parts) < 2:
                            continue
                        if parts[0].strip().lower() == 'grapheme' and parts[1].strip().lower() == 'phonemes':
                            continue  # Skip header
                        if parts[0].strip().startswith(';;;'):
                            # Comments can be stored in a separate table if needed, or ignored for now.
                            continue

                        grapheme = parts[0].strip()
                        phonemes = list(map(str.strip, parts[1].split()))
                        base_grapheme = grapheme

                        # Handle duplicates by adding a suffix (e.g., WORD(1))
                        temp_grapheme = base_grapheme
                        while self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (temp_grapheme,)).fetchone():
                            grapheme_count[base_grapheme] += 1
                            temp_grapheme = f"{base_grapheme}({grapheme_count[base_grapheme]})"
                        grapheme = temp_grapheme

                        entries_to_insert.append((grapheme, json.dumps(phonemes), current_order))
                        current_order += 1

                        if len(entries_to_insert) % 5000 == 0: # Batch insert every 5000 entries
                            insert_cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                            self.db_conn.commit()
                            entries_to_insert = [] # Clear batch

                    except Exception as e:
                        self.loading_window.destroy()
                        messagebox.showerror("Error", f"{self.localization.get('load_cmudict_procc', 'Error occurred while processing line')} {line_number}: '{parts}'\n{str(e)}")
                        return # Exit function on error

                # Insert any remaining entries
                if entries_to_insert:
                    insert_cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                    self.db_conn.commit()

            messagebox.showinfo("Load Complete", "CMUDict loaded into database successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('cmudict_err_1', 'Error occurred while reading file: ')} {e}")
            return
        finally:
            self.loading_window.destroy()
            self.update_entries_window() # Refresh Treeview with new data

    def append_cmudict_file(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not filepath:
            messagebox.showinfo("No File", f"{self.localization.get('cmudict_nofile', 'No file was selected.')}")
            return
        
        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, self.append_load_process_cmudict_file, filepath)

    def append_load_process_cmudict_file(self, filepath):
        self.file_opened = True
        self.update_cache_button_text()
        self.update_template_combobox(self.template_combobox)
        
        self.current_filename = filepath
        self.file_modified = False
        self.update_title()

        try:
            ext = os.path.splitext(filepath)[-1].lower()
            delimiter = ',' if ext == '.csv' else '\t' if ext == '.tsv' else None

            # Get the current maximum original_order for appending
            self.cursor.execute("SELECT MAX(original_order) FROM entries")
            max_order = self.cursor.fetchone()[0]
            current_order = (max_order + 1) if max_order is not None else 0

            with open(filepath, 'r', encoding='utf-8-sig', newline='') as file:
                if delimiter:
                    reader = csv.reader(file, delimiter=delimiter)
                else:
                    reader = (re.split(r'\s{2,}|\t|,|;', line.strip()) for line in file)

                entries_to_insert = []
                grapheme_count = defaultdict(int) # For handling duplicates in new data

                for line_number, parts in enumerate(reader, start=1):
                    try:
                        if isinstance(parts, str):
                            parts = re.split(r'\s{2,}|\t|,|;', parts.strip())
                        if not parts or len(parts) < 2:
                            continue
                        if parts[0].strip().lower() == 'grapheme' and parts[1].strip().lower() == 'phonemes':
                            continue  # Skip header
                        if parts[0].strip().startswith(';;;'):
                            continue

                        grapheme = parts[0].strip()
                        phonemes = list(map(str.strip, parts[1].split()))
                        base_grapheme = grapheme

                        # Check if grapheme already exists in DB
                        existing_grapheme = self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (base_grapheme,)).fetchone()
                        if existing_grapheme:
                            # If it exists, check if phonemes are identical
                            existing_phonemes_json = self.cursor.execute("SELECT phonemes FROM entries WHERE grapheme = ? COLLATE NOCASE", (base_grapheme,)).fetchone()[0]
                            existing_phonemes = json.loads(existing_phonemes_json)
                            if existing_phonemes == phonemes:
                                continue # Skip if exact duplicate
                            
                            # If grapheme exists but phonemes are different, generate a unique grapheme
                            temp_grapheme = base_grapheme
                            while self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (temp_grapheme,)).fetchone():
                                grapheme_count[base_grapheme] += 1
                                temp_grapheme = f"{base_grapheme}({grapheme_count[base_grapheme]})"
                            grapheme = temp_grapheme

                        entries_to_insert.append((grapheme, json.dumps(phonemes), current_order))
                        current_order += 1

                        if len(entries_to_insert) % 5000 == 0:
                            self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                            self.db_conn.commit()
                            entries_to_insert = []

                    except Exception as e:
                        self.loading_window.destroy()
                        messagebox.showerror("Error", f"{self.localization.get('load_cmudict_procc', 'Error occurred while processing line')} {line_number}: '{parts}'\n{str(e)}")
                        return # Exit function on error

                if entries_to_insert:
                    self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                    self.db_conn.commit()
            
            messagebox.showinfo("Append Complete", "CMUDict appended to database successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('cmudict_err_1', 'Error occurred while reading file: ')} {e}")
            return
        finally:
            self.loading_window.destroy()
            self.update_entries_window() # Refresh Treeview with new data

    def append_csv_tsv(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(filetypes=[
                ("Supported Text Files", "*.tsv;*.csv"),
                ("TSV files", "*.tsv"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ])
        if not filepath:
            messagebox.showinfo("No File", f"{self.localization.get('cmudict_nofile', 'No file was selected.')}")
            return

        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, lambda: self._process_append_csv_tsv(filepath))

    def _process_append_csv_tsv(self, filepath):
        self.file_opened = True
        self.update_cache_button_text()
        self.update_template_combobox(self.template_combobox)
        
        self.current_filename = filepath
        self.file_modified = False
        self.update_title()

        ext = os.path.splitext(filepath)[-1].lower()
        is_csv = ext == ".csv"
        is_tsv = ext == ".tsv"
        delimiter = ',' if is_csv else '\t' if is_tsv else None

        try:
            # Get the current maximum original_order for appending
            self.cursor.execute("SELECT MAX(original_order) FROM entries")
            max_order = self.cursor.fetchone()[0]
            current_order = (max_order + 1) if max_order is not None else 0

            with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
                if delimiter:
                    reader = csv.reader(f, delimiter=delimiter)
                else:
                    reader = (re.split(r'\s{2,}|\t|,|;', line.strip()) for line in f)

                entries_to_insert = []
                grapheme_count = defaultdict(int)

                for line_number, parts in enumerate(reader, start=1):
                    if isinstance(parts, str):
                        parts = [p.strip() for p in parts if p.strip()]
                    if not parts or len(parts) < 2:
                        continue

                    # Check for header
                    if ("grapheme" in parts[0].lower() and "phoneme" in parts[1].lower()):
                        continue  # Skip header line

                    grapheme = str(parts[0]).strip()
                    phoneme_list = [p.strip() for p in parts[1].split()]

                    if not grapheme or not phoneme_list:
                        continue

                    # Check for duplicates in DB
                    existing_grapheme = self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (grapheme,)).fetchone()
                    if existing_grapheme:
                        existing_phonemes_json = self.cursor.execute("SELECT phonemes FROM entries WHERE grapheme = ? COLLATE NOCASE", (grapheme,)).fetchone()[0]
                        existing_phonemes = json.loads(existing_phonemes_json)
                        if existing_phonemes == phoneme_list:
                            continue # Skip if exact duplicate
                        
                        temp_grapheme = grapheme
                        while self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (temp_grapheme,)).fetchone():
                            grapheme_count[grapheme] += 1
                            temp_grapheme = f"{grapheme}({grapheme_count[grapheme]})"
                        grapheme = temp_grapheme

                    entries_to_insert.append((grapheme, json.dumps(phoneme_list), current_order))
                    current_order += 1

                    if len(entries_to_insert) % 5000 == 0:
                        self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                        self.db_conn.commit()
                        entries_to_insert = []

            if entries_to_insert:
                self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                self.db_conn.commit()

            messagebox.showinfo("Append Complete", "CSV/TSV appended to database successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('load_cmudict_procc', 'Error processing file')}: {str(e)}")
        finally:
            self.loading_window.destroy()
            self.update_entries_window()

    def remove_numbered_accents(self, phonemes):
        return [phoneme[:-1] if phoneme[-1].isdigit() else phoneme for phoneme in phonemes]
    
    def load_json_file(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(title="Open JSON File", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not filepath:
            messagebox.showinfo("No File", f"{self.localization.get('json_nofile', 'No file was selected.')}")
            return

        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, self.load_process_json_file, filepath)

    def load_process_json_file(self, filepath):
        self.file_opened = True
        self.update_cache_button_text()
        self.update_template_combobox(self.template_combobox)
        self.current_filename = filepath
        self.file_modified = False
        self.update_title()

        try:
            # Clear existing entries in the database
            self.cursor.execute("DELETE FROM entries")
            self.db_conn.commit()

            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                entries = data.get('data', [])
                if not entries:
                    self.loading_window.destroy()
                    messagebox.showinfo("Empty Data", f"{self.localization.get('json_empty', 'The JSON file contains no data.')}")
                    return

            entries_to_insert = []
            grapheme_count = defaultdict(int)
            current_order = 0

            for item in entries:
                grapheme = item.get('w')
                phonemes_str = item.get('p')
                if not (isinstance(grapheme, str) and isinstance(phonemes_str, str)):
                    messagebox.showerror("Invalid Entry", f"{self.localization.get('json_inv_entry', 'Each entry must have a (w) key with a string value and a (p) key with a string value.')}")
                    continue
                
                phoneme_list = [str(p).strip() for p in phonemes_str.split()]

                # Handle duplicates by adding a suffix
                temp_grapheme = grapheme
                while self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (temp_grapheme,)).fetchone():
                    grapheme_count[grapheme] += 1
                    temp_grapheme = f"{grapheme}({grapheme_count[grapheme]})"
                grapheme = temp_grapheme

                entries_to_insert.append((grapheme, json.dumps(phoneme_list), current_order))
                current_order += 1

                if len(entries_to_insert) % 5000 == 0:
                    self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                    self.db_conn.commit()
                    entries_to_insert = []

            if entries_to_insert:
                self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                self.db_conn.commit()

            messagebox.showinfo("Load Complete", "JSON data loaded into database successfully.")

        except json.JSONDecodeError as je:
            messagebox.showerror("JSON Syntax Error", f"{self.localization.get('json_parse_file', 'An error occurred while parsing the JSON file: ')} {str(je)}")
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('json_read_ex', 'An error occurred while reading the JSON file: ')} {str(e)}")
        finally:
            self.loading_window.destroy()
            self.update_entries_window()
    
    def export_csv_tsv(self):
        self.cursor.execute("SELECT COUNT(*) FROM entries")
        if self.cursor.fetchone()[0] == 0:
            messagebox.showinfo("Warning", self.localization.get('save_cmudict_m', 'No entries to save. Please add entries before saving.'))
            return

        # Prompt user for CSV or TSV save location
        output_file_path = filedialog.asksaveasfilename(
            title="Export CSV or TSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("TSV files", "*.tsv"), ("All files", "*.*")]
        )

        if not output_file_path:
            messagebox.showinfo("Cancelled", self.localization.get('cmudict_cancel', 'Save operation cancelled.'))
            return

        self.save_window()
        self.saving_window.update_idletasks()
        self.after(100, self.process_export_csv_tsv, output_file_path)

    def process_export_csv_tsv(self, filepath):
        self.file_opened = True
        self.update_cache_button_text()

        # Determine delimiter from extension
        _, ext = os.path.splitext(filepath)
        delimiter = '\t' if ext.lower() == '.tsv' else ','

        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file, delimiter=delimiter)
                writer.writerow(["Grapheme", "Phonemes"])  # Header

                self.cursor.execute("SELECT grapheme, phonemes FROM entries ORDER BY original_order")
                for grapheme, phonemes_json in self.cursor.fetchall():
                    phonemes = json.loads(phonemes_json)
                    if self.lowercase_phonemes_var.get():
                        phonemes = [phoneme.lower() for phoneme in phonemes]
                    if self.remove_numbered_accents_var.get():
                        phonemes = self.remove_numbered_accents(phonemes)
                    writer.writerow([grapheme, ' '.join(phonemes)])

            self.saving_window.destroy()
            messagebox.showinfo("Success", self.localization.get('cmudict_saved_dict', 'Dictionary saved to ') + filepath)

        except Exception as e:
            messagebox.showerror("Error", self.localization.get('cmudict_cache_err', 'Error occurred while saving: ') + str(e))
        finally:
            self.saving_window.destroy() # Ensure window closes even on error

    def append_json_file(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(title="Open JSON File", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not filepath:
            messagebox.showinfo("No File", f"{self.localization.get('json_nofile', 'No file was selected.')}")
            return

        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, self.append_process_json_file, filepath)

    def append_process_json_file(self, filepath):
        self.file_opened = True
        self.update_cache_button_text()
        self.update_template_combobox(self.template_combobox)
        self.current_filename = filepath
        self.file_modified = False
        self.update_title()

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                entries = data.get('data', [])
                if not entries:
                    self.loading_window.destroy()
                    messagebox.showinfo("Empty Data", f"{self.localization.get('json_empty', 'The JSON file contains no data.')}") 
                    return
            
            entries_to_insert = []
            grapheme_count = defaultdict(int)
            
            # Get the current maximum original_order for appending
            self.cursor.execute("SELECT MAX(original_order) FROM entries")
            max_order = self.cursor.fetchone()[0]
            current_order = (max_order + 1) if max_order is not None else 0

            for item in entries:
                grapheme = item.get('w')
                phonemes_str = item.get('p')
                if not (isinstance(grapheme, str) and isinstance(phonemes_str, str)):
                    messagebox.showerror("Invalid Entry", f"{self.localization.get('json_inv_entry', 'Each entry must have a (w) key with a string value and a (p) key with a string value.')}") 
                    continue
                
                phoneme_list = [str(p).strip() for p in phonemes_str.split()]

                # Check for duplicates in DB
                existing_grapheme = self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (grapheme,)).fetchone()
                if existing_grapheme:
                    existing_phonemes_json = self.cursor.execute("SELECT phonemes FROM entries WHERE grapheme = ? COLLATE NOCASE", (grapheme,)).fetchone()[0]
                    existing_phonemes = json.loads(existing_phonemes_json)
                    if existing_phonemes == phoneme_list:
                        continue # Skip if exact duplicate
                    
                    temp_grapheme = grapheme
                    while self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (temp_grapheme,)).fetchone():
                        grapheme_count[grapheme] += 1
                        temp_grapheme = f"{grapheme}({grapheme_count[grapheme]})"
                    grapheme = temp_grapheme

                entries_to_insert.append((grapheme, json.dumps(phoneme_list), current_order))
                current_order += 1

                if len(entries_to_insert) % 5000 == 0:
                    self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                    self.db_conn.commit()
                    entries_to_insert = []

            if entries_to_insert:
                self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                self.db_conn.commit()

            messagebox.showinfo("Append Complete", "JSON data appended to database successfully.")

        except json.JSONDecodeError as je:
            messagebox.showerror("JSON Syntax Error", f"{self.localization.get('json_parse_file', 'An error occurred while parsing the JSON file: ')} {str(je)}")
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('json_read_ex', 'An error occurred while reading the JSON file: ')} {str(e)}")
        finally:
            self.loading_window.destroy()
            self.update_entries_window()

    def load_yaml_file(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(
                title="Open YAML File",
                filetypes=[("YAML files", "*.yaml"), ("Y'ALL files", "*yaml.y'all"), ("All files", "*.*")]
            )
            if not filepath:
                messagebox.showinfo("No File", f"{self.localization.get('yaml_nofile', 'No file was selected.')}")
                return
        
        # Show loading window
        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, self.load_process_yaml_file, filepath)  # Delay to ensure the loading window appears

    def load_process_yaml_file(self, filepath):
        self.file_opened = True
        self.update_cache_button_text()
        self.update_template_combobox(self.template_combobox)
        try:
            # Handle file opening to update title
            self.current_filename = filepath
            self.file_modified = False
            self.update_title()

            yaml = YAML(typ='safe')
            yaml.prefix_colon = True
            yaml.preserve_quotes = True
            with open(filepath, 'r', encoding='utf-8') as file:
                data = yaml.load(file)
                if data is None:
                    self.loading_window.destroy()
                    raise ValueError({self.localization.get('yaml_inc_format_rv', 'The YAML file is empty or has an incorrect format.')})
            
            # Clear existing data in database tables
            self.cursor.execute("DELETE FROM entries")
            self.cursor.execute("DELETE FROM symbols")
            self.cursor.execute("DELETE FROM replacements")
            self.db_conn.commit()

            # Load entries
            entries = data.get('entries', [])
            if not isinstance(entries, list):
                if isinstance(data, list): # Support old format where top-level is a list of entries
                    entries = [item for item in data if isinstance(item, dict) and 'grapheme' in item and 'phonemes' in item]
                elif isinstance(data, dict) and 'grapheme' in data and 'phonemes' in data: # Support single entry as top-level dict
                    entries = [data]
                else:
                    self.loading_window.destroy()
                    raise ValueError({self.localization.get('yaml_dict_fromat_rv', 'Entry format incorrect. Each entry must be a dictionary or top-level list/dict.')})
            
            entries_to_insert = []
            grapheme_count = defaultdict(int)
            current_order = 0
            for item in entries:
                if not isinstance(item, dict):
                    self.loading_window.destroy()
                    raise ValueError({self.localization.get('yaml_dict_fromat_rv', 'Entry format incorrect. Each entry must be a dictionary.')})
                grapheme = item.get('grapheme')
                phonemes = item.get('phonemes', [])
                if grapheme is None or not isinstance(phonemes, list):
                    self.loading_window.destroy()
                    raise ValueError({self.localization.get('yaml_type_rv', 'Each entry must have a (grapheme) key and a list of (phonemes).')})
                
                # Handle duplicates by adding a suffix
                temp_grapheme = grapheme
                while self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (temp_grapheme,)).fetchone():
                    grapheme_count[grapheme] += 1
                    temp_grapheme = f"{grapheme}({grapheme_count[grapheme]})"
                grapheme = temp_grapheme

                entries_to_insert.append((grapheme, json.dumps(phonemes), current_order))
                current_order += 1

                if len(entries_to_insert) % 5000 == 0:
                    self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                    self.db_conn.commit()
                    entries_to_insert = []
            if entries_to_insert:
                self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                self.db_conn.commit()

            # Load symbols if available
            symbols = data.get('symbols', [])
            if isinstance(symbols, list):
                symbols_to_insert = []
                symbol_grapheme_count = defaultdict(int)
                for item in symbols:
                    if not isinstance(item, dict):
                        self.loading_window.destroy()
                        raise ValueError({self.localization.get('sym_inc_rv', 'Symbol entry format incorrect. Each entry must be a dictionary.')})
                    symbol = item.get('symbol')
                    type_ = item.get('type')
                    rename = item.get('rename', '') # Get rename field, default to empty string
                    if symbol is None or type_ is None:
                        self.loading_window.destroy()
                        raise ValueError({self.localization.get('sym_ent_inc_rv', 'Symbol entry is incomplete.')})
                    if not isinstance(type_, str):
                        self.loading_window.destroy()
                        raise ValueError({self.localization.get('sym_str_rv', 'Type must be a string representing the category.')})
                    
                    # Handle symbol duplicates by adding a suffix
                    temp_symbol = symbol
                    while self.cursor.execute("SELECT symbol FROM symbols WHERE symbol = ? COLLATE NOCASE", (temp_symbol,)).fetchone():
                        symbol_grapheme_count[symbol] += 1
                        temp_symbol = f"{symbol}({symbol_grapheme_count[symbol]})"
                    symbol = temp_symbol

                    symbols_to_insert.append((symbol, type_, json.dumps(rename if isinstance(rename, list) else [rename])))

                if symbols_to_insert:
                    self.cursor.executemany("INSERT OR IGNORE INTO symbols (symbol, type, rename) VALUES (?, ?, ?)", symbols_to_insert)
                    self.db_conn.commit()
            
            # Load replacements
            replacements = data.get('replacements', [])
            if isinstance(replacements, list):
                replacements_to_insert = []
                for replacement in replacements:
                    from_config = replacement.get('from')
                    to_config = replacement.get('to')
                    
                    if from_config is None or to_config is None:
                        messagebox.showerror("Error", self.localization.get('process_repl_sym_err', 'Each replacement entry must have a (from) and a (to) symbol (string or list)'))
                        continue
                    
                    # Store from and to as JSON strings, handling single strings or lists
                    from_json = json.dumps(from_config if isinstance(from_config, list) else [from_config])
                    to_json = json.dumps(to_config if isinstance(to_config, list) else [to_config])
                    replacements_to_insert.append((from_json, to_json))

                if replacements_to_insert:
                    self.cursor.executemany("INSERT INTO replacements (from_symbol, to_symbol) VALUES (?, ?)", replacements_to_insert)
                    self.db_conn.commit()


            messagebox.showinfo("Load Complete", "YAML data loaded into database successfully.")

        except (YAMLError, ValueError) as e:
            self.loading_window.destroy()
            messagebox.showerror("Error", f"{self.localization.get('yaml_load_err', 'An error occurred: ')} {str(e)}")
        except Exception as e:
            self.loading_window.destroy()
            messagebox.showerror("Error", f"{self.localization.get('yaml_unex_err', 'An unexpected error occurred: ')} {str(e)}")
        finally:
            self.loading_window.destroy()
            self.update_entries_window() # Refresh Treeview with new data

    def append_yaml_file(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(
                title="Open YAML File",
                filetypes=[("YAML files", "*.yaml"), ("Y'ALL files", "*yaml.y'all"), ("All files", "*.*")]
            )
            if not filepath:
                messagebox.showinfo("No File", f"{self.localization.get('yaml_nofile', 'No file was selected.')}")
                return
        
        # Show loading window
        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, self.append_process_yaml_file, filepath)  # Delay to ensure the loading window appears

    def append_process_yaml_file(self, filepath):
        self.file_opened = True
        self.update_cache_button_text()
        self.update_template_combobox(self.template_combobox)
        try:
            self.current_filename = filepath
            self.file_modified = False
            self.update_title()

            yaml = YAML(typ='safe')
            yaml.prefix_colon = True
            yaml.preserve_quotes = True
            with open(filepath, 'r', encoding='utf-8') as file:
                data = yaml.load(file)
                if data is None:
                    self.loading_window.destroy()
                    raise ValueError(self.localization.get('yaml_inc_format_rv', 'The YAML file is empty or has an incorrect format.'))
            
            entries_to_insert = []
            grapheme_count = defaultdict(int)
            
            # Get the current maximum original_order for appending
            self.cursor.execute("SELECT MAX(original_order) FROM entries")
            max_order = self.cursor.fetchone()[0]
            current_order = (max_order + 1) if max_order is not None else 0

            entries = data.get('entries', [])
            if not isinstance(entries, list): # Support old format where top-level is a list of entries
                if isinstance(data, list):
                    entries = [item for item in data if isinstance(item, dict) and 'grapheme' in item and 'phonemes' in item]
                elif isinstance(data, dict) and 'grapheme' in data and 'phonemes' in data: # Support single entry as top-level dict
                    entries = [data]
                else:
                    self.loading_window.destroy()
                    raise ValueError(self.localization.get('yaml_dict_fromat_rv', 'Entry format incorrect. Each entry must be a dictionary or top-level list/dict.'))

            for item in entries:
                if not isinstance(item, dict):
                    self.loading_window.destroy()
                    raise ValueError(self.localization.get('yaml_dict_fromat_rv', 'Entry format incorrect. Each entry must be a dictionary.'))

                grapheme = item.get('grapheme')
                phonemes = item.get('phonemes', [])

                if grapheme is None or not isinstance(phonemes, list):
                    self.loading_window.destroy()
                    raise ValueError(self.localization.get('yaml_type_rv', 'Each entry must have a (grapheme) key and a list of (phonemes).'))
                
                # Check for duplicates in DB
                existing_grapheme = self.cursor.execute("SELECT grapheme, phonemes FROM entries WHERE grapheme = ? COLLATE NOCASE", (grapheme,)).fetchone()
                if existing_grapheme:
                    existing_phonemes = json.loads(existing_grapheme[1])
                    if existing_phonemes == phonemes:
                        continue # Skip if exact duplicate
                    
                    temp_grapheme = grapheme
                    while self.cursor.execute("SELECT grapheme FROM entries WHERE grapheme = ? COLLATE NOCASE", (temp_grapheme,)).fetchone():
                        grapheme_count[grapheme] += 1
                        temp_grapheme = f"{grapheme}({grapheme_count[grapheme]})"
                    grapheme = temp_grapheme
                
                entries_to_insert.append((grapheme, json.dumps(phonemes), current_order))
                current_order += 1

                if len(entries_to_insert) % 5000 == 0:
                    self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                    self.db_conn.commit()
                    entries_to_insert = []

            if entries_to_insert:
                self.cursor.executemany("INSERT OR IGNORE INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)", entries_to_insert)
                self.db_conn.commit()

            # Append symbols
            symbols = data.get('symbols', [])
            if isinstance(symbols, list):
                symbols_to_insert = []
                symbol_grapheme_count = defaultdict(int)
                for item in symbols:
                    if not isinstance(item, dict):
                        self.loading_window.destroy()
                        raise ValueError(self.localization.get('sym_inc_rv', 'Symbol entry format incorrect. Each entry must be a dictionary.'))
                    symbol = item.get('symbol')
                    type_ = item.get('type')
                    rename = item.get('rename', '')

                    if symbol is None or type_ is None:
                        self.loading_window.destroy()
                        raise ValueError(self.localization.get('sym_ent_inc_rv', 'Symbol entry is incomplete.'))
                    if not isinstance(type_, str):
                        self.loading_window.destroy()
                        raise ValueError(self.localization.get('sym_str_rv', 'Type must be a string representing the category.'))
                    
                    # Check for symbol duplicates in DB
                    existing_symbol = self.cursor.execute("SELECT symbol, type, rename FROM symbols WHERE symbol = ? COLLATE NOCASE", (symbol,)).fetchone()
                    if existing_symbol:
                        existing_rename = json.loads(existing_symbol[2])
                        current_rename = [rename] if isinstance(rename, str) else rename # Ensure current is a list for comparison
                        if existing_symbol[1] == type_ and existing_rename == current_rename:
                            continue # Skip if exact duplicate
                        
                        temp_symbol = symbol
                        while self.cursor.execute("SELECT symbol FROM symbols WHERE symbol = ? COLLATE NOCASE", (temp_symbol,)).fetchone():
                            symbol_grapheme_count[symbol] += 1
                            temp_symbol = f"{symbol}({symbol_grapheme_count[symbol]})"
                        symbol = temp_symbol

                    symbols_to_insert.append((symbol, type_, json.dumps(rename if isinstance(rename, list) else [rename])))
                
                if symbols_to_insert:
                    self.cursor.executemany("INSERT OR IGNORE INTO symbols (symbol, type, rename) VALUES (?, ?, ?)", symbols_to_insert)
                    self.db_conn.commit()

            # Append replacements
            replacements = data.get('replacements', [])
            if isinstance(replacements, list):
                replacements_to_insert = []
                for replacement in replacements:
                    from_config = replacement.get('from')
                    to_config = replacement.get('to')
                    
                    if from_config is None or to_config is None:
                        messagebox.showerror("Error", self.localization.get('process_repl_sym_err', 'Each replacement entry must have a (from) and a (to) symbol (string or list)'))
                        continue
                    
                    from_json = json.dumps(from_config if isinstance(from_config, list) else [from_config])
                    to_json = json.dumps(to_config if isinstance(to_config, list) else [to_config])

                    # Check for duplicates before inserting
                    existing_replacement = self.cursor.execute("SELECT id FROM replacements WHERE from_symbol = ? AND to_symbol = ?", (from_json, to_json)).fetchone()
                    if existing_replacement:
                        continue # Skip if exact duplicate
                    
                    replacements_to_insert.append((from_json, to_json))

                if replacements_to_insert:
                    self.cursor.executemany("INSERT INTO replacements (from_symbol, to_symbol) VALUES (?, ?)", replacements_to_insert)
                    self.db_conn.commit()
            
            messagebox.showinfo("Append Complete", "YAML data appended to database successfully.")

        except (YAMLError, ValueError) as e:
            self.loading_window.destroy()
            messagebox.showerror("Error", f"{self.localization.get('yaml_load_err', 'An error occurred: ')} {str(e)}")
        except Exception as e:
            self.loading_window.destroy()
            messagebox.showerror("Error", f"{self.localization.get('yaml_unex_err', 'An unexpected error occurred: ')} {str(e)}")
        finally:
            self.loading_window.destroy()
            self.update_entries_window()
    
    def open_symbol_editor(self):
        if self.symbol_editor_window is None or not self.symbol_editor_window.winfo_exists():
            self.symbol_editor_window = tk.Toplevel(self)
            self.symbol_editor_window.title("Symbols Editor")
            self.symbol_editor_window.protocol("WM_DELETE_WINDOW", self.symbol_editor_window.destroy)
            # self.save_state_before_change() # Undo/Redo removed
            self.icon(self.symbol_editor_window)

            # Configure the window's grid layout to expand with resizing
            self.symbol_editor_window.columnconfigure(0, weight=1)
            self.symbol_editor_window.rowconfigure(1, weight=1)
            self.symbol_editor_window.rowconfigure(2, weight=0)
            self.symbol_editor_window.rowconfigure(3, weight=0)

            # Create a Frame for the search bar
            search_bar_frame = ttk.Frame(self.symbol_editor_window, style='Card.TFrame')
            search_bar_frame.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
            search_bar_frame.columnconfigure(1, weight=1)

            search_button = ttk.Button(search_bar_frame, text="Search:", style='Accent.TButton', command=self.filter_symbols_treeview)
            search_button.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            self.localizable_widgets['search'] = search_button

            self.search_var = tk.StringVar()
            self.search_var.trace("w", lambda name, index, mode, sv=self.search_var: self.filter_symbols_treeview())
            search_entry = ttk.Entry(search_bar_frame, textvariable=self.search_var)
            search_entry.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
            self.create_tooltip(search_entry, 'tp_search_entry', 'Search the dictionary symbols')

            # Create a Frame to hold the Treeview and the Scrollbar
            treeview_frame = tk.Frame(self.symbol_editor_window)
            treeview_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
            treeview_frame.columnconfigure(0, weight=1)
            treeview_frame.rowconfigure(0, weight=1)

            # Create the Treeview
            self.symbol_treeview = ttk.Treeview(treeview_frame, columns=('Symbol', 'Type', 'Rename'), show='headings', height=14)
            self.symbol_treeview.heading('Symbol', text='Symbol')
            self.symbol_treeview.heading('Type', text='Type')
            self.symbol_treeview.heading('Rename', text='Replacement')
            self.symbol_treeview.column('Symbol', width=120, anchor='w')
            self.symbol_treeview.column('Type', width=120, anchor='w')
            self.symbol_treeview.column('Rename', width=120, anchor='w')
            self.symbol_treeview.grid(row=0, column=0, padx=(10,0), pady=5, sticky="nsew")

            # mouse drag
            self.symbol_treeview.bind("<ButtonPress-1>", self.start_drag_sym)
            self.symbol_treeview.bind("<B1-Motion>", self.on_drag_sym)
            self.symbol_treeview.bind("<ButtonRelease-1>", self.stop_drag_sym)
            # Deselect
            self.symbol_editor_window.bind("<Button-2>", self.deselect_symbols)
            self.symbol_editor_window.bind("<Button-3>", self.deselect_symbols)
            # Select
            self.symbol_editor_window.bind("<<TreeviewSelect>>", self.on_tree_symbol_selection)
            self.symbol_treeview.bind("<Delete>", lambda event: self.delete_symbol_entry())

            # Create and pack the Scrollbar
            self.treeview_scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.symbol_treeview.yview)
            self.treeview_scrollbar.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ns")

            self.symbol_treeview.configure(yscrollcommand=self.treeview_scrollbar.set)
            self.symbol_treeview.bind("<Escape>", lambda event: self.close())
            
            self.symbol_treeview.bind("<Double-1>", self.edit_cell_symbols)

            # Frame for action buttons
            action_button_frame = ttk.Frame(self.symbol_editor_window)
            action_button_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
            action_button_frame.grid_columnconfigure(0, weight=1)
            action_button_frame.grid_columnconfigure(1, weight=1)

            # 3 entries
            sym_entry_frame = ttk.Frame(self.symbol_editor_window)
            sym_entry_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
            sym_entry_frame.grid_columnconfigure(0, weight=1)
            sym_entry_frame.grid_columnconfigure(1, weight=1)
            sym_entry_frame.grid_columnconfigure(2, weight=1) # Adjusted for 3 columns

            action_button_frame1 = ttk.Frame(self.symbol_editor_window)
            action_button_frame1.grid(row=4, column=0, padx=10, pady=(5,15), sticky="nsew")
            action_button_frame1.grid_columnconfigure(0, weight=1)

            delete_button = ttk.Button(action_button_frame, style='TButton', text="Delete", command=self.delete_symbol_entry)
            delete_button.grid(row=1, column=0, padx=5, pady=0, sticky="nsew")
            self.localizable_widgets['del'] = delete_button
            self.create_tooltip(delete_button, 'tp_delete_ent_sym', '(Delete key) Deletes the selected entries')

            self.word_edit = ttk.Entry(sym_entry_frame)
            self.word_edit.grid(row=0, column=0, padx=5, pady=0, sticky="nsew")
            self.create_tooltip(self.word_edit, 'tp_add_ent_symbol', '(Enter) Symbol entry')
            
            self.phoneme_edit = ttk.Entry(sym_entry_frame)
            self.phoneme_edit.grid(row=0, column=1, padx=5, pady=0, sticky="nsew")
            self.create_tooltip(self.phoneme_edit, 'tp_add_ent_value', 'Value of the Symbol eg: vowel, affricate etc')

            self.rename_edit = ttk.Entry(sym_entry_frame)
            self.rename_edit.grid(row=0, column=2, padx=5, pady=0, sticky="nsew")
            self.create_tooltip(self.rename_edit, 'tp_add_ent_rname', '(Optional) For Symbol Replacement')

            add_button = ttk.Button(action_button_frame, style='TButton', text="Add", command=self.add_symbol_entry)
            add_button.grid(row=1, column=1, padx=5, pady=0, sticky="nsew")
            self.localizable_widgets['add'] = add_button
            self.create_tooltip(add_button, 'tp_add_sym_ent', '(Enter key) Adds the Entry')

            self.word_edit.bind("<Return>", self.add_symbol_entry_event)
            self.phoneme_edit.bind("<Return>", self.add_symbol_entry_event)
            self.rename_edit.bind("<Return>", self.add_symbol_entry_event)

            save_templ = ttk.Button(action_button_frame1, style='Accent.TButton', text="Save to Templates", command=self.save_yaml_template)
            save_templ.grid(row=3, column=0, padx=5, pady=0, sticky="ew")
            self.localizable_widgets['save_templ'] = save_templ
            self.create_tooltip(save_templ, 'tp_save_templ', 'Save the Symbols into a YAML Template')

            self.symbol_editor_window.bind("<Escape>", lambda event: self.symbol_editor_window.destroy())

        self.load_symbols_from_db_into_memory() # Load symbols from DB
        self.refresh_treeview_symbols()
        if self.symbol_editor_window.winfo_exists():
            self.apply_localization()

    def load_symbols_from_db_into_memory(self):
        """Loads all symbols and replacements from the database into self.symbols and self.symbols_list."""
        self.symbols.clear()
        self.symbols_list.clear()
        
        # Load symbols from DB
        self.cursor.execute("SELECT symbol, type, rename FROM symbols ORDER BY symbol COLLATE NOCASE")
        for symbol, type_str, rename_json in self.cursor.fetchall():
            rename_list = json.loads(rename_json) if rename_json else []
            self.symbols[symbol] = [type_str, rename_list]
            self.symbols_list.append({'symbol': symbol, 'type': type_str, 'rename': rename_list})
        
        # Merge replacements into symbols' rename data
        self.cursor.execute("SELECT from_symbol, to_symbol FROM replacements")
        for from_json, to_json in self.cursor.fetchall():
            from_symbol_list = json.loads(from_json)
            to_symbol_list = json.loads(to_json)

            # Join from_symbol list into a single string for key lookup if necessary
            from_symbol_key = from_symbol_list[0] if len(from_symbol_list) == 1 else ', '.join(from_symbol_list)

            if from_symbol_key in self.symbols:
                existing_rename = self.symbols[from_symbol_key][1]
                for to_item in to_symbol_list:
                    if to_item not in existing_rename:
                        existing_rename.append(to_item)
            else:
                # If from_symbol is not in symbols, add it with guessed type and the replacement
                # This part needs read_symbol_types_from_yaml or a default mechanism
                symbol_types = read_symbol_types_from_yaml(TEMPLATES) # Re-read for robustness
                type_ = symbol_types.get(from_symbol_key, 'unknown')
                self.symbols[from_symbol_key] = [type_, to_symbol_list]
                
        # Rebuild symbols_list from the updated self.symbols to reflect merged replacements
        self.symbols_list = []
        for symbol, data in self.symbols.items():
            type_ = data[0] if isinstance(data[0], str) else ''
            rename_data = data[1] if len(data) > 1 else [] # Ensure rename_data is a list
            
            # Ensure rename_data is a flat list of strings
            final_rename = []
            for r_item in rename_data:
                if isinstance(r_item, list):
                    final_rename.extend(r_item)
                else:
                    final_rename.append(r_item)
            
            self.symbols_list.append({
                'symbol': symbol,
                'type': type_,
                'rename': final_rename # Store as list
            })
        self.symbols_list.sort(key=lambda x: str(x['symbol']).lower()) # Keep sorted

    def start_drag_sym(self, event):
        # self.save_state_before_change() # Undo/Redo removed
        self.drag_start_x_sym = event.x
        self.drag_start_y_sym = event.y
        self.dragged_symbols = self.symbol_treeview.identify_row(event.y)
        self.drag_initiated_sym = False

    def on_drag_sym(self, event):
        # Update the position of the drag window during the drag
        dx = abs(event.x - self.drag_start_x_sym)
        dy = abs(event.y - self.drag_start_y_sym)
        # Determine if the movement is enough to consider it a drag (you can adjust the threshold)
        if (dx > 5 or dy > 5) and not self.drag_initiated_sym:
            self.drag_initiated_sym = True
            self.create_drag_window_sym(event)
        if self.drag_initiated_sym:
            # Update the position of the drag window during the drag
            self.drag_window_sym.geometry(f"+{event.x_root}+{event.y_root-30}")
            self.autoscroll_sym(event)

    def create_drag_window_sym(self, event):
        selected_item = self.symbol_treeview.selection()
        if selected_item:
            # Retrieve the first selected item
            item = self.symbol_treeview.item(selected_item[0])
            values = item['values']
            if values:
                # Use the appropriate value from the selected item's values
                selected_text = values[0]

                if not hasattr(self, 'drag_window_sym') or not self.drag_window_sym: # Corrected variable name
                    self.drag_window_sym = tk.Toplevel(self)
                    self.drag_window_sym.overrideredirect(True)
                    self.drag_window_sym.attributes("-alpha", 0.8)

                    # Create the label with the selected item's text
                    label = ttk.Label(self.drag_window_sym, text=f"{selected_text}", style='Accent.TButton')
                    label.pack(expand=True)

                    self.drag_window_sym.config(borderwidth=1, relief="solid")
                    self.drag_window_sym.wm_attributes("-topmost", True)
                    self.drag_window_sym.wm_attributes("-toolwindow", True)

                # self.save_state_before_change() # Undo/Redo removed

    def autoscroll_sym(self, event):
        treeview_height = self.symbol_treeview.winfo_height()
        y_relative = event.y_root - self.symbol_treeview.winfo_rooty()
        scroll_zone_size = 20

        if y_relative < scroll_zone_size:
            # Calculate scroll speed based on distance to edge
            speed = 5 - (y_relative / scroll_zone_size)
            self.symbol_treeview.yview_scroll(int(-1 * speed), "units")
        elif y_relative > (treeview_height - scroll_zone_size):
            speed = 5 - ((treeview_height - y_relative) / scroll_zone_size)
            self.symbol_treeview.yview_scroll(int(1 * speed), "units")

    def stop_drag_sym(self, event):
        if self.drag_initiated_sym and self.dragged_symbols:
            target_item = self.symbol_treeview.identify_row(event.y)
            if target_item and self.dragged_symbols != target_item:
                # Reorder in Treeview
                dragged_index = self.symbol_treeview.index(self.dragged_symbols)
                target_index = self.symbol_treeview.index(target_item)
                self.symbol_treeview.move(self.dragged_symbols, '', target_index)

                # Update self.symbols_list to reflect the new order
                # This is an in-memory operation for the display list
                dragged_entry_data = self.symbol_treeview.item(self.dragged_symbols, 'values')
                if dragged_entry_data:
                    dragged_symbol_text = dragged_entry_data[0]
                    # Find the full entry in self.symbols_list based on the symbol text
                    dragged_entry_full = next((entry for entry in self.symbols_list if entry['symbol'] == dragged_symbol_text), None)
                    if dragged_entry_full:
                        self.symbols_list.remove(dragged_entry_full)
                        self.symbols_list.insert(target_index, dragged_entry_full)
                        
                        # --- Database update for order (optional, complex) ---
                        # If you need to persist display order in DB, you'd need an 'order' column
                        # and update it here. For simplicity, current implementation does not.
                        # For now, this reordering is primarily for the current session's display.
                        # If you later save, it will likely re-sort by symbol.
                        # --- End Database update for order ---

            self.symbol_treeview.selection_set(self.dragged_symbols)
            self.symbol_treeview.see(self.dragged_symbols)

        if hasattr(self, 'drag_window_sym') and self.drag_window_sym:
            self.drag_window_sym.destroy()
            self.drag_window_sym = None

        self.drag_initiated_sym = False

    def save_yaml_template(self):
        self.cursor.execute("SELECT COUNT(*) FROM symbols")
        if self.cursor.fetchone()[0] == 0:
            messagebox.showinfo("Warning", f"{self.localization.get('yaml_temp_ns', 'No entries to save. Please add entries before saving.')}")
            return

        templates_dir = os.path.join(os.getcwd(), TEMPLATES)
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        template_path = filedialog.asksaveasfilename(
            title="Saving symbols to Template YAML",
            initialdir=templates_dir,
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if not template_path:
            return

        if not template_path.endswith('.yaml'):
            template_path += '.yaml'
        self.save_window()
        self.saving_window.update_idletasks()
        self.after(100, self.save_template_process, template_path)

    def save_template_process(self, template_path):
        yaml = YAML()
        yaml.width = 4096
        yaml.preserve_quotes = True
        yaml.allow_duplicate_keys = True
        yaml.version = (1, 2)
        
        existing_data = CommentedMap()
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                existing_data = yaml.load(file) or CommentedMap()

        symbols_entries = CommentedSeq()
        # Fetch symbols from DB
        self.cursor.execute("SELECT symbol, type, rename FROM symbols ORDER BY symbol COLLATE NOCASE")
        for symbol, type_str, rename_json in self.cursor.fetchall():
            rename_list = json.loads(rename_json) if rename_json else []
            entry = CommentedMap([('symbol', symbol), ('type', type_str)])
            if rename_list:
                entry['rename'] = rename_list
            symbols_entries.append(entry)
        
        rename_entries = CommentedSeq()
        # Fetch replacements from DB
        self.cursor.execute("SELECT from_symbol, to_symbol FROM replacements")
        for from_json, to_json in self.cursor.fetchall():
            from_list = json.loads(from_json)
            to_list = json.loads(to_json)
            entry = CommentedMap([('from', from_list), ('to', to_list)])
            rename_entries.append(entry)

        # Clear existing sections in the existing_data
        existing_data.pop('symbols', None)
        existing_data.pop('replacements', None)
        existing_data.pop('entries', None)

        existing_data['symbols'] = symbols_entries
        if rename_entries:
            existing_data['replacements'] = rename_entries
        existing_data['entries'] = CommentedSeq() # Always include an empty entries section for compatibility

        yaml.default_flow_style = None
        yaml.indent(mapping=2, sequence=4, offset=2)

        if template_path:
            try:
                with open(template_path, 'w', encoding='utf-8') as file:
                    yaml.dump(existing_data, file)
                self.update_template_combobox(self.template_combobox)
                self.saving_window.destroy()
                messagebox.showinfo("Success", f"{self.localization.get('templ_saved', 'Templates saved to ')} {template_path}")
            except Exception as e:
                messagebox.showerror("Error", f"{self.localization.get('save_yaml_f', 'Failed to save the file: ')} {e}")
            finally:
                self.saving_window.destroy()
        else:
            self.saving_window.destroy()
            messagebox.showinfo("Cancelled", f"{self.localization.get('yaml_cancel', 'Save operation cancelled.')}")

    def deselect_symbols(self, event):
        selected_items = self.symbol_treeview.selection()
        if selected_items:
            self.symbol_treeview.selection_remove(selected_items)

            self.word_edit.delete(0, tk.END)
            self.phoneme_edit.delete(0, tk.END)
            self.rename_edit.delete(0, tk.END)
        
    def add_symbol_entry_event(self, event):
        self.add_symbol_entry()

    def add_symbol_entry(self):
        symbol = self.word_edit.get().strip()
        type_str = self.phoneme_edit.get().strip()
        rename_str = self.rename_edit.get().strip()
        # self.save_state_before_change() # Undo/Redo removed

        if symbol and type_str:
            if not self.symbol_editor_window or not self.symbol_editor_window.winfo_exists():
                self.open_symbol_editor()
            
            rename_list = [item.strip() for item in rename_str.replace(" ", ",").split(',') if item.strip()] # Handles multiple spaces

            # Check if symbol already exists in DB
            existing_symbol_in_db = self.cursor.execute("SELECT symbol, type, rename FROM symbols WHERE symbol = ? COLLATE NOCASE", (symbol,)).fetchone()
            if existing_symbol_in_db:
                # Update existing symbol in DB
                db_symbol, db_type, db_rename_json = existing_symbol_in_db
                db_rename_list = json.loads(db_rename_json) if db_rename_json else []
                
                # Merge new rename values into existing ones
                merged_rename_list = list(set(db_rename_list + rename_list))
                
                self.cursor.execute("UPDATE symbols SET type = ?, rename = ? WHERE symbol = ?",
                                   (type_str, json.dumps(merged_rename_list), symbol))
                self.db_conn.commit()
                messagebox.showinfo("Symbol Updated", f"Symbol '{symbol}' updated in database.")
            else:
                # Insert new symbol into DB
                try:
                    self.cursor.execute("INSERT INTO symbols (symbol, type, rename) VALUES (?, ?, ?)",
                                       (symbol, type_str, json.dumps(rename_list)))
                    self.db_conn.commit()
                    messagebox.showinfo("Symbol Added", f"Symbol '{symbol}' added to database.")
                except sqlite3.IntegrityError:
                    messagebox.showerror("Duplicate Symbol", f"Symbol '{symbol}' already exists in the database.")
                    return # Exit if insert failed due to unique constraint

            self.load_symbols_from_db_into_memory() # Reload in-memory list from DB
            self.refresh_treeview_symbols() # Refresh Treeview display

            self.word_edit.delete(0, tk.END)
            self.phoneme_edit.delete(0, tk.END)
            self.rename_edit.delete(0, tk.END)
        else:
            messagebox.showinfo("Error", f"{self.localization.get('add_sym_ent', 'Please provide both phonemes and its respective value for the entry.')}")

    def delete_symbol_entry(self):
        selected_items = self.symbol_treeview.selection()
        if not selected_items:
            messagebox.showinfo("Notice", self.localization.get('del_no_sel', 'No items selected.'))
            return

        # self.save_state_before_change() # Undo/Redo removed
        
        symbols_to_delete = []
        for item_id in selected_items:
            item_data = self.symbol_treeview.item(item_id, 'values')
            if item_data:
                symbol = item_data[0]
                symbols_to_delete.append(symbol)
        
        if not symbols_to_delete:
            messagebox.showinfo("Notice", f"{self.localization.get('del_sym_id', 'No valid symbols selected for deletion.')}")
            return

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {len(symbols_to_delete)} selected symbol(s)?")
        if not confirm:
            return

        try:
            for symbol in symbols_to_delete:
                self.cursor.execute("DELETE FROM symbols WHERE symbol = ? COLLATE NOCASE", (symbol,))
            self.db_conn.commit()
            messagebox.showinfo("Deletion Complete", f"{len(symbols_to_delete)} symbol(s) deleted from database.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error deleting symbols: {e}")
            
        self.load_symbols_from_db_into_memory() # Reload in-memory list from DB
        self.refresh_treeview_symbols() # Refresh Treeview display

        self.phoneme_edit.delete(0, tk.END)
        self.word_edit.delete(0, tk.END)
        self.rename_edit.delete(0, tk.END)

    def add_symbols_treeview(self, word=None, value=None, rename=None):
        # This function is now primarily for adding/updating symbols in the DB,
        # then reloading the in-memory list and refreshing the Treeview.
        # The direct Treeview insertion logic from before is mostly handled by refresh_treeview_symbols.
        
        # self.save_state_before_change() # Undo/Redo removed

        if word and value is not None:
            type_str = value[0] if isinstance(value, list) and value else '' # Ensure type is a string
            rename_list = rename if isinstance(rename, list) else ([rename] if rename else [])
            
            # Check if symbol already exists in DB
            existing_symbol_in_db = self.cursor.execute("SELECT symbol, type, rename FROM symbols WHERE symbol = ? COLLATE NOCASE", (word,)).fetchone()
            if existing_symbol_in_db:
                db_symbol, db_type, db_rename_json = existing_symbol_in_db
                db_rename_list = json.loads(db_rename_json) if db_rename_json else []
                
                # Merge new rename values into existing ones
                merged_rename_list = list(set(db_rename_list + rename_list))
                
                self.cursor.execute("UPDATE symbols SET type = ?, rename = ? WHERE symbol = ?",
                                   (type_str, json.dumps(merged_rename_list), word))
                self.db_conn.commit()
            else:
                # Insert new symbol into DB
                try:
                    self.cursor.execute("INSERT INTO symbols (symbol, type, rename) VALUES (?, ?, ?)",
                                       (word, type_str, json.dumps(rename_list)))
                    self.db_conn.commit()
                except sqlite3.IntegrityError:
                    messagebox.showerror("Duplicate Symbol", f"Symbol '{word}' already exists in the database.")
                    return # Exit if insert failed due to unique constraint

            self.load_symbols_from_db_into_memory() # Reload in-memory list from DB
            self.refresh_treeview_symbols() # Refresh Treeview display

    def edit_cell_symbols(self, event):
        selected_item = self.symbol_treeview.selection()
        if not selected_item:
            return
        selected_item = selected_item[0]
        
        #column = self.symbol_treeview.identify_column(event.x) # Not directly used for placement now

        # Define the column identifiers
        grapheme_column = "#1"
        phoneme_column = "#2" # This is 'Type' in symbols table
        rename_column = "#3"

        # Retrieve initial values from Treeview
        item_values = self.symbol_treeview.item(selected_item, "values")
        if not item_values or len(item_values) < 3: # Ensure enough values
            return
            
        initial_symbol = item_values[0]
        initial_type = item_values[1]
        initial_rename = item_values[2] # Already string from Treeview

        # Destroy currently open widgets if they exist
        if self.current_entry_widgets:
            for widget in self.current_entry_widgets.values():
                widget.destroy()
            self.current_entry_widgets = {}

        # Get bounding box for the entire row to place entries correctly
        x_row, y_row, width_row, height_row = self.symbol_treeview.bbox(selected_item, '#0') # Bbox of the item
        
        # Adjust x positions for each column, relative to Treeview's rootx
        x_g = self.symbol_treeview.bbox(selected_item, grapheme_column)[0]
        x_p = self.symbol_treeview.bbox(selected_item, phoneme_column)[0]
        x_r = self.symbol_treeview.bbox(selected_item, rename_column)[0]

        # Create entry widgets for editing symbol, type, and rename
        # Place them directly over the Treeview cells using their bounding box
        self.entry_popup_sym = ttk.Entry(self.symbol_treeview)
        self.entry_popup_sym.place(x=x_g, y=y_row, width=self.symbol_treeview.column(grapheme_column, 'width'), height=height_row)
        self.entry_popup_sym.insert(0, initial_symbol)
        self.entry_popup_sym.focus_set()
        self.current_entry_widgets['entry_popup_sym'] = self.entry_popup_sym

        self.entry_popup_val = ttk.Entry(self.symbol_treeview)
        self.entry_popup_val.place(x=x_p, y=y_row, width=self.symbol_treeview.column(phoneme_column, 'width'), height=height_row)
        self.entry_popup_val.insert(0, initial_type)
        self.current_entry_widgets['entry_popup_val'] = self.entry_popup_val

        self.entry_popup_rn = ttk.Entry(self.symbol_treeview)
        self.entry_popup_rn.place(x=x_r, y=y_row, width=self.symbol_treeview.column(rename_column, 'width'), height=height_row)
        self.entry_popup_rn.insert(0, initial_rename)
        self.current_entry_widgets['entry_popup_rn'] = self.entry_popup_rn

        def on_validate(event):
            # self.save_state_before_change() # Undo/Redo removed

            new_symbol = self.entry_popup_sym.get().strip()
            new_type = self.entry_popup_val.get().strip()
            new_rename_str = self.entry_popup_rn.get().strip()
            
            # Convert new_rename_str to a list of strings
            new_rename_list = [r.strip() for r in new_rename_str.replace(" ", ",").split(',') if r.strip()]

            # Destroy entry widgets first
            for widget in self.current_entry_widgets.values():
                widget.destroy()
            self.current_entry_widgets = {}

            if not new_symbol or not new_type:
                messagebox.showerror("Input Error", "Symbol and Type cannot be empty.")
                self.load_symbols_from_db_into_memory() # Reload to restore state
                self.refresh_treeview_symbols()
                return

            try:
                # Update the database
                self.cursor.execute("UPDATE symbols SET symbol = ?, type = ?, rename = ? WHERE symbol = ?",
                                   (new_symbol, new_type, json.dumps(new_rename_list), initial_symbol))
                self.db_conn.commit()
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate Symbol", f"Symbol '{new_symbol}' already exists.")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error updating symbol: {e}")
            
            self.load_symbols_from_db_into_memory() # Reload in-memory list from DB
            self.refresh_treeview_symbols() # Refresh Treeview display

        self.entry_popup_sym.bind("<Return>", on_validate)
        self.entry_popup_val.bind("<Return>", on_validate)
        self.entry_popup_rn.bind("<Return>", on_validate)
        # Bind to treeview itself for enter key press when any entry is active
        self.symbol_treeview.bind("<Return>", on_validate)
    
    def delete_selected_symbols(self):
        # This function seems redundant with delete_symbol_entry, keeping for now
        # but should be merged or removed if not needed.
        self.delete_symbol_entry() 
    
    def filter_symbols_treeview(self):
        search_symbol = self.search_var.get().lower().replace(",", "")
        
        # Clear existing Treeview items
        self.symbol_treeview.delete(*self.symbol_treeview.get_children())

        # Populate Treeview with filtered data from in-memory self.symbols_list
        for entry in self.symbols_list:
            symbol = entry['symbol']
            type_list = entry['type']
            rename = entry.get('rename', [])
            rename_display = ', '.join(rename) if isinstance(rename, list) else str(rename) # Ensure rename is displayed as string
            
            # Apply filter logic
            if search_symbol in str(symbol).lower().replace(",", "") or \
               search_symbol in str(type_list).lower().replace(",", "") or \
               search_symbol in str(rename_display).lower().replace(",", ""):
                
                values = (symbol, type_list, rename_display)
                self.symbol_treeview.insert('', 'end', values=values, tags=('normal',))
        
        # Re-apply styling in case it was lost during delete/insert
        self.refresh_treeview_symbols_styling() # A new helper for styling only

    def refresh_treeview_symbols_styling(self):
        self.symbol_treeview.tag_configure('normal', font=self.tree_font)
        self.symbol_treeview.tag_configure('selected', font=self.tree_font_b)

        # Apply bold font to selected items
        selected_items = self.symbol_treeview.selection()
        for item in selected_items:
            self.symbol_treeview.item(item, tags=('selected',))

    def refresh_treeview_symbols(self):
        # Clear existing Treeview items
        self.symbol_treeview.delete(*self.symbol_treeview.get_children())
        
        # Populate Treeview from in-memory self.symbols_list (which is loaded from DB)
        for entry in self.symbols_list:
            symbol = entry['symbol']
            type_list = entry['type']
            rename = entry.get('rename', [])
            rename_display = ', '.join(rename) if isinstance(rename, list) else str(rename)
            values = (symbol, type_list, rename_display)
            self.symbol_treeview.insert('', 'end', values=values, tags=('normal',))
        
        self.refresh_treeview_symbols_styling()

    def on_tree_symbol_selection(self, event):
        # Reset styles for all items (could be optimized if only changing selection)
        for item in self.symbol_treeview.get_children():
            self.symbol_treeview.item(item, tags=('normal',))
        
        self.refresh_treeview_symbols_styling() # Apply bold font to selected items
        
        selected_items = self.symbol_treeview.selection()
        if selected_items:
            graphemes = []
            phoneme_lists = []
            renames = []
            
            for item_id in selected_items:
                item_data = self.symbol_treeview.item(item_id, 'values')
                if item_data:
                    if len(item_data) >= 3:
                        grapheme, phonemes_str, rename_str = item_data[:3]
                    elif len(item_data) == 2:
                        grapheme, phonemes_str = item_data
                        rename_str = ''
                    else:
                        grapheme = phonemes_str = rename_str = ''

                    phonemes = [p.strip() for p in phonemes_str.split(',')] # Parse phonemes string
                    rename = [r.strip() for r in rename_str.split(',') if r.strip()] # Parse rename string
                    
                    graphemes.append(grapheme)
                    phoneme_lists.append(phonemes)
                    renames.append(rename)
            
            graphemes_text = ', '.join(graphemes)

            if len(phoneme_lists) > 1:
                phonemes_text = '] ['.join(' '.join(str(phoneme) for phoneme in pl) for pl in phoneme_lists)
                phonemes_text = f"[{phonemes_text}]"
            else:
                phonemes_text = ' '.join(str(phoneme) for phoneme in phoneme_lists[0])

            if len(renames) > 1:
                # Concatenate all rename lists and then join unique elements for display
                all_renames_flat = []
                for sublist in renames:
                    all_renames_flat.extend(sublist)
                rename_text = ', '.join(sorted(list(set(all_renames_flat)))) # Display unique, sorted renames
            else:
                rename_text = ', '.join(renames[0]) if renames and renames[0] else '' # Display first item's renames
            
            self.word_edit.delete(0, tk.END)
            self.word_edit.insert(0, graphemes_text)
            self.phoneme_edit.delete(0, tk.END)
            self.phoneme_edit.insert(0, phonemes_text)
            self.rename_edit.delete(0, tk.END)
            self.rename_edit.insert(0, rename_text)

    def add_manual_entry_event(self, event):
        self.add_manual_entry()

    def add_manual_entry(self):
        word = self.word_entry.get().strip()
        phonemes_str = self.phoneme_entry.get().strip()
        # self.save_state_before_change() # Undo/Redo removed

        if word and phonemes_str:
            phoneme_list = [p.strip() for p in phonemes_str.split()]
            
            # Get next original_order
            self.cursor.execute("SELECT MAX(original_order) FROM entries")
            max_order = self.cursor.fetchone()[0]
            next_order = (max_order + 1) if max_order is not None else 0

            # Insert into database
            try:
                self.cursor.execute("INSERT INTO entries (grapheme, phonemes, original_order) VALUES (?, ?, ?)",
                                   (word, json.dumps(phoneme_list), next_order))
                self.db_conn.commit()
                messagebox.showinfo("Entry Added", f"Entry '{word}' added successfully.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate Entry", f"Entry '{word}' already exists. Please edit or use a unique grapheme.")
                return # Exit if insert failed due to unique constraint
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error adding entry: {e}")
                return

            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
            self.update_entries_window() # Refresh Treeview to show new entry
        else:
            messagebox.showinfo("Error", f"{self.localization.get('add_manual_ent', 'Please provide both word and phonemes for the entry.')}")

    def delete_manual_entry(self):
        selected_items = self.viewer_tree.selection()
        if not selected_items:
            messagebox.showinfo("Notice", self.localization.get('del_no_sel', 'No items selected.'))
            return
        # self.save_state_before_change() # Undo/Redo removed

        graphemes_to_delete = []
        for item_id in selected_items:
            item_values = self.viewer_tree.item(item_id, 'values')
            if item_values and len(item_values) > 1:
                graphemes_to_delete.append(item_values[1]) # Grapheme is in the second column

        if not graphemes_to_delete:
            messagebox.showinfo("Notice", f"{self.localization.get('del_ent_id', 'No valid entries found for deletion.')}")
            return

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {len(graphemes_to_delete)} selected entry(s)?")
        if not confirm:
            return
        
        try:
            for grapheme in graphemes_to_delete:
                self.cursor.execute("DELETE FROM entries WHERE grapheme = ? COLLATE NOCASE", (grapheme,))
            self.db_conn.commit()
            messagebox.showinfo("Deletion Complete", f"{len(graphemes_to_delete)} entry(s) deleted from database.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error deleting entries: {e}")
        
        self.word_entry.delete(0, tk.END)
        self.phoneme_entry.delete(0, tk.END)
        self.update_entries_window() # Refresh Treeview

    def delete_all_entries(self):
        self.cursor.execute("SELECT COUNT(*) FROM entries")
        if self.cursor.fetchone()[0] == 0:
            messagebox.showinfo("Info", f"{self.localization.get('del_all_ent', 'No entries to delete.')}")
            return

        if messagebox.askyesno("Confirm", f"{self.localization.get('dell_all_ques', 'Are you sure you want to delete all entries?')}"):
            # self.save_state_before_change() # Undo/Redo removed
            try:
                self.cursor.execute("DELETE FROM entries")
                self.db_conn.commit()
                messagebox.showinfo("Deletion Complete", "All entries deleted from database.")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error deleting all entries: {e}")
            
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
            self.update_entries_window()

    def delete_selected_entries(self):
        # This function is redundant with delete_manual_entry, will remove.
        # Keeping for now to ensure consistency, but direct calls should use delete_manual_entry.
        self.delete_manual_entry()
    
    # --- Lazy Loading for Main Treeview ---
    def update_entries_window(self):
        if self.entries_window is None or not self.entries_window.winfo_exists():
            self.entries_window = tk.Toplevel(self)
            self.entries_window.title("Entries Viewer")
            self.entries_window.protocol("WM_DELETE_WINDOW", self.close)
            self.icon(self.entries_window)

            # Create a Frame for the search bar
            search_frame = ttk.Frame(self.entries_window, style='Card.TFrame')
            search_frame.pack(fill=tk.X, padx=15, pady=10)
            search_label = ttk.Button(search_frame, text="Search:", style='Accent.TButton', command=self.iterate_search)
            search_label.pack(side=tk.LEFT, padx=(10,5), pady=5)
            self.localizable_widgets['search'] = search_label
            self.search_var = tk.StringVar()
            self.search_var.trace("w", lambda name, index, mode, sv=self.search_var: self.filter_treeview())
            self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
            self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
            self.create_tooltip(self.search_entry, 'tp_search_dict', '(Ctrl/⌘ + F) Seach your entries (index, word, or phonemes)')
            get_syms = ttk.Button(search_frame, text="Get Symbols", command=self.add_unique_phonemes)
            get_syms.pack(side=tk.LEFT, padx=5, pady=10)
            self.localizable_widgets['get_symbols_button'] = get_syms
            self.create_tooltip(get_syms, 'tp_get_syms', 'Grabs all unique phonemes and adds them to the Symbol Editor with the guessed value')
            rep2 = ttk.Button(search_frame, text="Replace", style='Accent.TButton', command=self.regex_replace_dialog)
            rep2.pack(side=tk.LEFT, padx=(5,10), pady=10)
            self.localizable_widgets['rep_button'] = rep2
            self.create_tooltip(rep2, 'tp_regex_find', '(Ctrl/⌘ + R) Regex find and Replace')

            # Create a Frame to hold the Treeview and the Scrollbar
            frame = tk.Frame(self.entries_window)
            frame.pack(fill=tk.BOTH, expand=True)

            # Create the Treeview
            self.viewer_tree = ttk.Treeview(frame, columns=('Index', 'Grapheme', 'Phonemes'),show='headings', height=20)
            self.viewer_tree.heading('#0', text='Category / Grapheme') # Changed default column heading for hierarchy
            self.viewer_tree.heading('Index', text='Index')
            self.viewer_tree.heading('Grapheme', text='Grapheme')
            self.viewer_tree.heading('Phonemes', text='Phonemes')
            self.viewer_tree.column('#0', width=120, anchor='w') # Default column for hierarchy
            self.viewer_tree.column('Index', width=50, anchor='center', stretch=False)
            self.viewer_tree.column('Grapheme', width=170, anchor='w')
            self.viewer_tree.column('Phonemes', width=230, anchor='w')

            # Create and pack the Scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.viewer_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(5))
            self.viewer_tree.configure(yscrollcommand=scrollbar.set)

            # Bind TreeviewOpen event for lazy loading
            self.viewer_tree.bind("<<TreeviewOpen>>", self._on_treeview_open)
            # deselect
            self.viewer_tree.bind("<Button-2>", self.deselect_entry)
            # select
            self.viewer_tree.bind("<<TreeviewSelect>>", self.on_tree_selection)
            # mouse drag
            self.viewer_tree.bind("<ButtonPress-1>", self.start_drag)
            self.viewer_tree.bind("<B1-Motion>", self.on_drag)
            self.viewer_tree.bind("<ButtonRelease-1>", self.stop_drag)
            self.viewer_tree.bind("<Double-1>", self.edit_cell)
            self.viewer_tree.bind("<Button-3>", self.show_context_menu)
            # keyboard entries
            self.viewer_tree.bind("<Delete>", lambda event: self.delete_manual_entry())
            self.entries_window.bind("<Escape>", lambda event: self.close())
            self.viewer_tree.bind("<Return>", self.edit_cell)
            os_name = platform.system()
            if os_name == "Windows":
                # Windows key bindings
                self.entries_window.bind("<Control-a>", lambda event: self.select_all_entries())
                self.entries_window.bind('<Control-z>', lambda event: messagebox.showinfo("Undo/Redo", "Undo/Redo is not currently supported with database backend."))
                self.entries_window.bind('<Control-y>', lambda event: messagebox.showinfo("Undo/Redo", "Undo/Redo is not currently supported with database backend."))
                self.entries_window.bind("<Control-c>", lambda event: self.copy_entry())
                self.entries_window.bind("<Control-x>", lambda event: self.cut_entry())
                self.entries_window.bind("<Control-v>", lambda event: self.paste_entry())
                self.entries_window.bind('<Control-f>', lambda event: self.search_entry.focus_set())
                self.entries_window.bind('<Control-h>', lambda event: self.regex_replace_dialog())
            elif os_name == "Darwin":
                # macOS key bindings (uses Command key)
                self.entries_window.bind("<Command-a>", lambda event: self.select_all_entries())
                self.entries_window.bind('<Command-z>', lambda event: messagebox.showinfo("Undo/Redo", "Undo/Redo is not currently supported with database backend."))
                self.entries_window.bind('<Command-y>', lambda event: messagebox.showinfo("Undo/Redo", "Undo/Redo is not currently supported with database backend."))
                self.entries_window.bind("<Command-c>", lambda event: self.copy_entry())
                self.entries_window.bind("<Command-x>", lambda event: self.cut_entry())
                self.entries_window.bind("<Command-v>", lambda event: self.paste_entry())
                self.entries_window.bind('<Command-f>', lambda event: self.search_entry.focus_set())
                self.entries_window.bind('<Command-h>', lambda event: self.regex_replace_dialog())
            else:
                self.entries_window.bind('<Control-z>', lambda event: messagebox.showinfo("Undo/Redo", "Undo/Redo is not currently supported with database backend."))
                self.entries_window.bind('<Control-y>', lambda event: messagebox.showinfo("Undo/Redo", "Undo/Redo is not currently supported with database backend."))
                self.entries_window.bind("<Control-c>", lambda event: self.copy_entry())
                self.entries_window.bind("<Control-x>", lambda event: self.cut_entry())
                self.entries_window.bind("<Control-v>", lambda event: self.paste_entry())
                self.entries_window.bind('<Control-f>', lambda event: self.search_entry.focus_set())
                self.entries_window.bind('<Control-h>', lambda event: self.regex_replace_dialog())
            # Buttons for saving or discarding changes
            button_frame = tk.Frame(self.entries_window)
            button_frame.pack(fill=tk.X, expand=False)
            clear = ttk.Button(button_frame, text="Clear all entries", style='Accent.TButton', command=self.delete_all_entries)
            clear.pack(side=tk.RIGHT, padx=(5,25), pady=10)
            self.localizable_widgets['clear_all'] = clear
            self.create_tooltip(clear, 'tp_clear_all_ent1', '(Ctrl/⌘ + A + Del) Clears all entries')
            ref = ttk.Button(button_frame, text="Refresh", style='TButton', command=self.update_entries_window)
            ref.pack(side=tk.RIGHT, padx=5, pady=10)
            self.localizable_widgets['refresh'] = ref
            self.create_tooltip(ref, 'tp_refresh', 'Refreshes the whole Treeview')
            close = ttk.Button(button_frame, text="Close", style='TButton', command=self.close)
            close.pack(side=tk.RIGHT, padx=5, pady=10)
            self.localizable_widgets['close'] = close
            self.create_tooltip(close, 'tp_close', '(Esc) Closes this window')
            minus_f = ttk.Button(button_frame, text="-", style='Accent.TButton', command=lambda: self.change_font_size(-1))
            minus_f.pack(side="left", padx=(15,5), pady=10)
            self.create_tooltip(minus_f, 'tp_zoom_out', 'Makes the entry font smaller')
            plus_f = ttk.Button(button_frame, text="+", style='Accent.TButton', command=lambda: self.change_font_size(1))
            plus_f.pack(side="left", padx=5, pady=10)
            self.create_tooltip(plus_f, 'tp_zoom_in', 'Makes the entry font bigger')

            self.viewer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15,0))
        
        self.populate_lazy_treeview_initial() # Populate or re-populate top-level
        if self.entries_window.winfo_exists():
            self.apply_localization()
        self.refresh_treeview() # Re-apply styling and selection

    def populate_lazy_treeview_initial(self):
        """Populates the Treeview with initial parent nodes for lazy loading."""
        self.viewer_tree.delete(*self.viewer_tree.get_children()) # Clear all
        self.loaded_parent_nodes = set() # Reset tracking

        # Get distinct first letters from the database
        self.cursor.execute("SELECT DISTINCT SUBSTR(grapheme, 1, 1) FROM entries WHERE grapheme IS NOT NULL ORDER BY grapheme COLLATE NOCASE")
        categories_raw = [row[0] for row in self.cursor.fetchall()]
        
        # Refine categories to handle non-alphabetic and ensure sorting
        categories = sorted(list(set([c.upper() if c.isalpha() else '#' for c in categories_raw])))
        if '#' in categories: # Ensure '#' is at the end
            categories.remove('#')
            categories.append('#')

        for category in categories:
            parent_id = f"cat_{category}"
            self.viewer_tree.insert("", "end", iid=parent_id, text=category, open=False)

            # Add a dummy child if this category has entries
            # (Check if there's at least one entry for this category)
            if category == '#':
                self.cursor.execute("SELECT COUNT(*) FROM entries WHERE SUBSTR(grapheme, 1, 1) NOT BETWEEN 'a' AND 'z' AND SUBSTR(grapheme, 1, 1) NOT BETWEEN 'A' AND 'Z'")
            else:
                self.cursor.execute("SELECT COUNT(*) FROM entries WHERE SUBSTR(grapheme, 1, 1) = ? COLLATE NOCASE", (category,))
            
            if self.cursor.fetchone()[0] > 0:
                self.viewer_tree.insert(parent_id, "end", text="Loading...", tags=("dummy",))
        
        self.entries_window.update_idletasks() # Update GUI after initial population


    def _on_treeview_open(self, event):
        """Handler for the <<TreeviewOpen>> event for lazy loading children."""
        item_id = self.viewer_tree.focus() # Get the ID of the item that was just expanded
        if not item_id or not item_id.startswith("cat_"): # Only act on our category parent nodes
            return

        # Check if children for this parent have already been loaded
        if item_id in self.loaded_parent_nodes:
            return # Already loaded, do nothing

        # Check for and remove the dummy child
        children = self.viewer_tree.get_children(item_id)
        if children and self.viewer_tree.item(children[0], "tags") == ("dummy",):
            self.viewer_tree.delete(children[0]) # Remove the "Loading..." dummy child

        # Get the category from the item_id (e.g., "cat_A" -> "A")
        category = item_id.split('_')[1]

        # Fetch actual entries for this category from the database
        if category == '#':
            # For non-alphabetic, select entries where first char is not alphabetic
            self.cursor.execute("SELECT original_order, grapheme, phonemes FROM entries WHERE SUBSTR(grapheme, 1, 1) NOT BETWEEN 'a' AND 'z' AND SUBSTR(grapheme, 1, 1) NOT BETWEEN 'A' AND 'Z' ORDER BY grapheme COLLATE NOCASE")
        else:
            self.cursor.execute("SELECT original_order, grapheme, phonemes FROM entries WHERE SUBSTR(grapheme, 1, 1) = ? COLLATE NOCASE ORDER BY grapheme COLLATE NOCASE", (category,))
        
        entries_to_load = self.cursor.fetchall()

        # Insert actual entries under the parent node
        for original_index, grapheme, phonemes_json in entries_to_load:
            phonemes = json.loads(phonemes_json) # Convert JSON string back to list
            phonemes_display = ' '.join(escape_special_characters(p) for p in phonemes)
            
            child_iid = f"{item_id}_{grapheme}" # Example: "cat_A_apple"
            self.viewer_tree.insert(item_id, "end", iid=child_iid,
                                     values=(original_index + 1, grapheme, phonemes_display), # +1 for 1-based index
                                     text=grapheme) # Display grapheme as the default text

        self.loaded_parent_nodes.add(item_id) # Mark this node as fully loaded
        self.entries_window.update_idletasks() # Refresh GUI after loading children


    def add_unique_phonemes(self):
        # Read symbol types from YAML files
        symbol_types = read_symbol_types_from_yaml(TEMPLATES)
        
        # Get all distinct phonemes from the 'entries' table
        self.cursor.execute("SELECT DISTINCT phonemes FROM entries")
        db_phoneme_json_list = [row[0] for row in self.cursor.fetchall()]

        all_phonemes_flat = set()
        for phonemes_json in db_phoneme_json_list:
            phonemes_list = json.loads(phonemes_json)
            for phoneme in phonemes_list:
                all_phonemes_flat.add(str(phoneme).strip())

        # Get existing symbols from the 'symbols' table
        self.cursor.execute("SELECT symbol FROM symbols")
        existing_symbols_in_db = {row[0] for row in self.cursor.fetchall()}

        new_phonemes_data = [] 

        for phoneme_str in sorted(all_phonemes_flat): # Sort for consistent order
            if phoneme_str and phoneme_str not in existing_symbols_in_db:
                # Determine the phoneme type, defaulting to 'unknown' if not found
                phoneme_type = symbol_types.get(phoneme_str, 'unknown')
                new_phonemes_data.append((phoneme_str, phoneme_type, json.dumps([]))) # Empty rename list
                
        if new_phonemes_data:
            try:
                self.cursor.executemany("INSERT OR IGNORE INTO symbols (symbol, type, rename) VALUES (?, ?, ?)", new_phonemes_data)
                self.db_conn.commit()
                messagebox.showinfo("Symbols Added", f"{len(new_phonemes_data)} unique phonemes added to symbols database.")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error adding unique phonemes: {e}")
        else:
            messagebox.showinfo("No New Symbols", "No new unique phonemes found to add to symbols.")

        self.open_symbol_editor() # Open/refresh the symbol editor with new data
    
    def show_context_menu(self, event):
        self.context_menu = tk.Menu(self.viewer_tree, tearoff=0)

        # Essential commands directly in the context menu
        self.context_menu.add_command(
            label=self.localization.get('cont_deselect', 'Deselect'), 
            command=self.deselect_entry_func)
        self.context_menu.add_command(
            label=self.localization.get('cont_edit', 'Edit'), 
            command=self.edit_cell)
        self.context_menu.add_command(
            label=self.localization.get('cont_delete', 'Delete'), 
            command=self.delete_manual_entry)
        self.context_menu.add_command(
            label=self.localization.get('cont_undo', 'Undo'), 
            command=lambda: messagebox.showinfo("Undo/Redo", "Undo/Redo is not currently supported with database backend."))
        self.context_menu.add_command(
            label=self.localization.get('cont_redo', 'Redo'), 
            command=lambda: messagebox.showinfo("Undo/Redo", "Undo/Redo is not currently supported with database backend."))
        
        # Cascading menu for less frequently used actions
        advanced_menu = tk.Menu(self.context_menu, tearoff=0)
        advanced_menu.add_command(
            label=self.localization.get('cont_copy', 'Copy'), 
            command=self.copy_entry)
        advanced_menu.add_command(
            label=self.localization.get('cont_cut', 'Cut'), 
            command=self.cut_entry)
        advanced_menu.add_command(
            label=self.localization.get('cont_paste', 'Paste'), 
            command=self.paste_entry)
        advanced_menu.add_command(
            label=self.localization.get('cont_select', 'Select all'), 
            command=self.select_all_entries)
        self.context_menu.add_cascade(
            label=self.localization.get('cont_more', 'More'), 
            menu=advanced_menu)

        self.context_menu.config(font=self.font_s)
        advanced_menu.config(font=self.font_s)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def edit_cell(self, event=None):
        selected_item = self.viewer_tree.selection()
        if not selected_item:
            return
        selected_item = selected_item[0] # Get the first selected item

        # The item ID is the ID of the actual entry, not a category
        # Get its original grapheme and phonemes from the Treeview's values
        item_values = self.viewer_tree.item(selected_item, "values")
        if not item_values or len(item_values) < 3:
            return

        # original_index = item_values[0] # Not directly used for editing, but can be for lookup
        initial_grapheme = item_values[1]
        initial_phonemes_str = item_values[2].replace("'", "") # Clean up display format

        # Define the column bounding boxes to place entries
        # Use #0 for first column, #1 for grapheme (column 2 in values), #2 for phonemes (column 3 in values)
        bbox_g2p_btn = self.viewer_tree.bbox(selected_item, '#0') # For the G2P button (default Treeview column)
        bbox_grapheme = self.viewer_tree.bbox(selected_item, 'Grapheme')
        bbox_phonemes = self.viewer_tree.bbox(selected_item, 'Phonemes')

        if not (bbox_g2p_btn and bbox_grapheme and bbox_phonemes):
            return # Can't get bbox, something is wrong

        # Destroy currently open widgets if they exist
        if self.current_entry_widgets:
            for widget in self.current_entry_widgets.values():
                widget.destroy()
            self.current_entry_widgets = {}
        
        # Create a button for G2P correction
        g2p_correction = ttk.Button(self.viewer_tree, text="G2P", style="Accent.TButton", command=self.is_g2p)
        g2p_correction.place(x=bbox_g2p_btn[0], y=bbox_g2p_btn[1], width=bbox_g2p_btn[2], height=bbox_g2p_btn[3])
        self.current_entry_widgets['g2p_correction'] = g2p_correction
        self.create_tooltip(g2p_correction, 'tp_g2p_correction', 'Uses the selected G2p model to phonemized the word')

        # Create entry widgets for editing grapheme and phoneme
        self.entry_popup_g = ttk.Entry(self.viewer_tree)
        self.entry_popup_g.place(x=bbox_grapheme[0], y=bbox_grapheme[1], width=bbox_grapheme[2], height=bbox_grapheme[3])
        self.entry_popup_g.insert(0, initial_grapheme)
        self.entry_popup_g.focus_set()
        self.current_entry_widgets['self.entry_popup_g'] = self.entry_popup_g
        self.create_tooltip(self.entry_popup_g, 'tp_grapheme', 'Grapheme (word) entry')

        self.entry_popup_p = ttk.Entry(self.viewer_tree)
        self.entry_popup_p.place(x=bbox_phonemes[0], y=bbox_phonemes[1], width=bbox_phonemes[2], height=bbox_phonemes[3])
        self.entry_popup_p.insert(0, initial_phonemes_str)
        self.current_entry_widgets['self.entry_popup_p'] = self.entry_popup_p
        self.create_tooltip(self.entry_popup_p, 'tp_phoneme', 'Phoneme entry')

        def on_validate(event):
            # self.save_state_before_change() # Undo/Redo removed

            new_grapheme = self.entry_popup_g.get().strip()
            new_phonemes_str = self.entry_popup_p.get().strip().replace("'", "")
            new_phoneme_list = [p.strip() for p in new_phonemes_str.split()]

            # Destroy entry widgets after editing
            for widget in self.current_entry_widgets.values():
                if widget.winfo_exists(): # Check if widget exists before destroying
                    widget.destroy()
            self.current_entry_widgets = {}

            if not new_grapheme or not new_phoneme_list:
                messagebox.showerror("Error", "Grapheme and Phonemes cannot be empty.")
                self.update_entries_window() # Refresh to restore view
                return

            try:
                # Update the database entry
                self.cursor.execute("UPDATE entries SET grapheme = ?, phonemes = ? WHERE grapheme = ?",
                                   (new_grapheme, json.dumps(new_phoneme_list), initial_grapheme))
                self.db_conn.commit()
                messagebox.showinfo("Entry Updated", f"Entry '{new_grapheme}' updated successfully.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Duplicate Grapheme", f"Grapheme '{new_grapheme}' already exists. Cannot update.")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error updating entry: {e}")

            # Refresh the affected part of the Treeview
            # Find the parent category of the original grapheme
            old_category = initial_grapheme[0].upper() if initial_grapheme and initial_grapheme[0].isalpha() else '#'
            old_parent_id = f"cat_{old_category}"

            # Find the parent category of the new grapheme
            new_category = new_grapheme[0].upper() if new_grapheme and new_grapheme[0].isalpha() else '#'
            new_parent_id = f"cat_{new_category}"

            if old_parent_id in self.loaded_parent_nodes:
                self.viewer_tree.delete(*self.viewer_tree.get_children(old_parent_id))
                self.loaded_parent_nodes.remove(old_parent_id)
                self.viewer_tree.item(old_parent_id, open=False) # Close to clear
                self.viewer_tree.item(old_parent_id, open=True) # Re-open to reload

            if new_parent_id != old_parent_id and new_parent_id in self.loaded_parent_nodes:
                self.viewer_tree.delete(*self.viewer_tree.get_children(new_parent_id))
                self.loaded_parent_nodes.remove(new_parent_id)
                self.viewer_tree.item(new_parent_id, open=False) # Close to clear
                self.viewer_tree.item(new_parent_id, open=True) # Re-open to reload
            elif new_parent_id not in self.viewer_tree.get_children() or old_parent_id not in self.viewer_tree.get_children():
                # If a new category is created or moved to an unloaded one, re-populate top-level
                self.populate_lazy_treeview_initial()

            self.entries_window.update_idletasks() # Ensure GUI update

        g2p_correction.bind("<Return>", on_validate)
        self.entry_popup_g.bind("<Return>", on_validate)
        self.entry_popup_p.bind("<Return>", on_validate)
        self.viewer_tree.bind("<Return>", on_validate)

    def is_g2p(self):
        if not self.g2p_checkbox_var.get():
            messagebox.showwarning("G2P Disabled", f"{self.localization.get('is_g2p_enabled', 'The G2P option is currently disabled. Please enable it to use this feature.')}")
        elif self.g2p_checkbox_var.get():
            self.direct_entry_change()

    def direct_entry_change(self):
        if self.entry_popup_g.get().strip():
            self.transform_text_with_g2p()
        elif not self.entry_popup_g.get().strip():
            self.entry_popup_p.delete(0, tk.END)  # Clear phoneme entry if word_entry is empty

    def transform_text_with_g2p(self):
        input_text1 = self.entry_popup_g.get()
        transformed_text1 = self.g2p_model.predict(input_text1)
        self.entry_popup_p.delete(0, tk.END)
        self.entry_popup_p.insert(0, transformed_text1)

    def start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.dragged_item = self.viewer_tree.identify_row(event.y)
        self.drag_initiated = False

    def on_drag(self, event):
        # Update the position of the drag window during the drag
        dx = abs(event.x - self.drag_start_x)
        dy = abs(event.y - self.drag_start_y)
        # Determine if the movement is enough to consider it a drag (you can adjust the threshold)
        if (dx > 5 or dy > 5) and not self.drag_initiated:
            self.drag_initiated = True
            self.create_drag_window(event)
        if self.drag_initiated:
            # Update the position of the drag window during the drag
            self.drag_window.geometry(f"+{event.x_root}+{event.y_root-30}")
            self.autoscroll(event)

    def create_drag_window(self, event):
        selected_item = self.viewer_tree.selection()
        if selected_item:
            # Retrieve the first selected item
            item = self.viewer_tree.item(selected_item[0])
            values = item['values']
            if values:
                # Use the appropriate value from the selected item's values
                selected_text = values[1]
                # selected_phoneme = values[2] # Not used for drag window display

                if not hasattr(self, 'drag_window') or not self.drag_window:
                    self.drag_window = tk.Toplevel(self)
                    self.drag_window.overrideredirect(True)
                    self.drag_window.attributes("-alpha", 0.8)

                    # Create the label with the selected item's text
                    label = ttk.Label(self.drag_window, text=f"[{selected_text}]", style='Accent.TButton')
                    label.pack(expand=True)

                    self.drag_window.config(borderwidth=1, relief="solid")
                    self.drag_window.wm_attributes("-topmost", True)
                    self.drag_window.wm_attributes("-toolwindow", True)

                # self.save_state_before_change() # Undo/Redo removed

    def autoscroll(self, event):
        treeview_height = self.viewer_tree.winfo_height()
        y_relative = event.y_root - self.viewer_tree.winfo_rooty()
        scroll_zone_size = 20

        if y_relative < scroll_zone_size:
            # Calculate scroll speed based on distance to edge
            speed = 5 - (y_relative / scroll_zone_size)
            self.viewer_tree.yview_scroll(int(-1 * speed), "units")
        elif y_relative > (treeview_height - scroll_zone_size):
            speed = 5 - ((treeview_height - y_relative) / scroll_zone_size)
            self.viewer_tree.yview_scroll(int(1 * speed), "units")

    def stop_drag(self, event):
        if self.drag_initiated and hasattr(self, 'dragged_item') and self.dragged_item:
            target_item_id = self.viewer_tree.identify_row(event.y)
            
            # Ensure target_item_id is a valid item and not a category node
            if target_item_id and self.viewer_tree.parent(target_item_id): # Check if it has a parent (i.e., not a root category)
                dragged_item_values = self.viewer_tree.item(self.dragged_item, 'values')
                target_item_values = self.viewer_tree.item(target_item_id, 'values')

                if dragged_item_values and target_item_values:
                    dragged_grapheme = dragged_item_values[1]
                    target_grapheme = target_item_values[1]

                    if dragged_grapheme != target_grapheme:
                        # Perform the reordering in the database
                        try:
                            # Get current order of all items
                            self.cursor.execute("SELECT grapheme, original_order FROM entries ORDER BY original_order")
                            all_entries_ordered = self.cursor.fetchall()
                            
                            # Create a temporary list to represent the new order
                            temp_order_list = [g for g, _ in all_entries_ordered]
                            
                            # Find and remove the dragged grapheme from its current position
                            if dragged_grapheme in temp_order_list:
                                temp_order_list.remove(dragged_grapheme)
                                
                                # Find the index of the target grapheme and insert the dragged grapheme
                                try:
                                    target_index = temp_order_list.index(target_grapheme)
                                    temp_order_list.insert(target_index, dragged_grapheme)
                                except ValueError: # Target not found (e.g., dragged to end)
                                    temp_order_list.append(dragged_grapheme)
                            else:
                                print(f"Dragged grapheme {dragged_grapheme} not found in current order list.")
                                return # Grapheme not found, exit

                            # Update the original_order in the database
                            for new_idx, g in enumerate(temp_order_list):
                                self.cursor.execute("UPDATE entries SET original_order = ? WHERE grapheme = ?", (new_idx, g))
                            self.db_conn.commit()
                            
                            messagebox.showinfo("Reorder Complete", "Entry reordered successfully in database.")
                        except sqlite3.Error as e:
                            messagebox.showerror("Database Error", f"Error reordering entry: {e}")
                            
            # Refresh Treeview with updated order
            self.update_entries_window() 
            self.viewer_tree.selection_set(self.dragged_item) # Restore selection

        if hasattr(self, 'drag_window') and self.drag_window:
            self.drag_window.destroy()
            self.drag_window = None
        self.drag_initiated = False  # Reset the drag initiated flag
                
    def regex_replace_dialog(self):
        if self.replace_window is None or not self.replace_window.winfo_exists():
            self.replace_window = tk.Toplevel(self)
            self.replace_window.resizable(False, False)
            self.replace_window.title("Regex Replace")
            # self.save_state_before_change() # Undo/Redo removed
            self.load_csv() # This loads phoneme systems, not regex patterns
  
            card_frame = ttk.Frame(self.replace_window, style='Card.TFrame')
            card_frame.pack(padx=10, pady=10, fill="both", expand=True)

            reg_frame = ttk.Frame(card_frame, style='Card.TFrame')
            reg_frame.grid(padx=10, pady=10, sticky='nsew', row=1)
            reg_frame.grid_columnconfigure(0, weight=1)
            reg_frame.grid_columnconfigure(1, weight=1)

            reg_frame1 = ttk.Frame(card_frame)
            reg_frame1.grid(padx=10, pady=10, sticky='nsew', row=0)
            reg_frame1.grid_columnconfigure(0, weight=1)
            reg_frame1.grid_columnconfigure(1, weight=20)
            
            # Fields for entering regex pattern and replacement text
            reg_pat = ttk.Label(reg_frame1, text="Regex Pattern:", font=self.font)
            reg_pat.grid(row=0, column=0, padx=10, pady=20)
            self.localizable_widgets['reg_pattern'] = reg_pat

            regex_var = tk.StringVar()
            regex_entry = ttk.Entry(reg_frame1, textvariable=regex_var, width=30)
            regex_entry.grid(row=0, column=1, padx=15, pady=5, sticky="ew")
            self.create_tooltip(regex_entry , 'tp_reg_pat', 'Find entry, use \ to escape the regex symbol')

            reg_rep = ttk.Label(reg_frame1, text="Replacement:", font=self.font)
            reg_rep.grid(row=1, column=0, padx=10, pady=5)
            self.localizable_widgets['replacement'] = reg_rep
            replace_var = tk.StringVar()
            replace_entry = ttk.Entry(reg_frame1, textvariable=replace_var, width=30)
            replace_entry.grid(row=1, column=1, padx=15, pady=5, sticky="ew")
            self.create_tooltip(replace_entry , 'tp_reg_rep', 'Replace entry')

            # Radio buttons to select target (graphemes or phonemes)
            target_var = tk.StringVar(value="Phonemes")
            ttk.Radiobutton(reg_frame, text="Graphemes", style="TRadiobutton", variable=target_var, value="Graphemes").grid(row=2, column=0, padx=(50,10), pady=(20, 5), sticky="w")
            ttk.Radiobutton(reg_frame, text="Phonemes", style="TRadiobutton", variable=target_var, value="Phonemes").grid(row=2, column=1, padx=(50,10), pady=(20, 5), sticky="w")

            # Combobox for `From Selected Phonetic System`
            phone_frame_from = ttk.Frame(reg_frame)
            phone_frame_from.grid(padx=(15,0), pady=(10,0), sticky='nsew', row=3, column=0)
            phone_frame_from.grid_columnconfigure(0, weight=30)
            phone_frame_from.grid_columnconfigure(1, weight=0)

            self.combo_from = ttk.Combobox(phone_frame_from, values=self.systems, state="readonly")
            self.combo_from.grid(row=0, column=0, sticky='nsew')
            self.combo_from.set("Phonetic System")
            self.create_tooltip(self.combo_from, 'tp_from', 'Current Phonetic System')

            to_tove_lo = ttk.Button(phone_frame_from, style='Accent.TButton', text="▶", command=self.system_phonemes)
            to_tove_lo.grid(row=0, column=1, padx=10)
            self.create_tooltip(to_tove_lo, 'tp_system_rep', 'Button for Phonetic System replacement')

            # Combobox for `To Selected Phonetic System`
            phone_frame_to = ttk.Frame(reg_frame)
            phone_frame_to.grid(padx=(0,15), pady=(10,0), sticky='nsew', row=3, column=1)
            phone_frame_to.grid_columnconfigure(0, weight=1)
            phone_frame_to.grid_columnconfigure(1, weight=0)

            self.combo_to = ttk.Combobox(phone_frame_to, values=self.systems, state="readonly")
            self.combo_to.grid(row=0, column=0, sticky='nsew')
            self.combo_to.set("Phonetic System")
            self.create_tooltip(self.combo_to, 'tp_to', 'Replacement Phonetic System')

            rep_frame = ttk.Frame(reg_frame)
            rep_frame.grid(padx=(5,15), pady=5, sticky="nsew", row=4, column=1)
            rep_frame.grid_columnconfigure(0, weight=1)
            rep_frame.grid_columnconfigure(1, weight=3)

            # Button to execute the replace operation
            apply_button = ttk.Button(rep_frame, text="Replace", style="Accent.TButton", command=lambda: replace_selected())
            apply_button.grid(row=0, column=0, padx=(0,3), pady=10, sticky="ew")
            self.localizable_widgets['apply'] = apply_button
            self.create_tooltip(apply_button, 'tp_reg_replace', 'Replaces the selected entries, if no selected, it will replace all')

            apply_button1 = ttk.Button(rep_frame, text="Replace All", style="Accent.TButton", command=lambda: apply_replace())
            apply_button1.grid(row=0, column=1, padx=(3,0), sticky="ew")
            self.localizable_widgets['apply1'] = apply_button1
            self.create_tooltip(apply_button1, 'tp_reg_replace_all', 'Replaces all of the entries')

            find_frame = ttk.Frame(reg_frame)
            find_frame.grid(padx=(10,0), pady=5, sticky="nsew", row=4, column=0)
            find_frame.grid_columnconfigure(0, weight=0)
            find_frame.grid_columnconfigure(1, weight=0)
            find_frame.grid_columnconfigure(2, weight=5)

            # Find buttons to highlight matching entries
            self.up = ttk.Button(find_frame, text="▲", style='TButton', command=lambda: self.find_next("▲", regex_var.get(), target_var.get()))
            self.up.grid(row=0, column=0, padx=(5,0), pady=10, sticky="ew")
            self.down = ttk.Button(find_frame, text="▼", style='TButton', command=lambda: self.find_next("▼", regex_var.get(), target_var.get()))
            self.down.grid(row=0, column=1, padx=6, pady=10, sticky="ew")
            find_button = ttk.Button(find_frame, text="Find", style='TButton', command=lambda: self.find_matches(regex_var.get(), target_var.get()))
            find_button.grid(row=0, column=2, padx=(0,5), pady=10, sticky="ew")
            self.localizable_widgets['find'] = find_button
            self.create_tooltip(find_button, 'tp_find_button', 'Finds and selects the searched characters')

            self.replace_window.bind("<Escape>", lambda event: self.replace_window.destroy())

        if self.replace_window.winfo_exists():
            self.apply_localization()

        def apply_replace():
            # self.save_state_before_change() # Undo/Redo removed
            pattern = regex_var.get()
            replacement = replace_var.get()
            target = target_var.get()

            try:
                compiled_pattern = re.compile(pattern)
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid regex pattern: {e}")
                return

            try:
                if target == "Graphemes":
                    # Fetch all graphemes to process
                    self.cursor.execute("SELECT id, grapheme FROM entries")
                    entries_to_update = self.cursor.fetchall()
                    
                    for entry_id, grapheme in entries_to_update:
                        new_grapheme = compiled_pattern.sub(replacement, grapheme)
                        if new_grapheme != grapheme:
                            # Update only if grapheme actually changed
                            self.cursor.execute("UPDATE entries SET grapheme = ? WHERE id = ?", (new_grapheme, entry_id))
                    self.db_conn.commit()
                elif target == "Phonemes":
                    # Fetch all phonemes to process
                    self.cursor.execute("SELECT id, phonemes FROM entries")
                    entries_to_update = self.cursor.fetchall()

                    for entry_id, phonemes_json in entries_to_update:
                        phonemes = json.loads(phonemes_json)
                        cleaned_phonemes = [p.replace("'", "") for p in phonemes] # Remove quotes for regex
                        phonemes_string = ' '.join(cleaned_phonemes)
                        modified_phoneme_string = compiled_pattern.sub(replacement, phonemes_string)

                        if modified_phoneme_string != phonemes_string:
                            new_phoneme_list = [phoneme.strip() for phoneme in modified_phoneme_string.split()]
                            self.cursor.execute("UPDATE entries SET phonemes = ? WHERE id = ?", (json.dumps(new_phoneme_list), entry_id))
                    self.db_conn.commit()
                
                messagebox.showinfo("Replace Complete", "Replacement applied to database.")
                self.update_entries_window() # Refresh Treeview after changes
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error during replacement: {e}")
            
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)


        def replace_selected():
            # self.save_state_before_change() # Undo/Redo removed
            selected_item_ids = self.viewer_tree.selection()
            
            if not selected_item_ids:
                apply_replace()  # If nothing is selected, apply to everything
                return

            pattern = regex_var.get()
            replacement = replace_var.get()
            target = target_var.get()

            try:
                compiled_pattern = re.compile(pattern)
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid regex pattern: {e}")
                return

            try:
                for item_id in selected_item_ids:
                    item_values = self.viewer_tree.item(item_id, "values")
                    # Assuming item_values is (index, grapheme, phonemes_display_string)
                    db_grapheme = item_values[1] # This is the unique identifier for DB lookup

                    # Fetch the full entry from DB using grapheme
                    self.cursor.execute("SELECT id, grapheme, phonemes FROM entries WHERE grapheme = ? COLLATE NOCASE", (db_grapheme,))
                    db_entry = self.cursor.fetchone()
                    
                    if db_entry:
                        entry_id, current_grapheme, current_phonemes_json = db_entry
                        current_phonemes_list = json.loads(current_phonemes_json)

                        if target == "Graphemes":
                            new_grapheme = compiled_pattern.sub(replacement, current_grapheme)
                            if new_grapheme != current_grapheme:
                                # Update only if grapheme actually changed
                                self.cursor.execute("UPDATE entries SET grapheme = ? WHERE id = ?", (new_grapheme, entry_id))
                        elif target == "Phonemes":
                            cleaned_phonemes = [p.replace("'", "") for p in current_phonemes_list]
                            phonemes_string = ' '.join(cleaned_phonemes)
                            modified_phoneme_string = compiled_pattern.sub(replacement, phonemes_string)

                            if modified_phoneme_string != phonemes_string:
                                new_phoneme_list = [phoneme.strip() for phoneme in modified_phoneme_string.split()]
                                self.cursor.execute("UPDATE entries SET phonemes = ? WHERE id = ?", (json.dumps(new_phoneme_list), entry_id))
                
                self.db_conn.commit()
                messagebox.showinfo("Replace Complete", "Replacement applied to selected entries in database.")
                self.update_entries_window() # Refresh Treeview after changes

            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Error during replacement: {e}")

            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)

            if self.search_var.get():
                self.filter_treeview()
        self.icon(self.replace_window)
        self.apply_localization()
    
    def system_phonemes(self):
        system_from = self.combo_from.get()
        system_to = self.combo_to.get()
        # self.save_state_before_change() # Undo/Redo removed

        # Ensure systems are selected
        if not system_from or not system_to:
            messagebox.showinfo("Error", f"{self.localization.get('select_phonetic_sys', 'Please select both From and To phonetic systems.')}")
            return

        # Ensure the selected systems are in the phoneme map
        if system_from not in self.phoneme_map or system_to not in self.phoneme_map:
            messagebox.showinfo("Error", f"{self.localization.get('phonetic_na', 'Selected phonetic systems are not available.')}")
            return

        phoneme_map_from = self.phoneme_map[system_from]
        phoneme_map_to = self.phoneme_map[system_to]

        # Create a reverse mapping for phoneme_map_to for efficient lookup
        inverse_phoneme_map_to = {v: k for k, v in phoneme_map_to.items()}

        def replace_phonemes_in_list(phoneme_sequence):
            replaced_sequence = []
            i = 0
            while i < len(phoneme_sequence):
                match_found = False
                # Check for the longest possible match from current position
                for j in range(len(phoneme_sequence), i, -1):
                    substring = ' '.join(str(phoneme) for phoneme in phoneme_sequence[i:j])
                    if substring in phoneme_map_from:
                        source_phoneme = phoneme_map_from[substring]
                        replacement = inverse_phoneme_map_to.get(str(source_phoneme), substring)
                        # Split multi-phoneme replacements by spaces
                        if ' ' in replacement:
                            replaced_sequence.extend(replacement.split(' '))
                        else:
                            replaced_sequence.append(replacement)
                        i = j
                        match_found = True
                        break
                if not match_found:
                    replaced_sequence.append(str(phoneme_sequence[i]))
                    i += 1
            return replaced_sequence

        try:
            self.cursor.execute("SELECT id, phonemes FROM entries")
            entries_to_update = self.cursor.fetchall()
            
            updates = []
            for entry_id, phonemes_json in entries_to_update:
                original_phonemes = json.loads(phonemes_json)
                updated_phonemes = replace_phonemes_in_list(original_phonemes)
                if updated_phonemes != original_phonemes: # Only update if changed
                    updates.append((json.dumps(updated_phonemes), entry_id))
            
            if updates:
                self.cursor.executemany("UPDATE entries SET phonemes = ? WHERE id = ?", updates)
                self.db_conn.commit()
                messagebox.showinfo("Phoneme System Conversion", "Phonemes converted successfully.")
                self.update_entries_window() # Refresh Treeview
            else:
                messagebox.showinfo("No Changes", "No phonemes needed conversion or no entries found.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error converting phonemes: {e}")

    def load_csv(self):
        csv_file_path = PHONEME_SYSTEMS
        # Check if the CSV file exists
        if not os.path.exists(csv_file_path):
            # Create the file with default content
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                csvfile.write(default_csv_content)
            messagebox.showinfo("File Created", f"{self.localization.get('default_csv', 'The CSV file was not found and has been created with default content.')}")

        # Load the CSV file
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader) # Read header row
            self.systems = [h.strip() for h in header if h.strip()] # Clean and store systems

            self.phoneme_map = {}
            for system in self.systems:
                self.phoneme_map[system] = {}

            for row in reader:
                # Assuming first column is the base phoneme (or source) and subsequent columns are target systems
                base_phoneme = row[0].strip()
                if not base_phoneme:
                    continue # Skip empty rows

                for i, system in enumerate(self.systems):
                    if i < len(row) and row[i].strip():
                        # Map target system phoneme to its base phoneme (for lookup)
                        self.phoneme_map[system][row[i].strip()] = base_phoneme

    def find_matches(self, pattern, target):
        # Convert pattern with square brackets into a regex pattern for exact character matches
        processed_pattern = re.sub(r'\[(.)\]', r'\1', pattern)
        compiled_pattern = re.compile(processed_pattern, re.IGNORECASE) # Ignore case for search

        items_to_highlight = []
        
        # Query database for matches
        if target == "Graphemes":
            self.cursor.execute("SELECT grapheme FROM entries ORDER BY original_order") # Order by original_order for consistency
        elif target == "Phonemes":
            self.cursor.execute("SELECT grapheme, phonemes FROM entries ORDER BY original_order")
        
        # Iterate through all entries (or a large batch) to find matches
        all_entries = self.cursor.fetchall()
        for i, entry_data in enumerate(all_entries):
            grapheme = entry_data[0] if target == "Graphemes" else entry_data[0] # Grapheme is always first
            content_to_search = grapheme if target == "Graphemes" else ' '.join(json.loads(entry_data[1])) # Phonemes for phoneme target

            if compiled_pattern.search(content_to_search):
                # Find the corresponding item in the Treeview (if loaded)
                # This part is tricky with lazy loading. We can only select what's currently visible.
                # To select an item not yet loaded, you'd have to expand its parents first.
                # For simplicity, this will only highlight already visible items.
                # For highlighting *all* matches, you'd need to expand relevant categories.
                item_id_in_tree = self.viewer_tree.identify_row(i) # This will not work with lazy loading and category parents
                
                # A more robust approach for finding in Treeview:
                # Iterate through all children of *all* loaded parents (categories)
                found_in_visible_tree = False
                for parent_iid in self.viewer_tree.get_children(): # Top-level categories
                    if parent_iid.startswith('cat_'):
                        for child_iid in self.viewer_tree.get_children(parent_iid):
                            child_values = self.viewer_tree.item(child_iid, 'values')
                            if child_values and child_values[1] == grapheme: # Match by grapheme
                                items_to_highlight.append(child_iid)
                                found_in_visible_tree = True
                                break
                    if found_in_visible_tree:
                        break # Stop if found in an expanded category
        
        # Clear the current selection to ensure only new results are highlighted
        self.viewer_tree.selection_remove(self.viewer_tree.selection())
        
        if items_to_highlight:
            self.viewer_tree.selection_set(items_to_highlight)
            self.viewer_tree.see(items_to_highlight[0])  # Ensure the first match is visible
        else:
            messagebox.showinfo("No Matches", self.localization.get('find_matches', 'No matches found.'))

    def find_next(self, direction=None, pattern=None, target=None):
        # Convert pattern with square brackets into a regex pattern for exact character matches

        def process_pattern(p):
            # Escape any special regex characters and replace `[char]` with `char`
            escaped_pattern = re.escape(p)
            # Replace \[char\] with char (literal match)
            exact_match_pattern = re.sub(r'\\\[(.)\\\]', r'\1', escaped_pattern)
            return exact_match_pattern
        
        processed_pattern = re.sub(r'\[(.)\]', r'\1', pattern)
        compiled_pattern = re.compile(processed_pattern)

        items = list(self.dictionary.items())
        current_selection = self.viewer_tree.selection()
        start_index = 0
        direction_multiplier = 1  # Default to forward direction

        if direction is not None:
            if direction == "▼":
                direction_multiplier = 1
            elif direction == "▲":
                direction_multiplier = -1

        if current_selection:
            try:
                current_item = self.viewer_tree.item(current_selection[0], "values")
                start_index = next(index for index, (grapheme, phonemes) in enumerate(items) if current_item[1] == grapheme) + direction_multiplier
            except (ValueError, StopIteration):
                pass

        # Wrap around if going beyond the last item or before the first item
        if start_index >= len(items) and direction == "▼":
            start_index = 0
        elif start_index < 0 and direction == "▲":
            start_index = len(items) - 1

        # Function to check for a match
        def check_match(index):
            grapheme, phonemes = items[index]
            if target == "Graphemes" and compiled_pattern.search(grapheme):
                return True
            if target == "Phonemes" and compiled_pattern.search(", ".join(map(str, phonemes))):
                return True
            return False

        # Iterate in the specified direction
        if direction == "▼":
            range_to_iterate = range(start_index, len(items))
        else:
            range_to_iterate = range(start_index, -1, -1)

        for index in range_to_iterate:
            if check_match(index):
                # Find the corresponding item in the Treeview
                item_id = self.viewer_tree.get_children()[index]
                self.viewer_tree.selection_set(item_id)
                self.viewer_tree.see(item_id)
                return
        # If no match found, inform the user
        messagebox.showinfo("No Match", self.localization.get('find_next_dia', 'No matching entry found.'))

    def clear_entries(self):
        self.word_entry.delete(0, tk.END)
        self.phoneme_entry.delete(0, tk.END)
        self.search_entry.delete(0, tk.END)
    
    def close(self):
        # Ensure the entries_window exists
        if hasattr(self, 'entries_window') and self.entries_window.winfo_exists():
            if not self.dictionary:
                self.entries_window.destroy()
            else:
                response = messagebox.askyesno("Notice", f"{self.localization.get('notice', 'There are entries in the viewer. Closing this window will clear them all. Are you sure you want to proceed?')}")
                if response:
                    self.file_opened = False
                    self.title(self.base_title)
                    self.viewer_tree.delete(*self.viewer_tree.get_children())
                    self.entries_window.destroy()
                    self.word_entry.delete(0, tk.END)
                    self.phoneme_entry.delete(0, tk.END)
                    self.dictionary.clear()
                    self.update_template_combobox(self.template_combobox)
                else:
                    return
        else:
            return
    
    def save_state_before_change(self):
        # Saves the current state of the dictionary before making changes
        self.undo_stack.append(copy.deepcopy(self.dictionary))
        self.redo_stack.clear()  # Clear the redo stack since new changes invalidate the old redos
    
    def select_all_entries(self):
        # Selects all entries in the viewer_tree.
        def get_all_children(node=""):
            children = self.viewer_tree.get_children(node)
            for child in children:
                children += get_all_children(child)
            return children

        all_items = get_all_children()
        self.viewer_tree.selection_set(all_items)

    def undo(self):
        if self.undo_stack:
            current_state = copy.deepcopy(self.dictionary)
            self.redo_stack.append(current_state)  # Save current state to redo stack
            
            self.dictionary = self.undo_stack.pop()
            self.refresh_treeview()
        else:
            messagebox.showinfo("Undo", f"{self.localization.get('undo_mess', 'No more actions to undo.')}")

    def redo(self):
        if self.redo_stack:
            current_state = copy.deepcopy(self.dictionary)
            self.undo_stack.append(current_state)  # Save current state to undo stack before redoing

            self.dictionary = self.redo_stack.pop()
            self.refresh_treeview()
        else:
            messagebox.showinfo("Redo", f"{self.localization.get('redo_mess', 'No more actions to redo.')}")
    
    def copy_entry(self):
        selected_items = self.viewer_tree.selection()
        if selected_items:
            # Initialize YAML object for dumping
            yaml = YAML()
            yaml.default_flow_style = False

            # Prepare entries for YAML serialization
            entries_to_copy = []
            for selected_id in selected_items:
                item = self.viewer_tree.item(selected_id)
                values = item['values']
                if len(values) >= 3:
                    grapheme = values[1]
                    phonemes_string = str(values[2]).strip()  # Ensure values[2] is treated as a string
                    phonemes = phonemes_string.split(', ')
                    # Create a CommentedMap for the entry
                    entry_map = CommentedMap([('grapheme', grapheme), ('phonemes', phonemes)])
                    entries_to_copy.append(entry_map)

            # Define a custom representer for CommentedMap to ensure the desired format
            def compact_representation(dumper, data):
                return dumper.represent_mapping(
                    'tag:yaml.org,2002:map', data, flow_style=True
                )
            yaml.representer.add_representer(CommentedMap, compact_representation)

            # Dump each entry with a preceding "- " and concatenate them
            yaml_output = io.StringIO()
            for entry in entries_to_copy:
                yaml_output.write('- ')
                yaml.dump(entry, yaml_output)
            yaml_string = yaml_output.getvalue()
            yaml_string = yaml_string.replace("'", "")
            # Copy the YAML string to clipboard
            pyperclip.copy(yaml_string)
            #messagebox.showinfo("Copy", "Selected entries have been copied to the clipboard.")
        else:
            messagebox.showinfo("Copy", f"{self.localization.get('copy_mess', 'No entry selected.')}")

    def cut_entry(self):
        selected_items = self.viewer_tree.selection()
        if selected_items:
            self.copy_entry()  # Copy entry first
            self.delete_selected_entries()
        else:
            messagebox.showinfo("Cut", f"{self.localization.get('cut_mess', 'No entry selected.')}")

    def paste_entry(self):
        self.save_state_before_change()
        clipboard_content = pyperclip.paste()
        yaml = YAML()
        # Attempt to parse YAML-like format
        try:
            # Load YAML content from clipboard
            entries = yaml.load(clipboard_content)

            if not isinstance(entries, list):
                raise ValueError("Clipboard content is not a valid YAML list.")

            entries_to_paste = []
            for entry in entries:
                if isinstance(entry, dict) and 'grapheme' in entry and 'phonemes' in entry:
                    grapheme = entry['grapheme'].strip("\"")
                    phonemes = entry['phonemes']
                    phonemes_list = [phoneme.strip("',[] \"") for phoneme in phonemes]
                    entries_to_paste.append({'grapheme': grapheme, 'phonemes': phonemes_list})
                else:
                    raise ValueError("Invalid entry format in clipboard content.")
            
            if entries_to_paste:
                selected = self.viewer_tree.selection()
                insert_index = self.viewer_tree.index(selected[-1]) + 1 if selected else 'end'
                
                for entry in entries_to_paste:
                    grapheme = entry['grapheme']
                    phonemes_list = entry['phonemes']
                    
                    # Handle duplicate graphemes
                    original_grapheme = grapheme
                    count = 1
                    match = re.match(r'^(.*)\((\d+)\)$', original_grapheme)
                    if match:
                        original_grapheme, count = match.groups()
                        count = int(count) + 1
                    
                    while grapheme in self.dictionary:
                        grapheme = f"{original_grapheme}({count})"
                        count += 1
                    
                    self.add_entry_treeview(new_word=grapheme, new_phonemes=phonemes_list, insert_index=insert_index)
                    if insert_index != 'end':
                        insert_index += 1
            else:
                messagebox.showinfo("Paste", self.localization.get('paste_mess', 'Clipboard is empty or data is invalid.'))
        except Exception as e:
            messagebox.showinfo("Paste", f"{self.localization.get('paste_mess', 'Clipboard is empty or data is invalid.')} Error: {str(e)}")
    
    def refresh_treeview(self):
        # Setup tag configurations for normal and bold fonts
        self.viewer_tree.tag_configure('normal', font=self.tree_font)
        self.viewer_tree.tag_configure('selected', font=self.tree_font_b)

        # Capture the grapheme of the currently selected item before clearing entries
        selected_grapheme = None
        selected = self.viewer_tree.selection()
        if selected:
            selected_item_id = selected[0]
            selected_item_values = self.viewer_tree.item(selected_item_id, "values")
            selected_grapheme = selected_item_values[1] if selected_item_values else None

        # Temporarily disable the treeview update during data loading
        self.viewer_tree.configure(displaycolumns=())
        self.viewer_tree.delete(*self.viewer_tree.get_children())

        # Prepare the new entries for the treeview
        items = []
        append_item = items.append
        lowercase_phonemes = self.lowercase_phonemes_var.get()
        remove_numbered_accents = self.remove_numbered_accents_var.get()

        for index, (grapheme, phonemes) in enumerate(self.dictionary.items(), start=1):
            if lowercase_phonemes:
                phonemes = [phoneme.lower() for phoneme in phonemes]
            if remove_numbered_accents:
                phonemes = self.remove_numbered_accents(phonemes)
            escaped_phonemes = ', '.join(escape_special_characters(str(phoneme)) for phoneme in phonemes)
            item_id = self.viewer_tree.insert('', 'end', values=(index, grapheme, escaped_phonemes), tags=('normal',))
            append_item(item_id)

        # Re-enable the treeview
        self.viewer_tree.configure(displaycolumns="#all")
        # If there was a previously selected grapheme, reselect its new corresponding item ID
        if selected_grapheme:
            for item_id in items:
                if self.viewer_tree.item(item_id, "values")[1] == selected_grapheme:
                    self.viewer_tree.selection_set(item_id)
                    self.viewer_tree.item(item_id, tags=('selected',))
                    self.viewer_tree.see(item_id)
                    break

    def on_tree_selection(self, event):
        selected_items = set(self.viewer_tree.selection())
        all_items = set(self.viewer_tree.get_children())
        items_to_reset = all_items - selected_items

        self.viewer_tree.tag_configure('normal', font=self.tree_font)
        self.viewer_tree.tag_configure('selected', font=self.tree_font_b)

        for item in items_to_reset:
            self.viewer_tree.item(item, tags=('normal',))
        for item in selected_items:
            self.viewer_tree.item(item, tags=('selected',))

        if selected_items:
            graphemes = []
            phoneme_lists = []
            for item_id in selected_items:
                item_data = self.viewer_tree.item(item_id, 'values')
                if item_data:
                    grapheme = item_data[1]
                    phonemes = self.dictionary.get(grapheme, [])
                    graphemes.append(grapheme)
                    phoneme_lists.append(map(str, phonemes))
            # Display only the first 3 items, with an ellipsis if there are more
            if len(graphemes) > 3:
                graphemes_text = ', '.join(graphemes[:3]) + ', ...'
            else:
                graphemes_text = ', '.join(graphemes)
            if len(phoneme_lists) > 1:
                phonemes_text = '] ['.join(' '.join(str(phoneme) for phoneme in phoneme_list) for phoneme_list in phoneme_lists[:3])
                if len(phoneme_lists) > 3:
                    phonemes_text += ', ...'
                phonemes_text = f"[{phonemes_text}]"
            else:
                phonemes_text = ' '.join(str(phoneme) for phoneme in phoneme_lists[0])
            self.word_entry.delete(0, tk.END)
            self.word_entry.insert(0, graphemes_text)
            self.phoneme_entry.delete(0, tk.END)
            self.phoneme_entry.insert(0, phonemes_text)
        else:
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)

    def deselect_entry(self, event):
        self.deselect_entry_func()
    def deselect_entry_func(self):
        # Check if there is currently a selection
        selected_items = self.viewer_tree.selection()
        if selected_items:
            self.viewer_tree.selection_remove(selected_items)

            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
    
    def add_entry_treeview(self, new_word=None, new_phonemes=None, insert_index='end'):
        if not new_word or not new_phonemes:
            return

        phoneme_display = ', '.join(new_phonemes)

        # Determine insert index (1-based)
        if insert_index == 'end' or not isinstance(insert_index, int):
            if self.viewer_tree.selection():  # If an entry is selected, insert below it
                selected_item = self.viewer_tree.selection()[-1]
                insert_index = self.viewer_tree.index(selected_item) + 2  # Below selected item
            else:
                insert_index = len(self.dictionary) + 1  # Append at end

        # Update existing entry efficiently
        if new_word in self.dictionary:
            self.dictionary[new_word] = new_phonemes  # Update dictionary
            item_id = self.word_to_item_id.get(new_word)
            if item_id:  # Update only the affected row
                self.viewer_tree.item(item_id, values=(self.viewer_tree.index(item_id) + 1, new_word, phoneme_display))
        else:
            # Insert new entry into dictionary
            self.dictionary = OrderedDict(
                list(self.dictionary.items())[:insert_index - 1] +
                [(new_word, new_phonemes)] + 
                list(self.dictionary.items())[insert_index - 1:]
            )

            # Insert into TreeView (adjust index to start from 1)
            item_id = self.viewer_tree.insert('', insert_index - 1, values=(insert_index, new_word, phoneme_display), tags=('normal',))
            self.word_to_item_id[new_word] = item_id  # Store reference for fast lookup
            self.viewer_tree.selection_set(item_id)

            if insert_index == len(self.dictionary):
                self.viewer_tree.see(item_id)  # Scroll to the new item

        # Only refresh if inserting in the middle (not needed for 'end')
        if insert_index != len(self.dictionary):
            self.refresh_treeview()

    def filter_treeview(self, exact_search=False):
        search_text = self.search_var.get().strip().lower() 
        self.viewer_tree.selection_remove(self.viewer_tree.selection())

        if not search_text:
            return

        closest_item = None
        closest_distance = float('inf')  # Start with a large distance
        matched_items = []

        for item in self.viewer_tree.get_children():
            item_values = self.viewer_tree.item(item, "values")
            matched = False

            for value in item_values:
                value_lower = str(value).lower().strip().replace(",", "")  # Convert everything to a string
                
                if exact_search:
                    # Exact match search
                    if search_text == value_lower:
                        closest_item = item
                        matched = True
                        break  # Stop checking once an exact match is found
                else:
                    # Partial match search
                    if search_text in value_lower:
                        matched_items.append(item)  # Store all matches
                        distance = abs(len(value_lower) - len(search_text))
                        if distance < closest_distance:
                            closest_item = item
                            closest_distance = distance
                        matched = True
            
            if exact_search and matched:
                break
        # Select and scroll to the closest matching item
        if closest_item:
            self.viewer_tree.selection_set(closest_item)
            self.viewer_tree.see(closest_item)
        
        # If no exact match, highlight all partial matches
        elif not exact_search and matched_items:
            self.viewer_tree.selection_set(matched_items)
            self.viewer_tree.see(matched_items[0])  # Scroll to the first match
    
    def iterate_search(self):
        search_text = self.search_var.get().strip().lower()  # Get and normalize search text
        # Clear previous selections
        self.viewer_tree.selection_remove(self.viewer_tree.selection())
        if search_text:
            items_to_select = []
            for item in self.viewer_tree.get_children():
                item_values = self.viewer_tree.item(item, "values")
                for value in item_values:
                    value_lower = value.lower().strip().replace(",", "")
                    if search_text in value_lower:
                        items_to_select.append(item)
                        break  # Stop iterating further for this item if a match is found

            # Select all matching items found during iteration
            for item in items_to_select:
                self.viewer_tree.selection_add(item)
                self.viewer_tree.see(item)
    
    def save_window(self):
        # Create a toplevel window to inform the user that the file is being saved
        self.saving_window = Toplevel(self)
        self.saving_window.overrideredirect(True)  # Remove window decorations
        self.saving_window.attributes("-topmost", True)
        # Set the desired width and height
        window_width = 250
        window_height = 100
        # Calculate the position to center the window
        screen_width = self.saving_window.winfo_screenwidth()
        screen_height = self.saving_window.winfo_screenheight()
        position_x = (screen_width // 2) - (window_width // 2)
        position_y = (screen_height // 2) - (window_height // 2)
        # Set the geometry with the calculated position
        self.saving_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        # Create a frame to act as the border and background
        frame = ttk.Frame(self.saving_window, borderwidth=2, relief="solid")
        frame.pack(fill="both", expand=True)
        # Add a label inside the frame
        label = ttk.Label(frame, text=f"{self.localization.get('save_win', 'Saving, please wait...')}", font=self.font)
        label.pack(expand=True)

    def load_window(self):
        self.loading_window = Toplevel()
        self.loading_window.overrideredirect(True)
        self.loading_window.attributes("-topmost", True)
        window_width = 250
        window_height = 100
        screen_width = self.loading_window.winfo_screenwidth()
        screen_height = self.loading_window.winfo_screenheight()
        position_x = (screen_width // 2) - (window_width // 2)
        position_y = (screen_height // 2) - (window_height // 2)
        self.loading_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        frame = ttk.Frame(self.loading_window, borderwidth=2, relief="solid")
        frame.pack(fill="both", expand=True)
        label = ttk.Label(frame, text=f"{self.localization.get('load_win', 'Loading, please wait...')}", font=self.font)
        self.localizable_widgets['load_win'] = label
        label.pack(expand=True)

    def save_as_ou_yaml(self):
        selected_template = self.template_var.get()
        # If "Current Template" is selected, ask the user to select a file to load and save.
        if not self.dictionary:
            messagebox.showinfo("Warning", f"{self.localization.get('save_yaml_m', 'No entries to save. Please add entries before saving.')}")
            return
        if selected_template == "No Template":
            template_path = "Assets/plugins/no.template.yaml"
            if not template_path:
                return
        if selected_template == "Current Template":
            template_path = filedialog.asksaveasfilename(title="Using the current YAML file as a template", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
            if not template_path:
                return
        else:
            # Define the base directory for templates and construct the file path
            data_folder = self.Templates
            template_path = os.path.join(data_folder, selected_template)
        
        # Prompt user for output file path using a file dialog if not chosen already
        if selected_template == "Current Template":
            output_file_path = template_path
        else:
            output_file_path = filedialog.asksaveasfilename(title="Save YAML File", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
        # Ensure the file path ends with .yaml
        if output_file_path and not output_file_path.endswith('.yaml'):
            output_file_path += '.yaml'
        self.save_window()
        self.saving_window.update_idletasks()
        self.after(100, self.process_save_as_ou_yaml, selected_template, template_path, output_file_path)
    def process_save_as_ou_yaml(self, selected_template, template_path, output_file_path):
        self.update_cache_button_text()
        yaml = YAML()
        yaml.width = 4096
        yaml.preserve_quotes = True
        yaml.allow_duplicate_keys = True  # Allow duplicated keys, but we'll handle duplicates manually
        yaml.version = (1, 2)  #YAML version
        
        existing_data = CommentedMap()
        # Read existing data from the template, preserving comments
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                existing_data = yaml.load(file)

        # Clear existing entries
        self.clear_entries()
        
        # Prepare new symbols entries
        symbols_entries = CommentedSeq()
        added_symbols = set()  # Track added symbols to avoid duplicates

        for symbol, values in self.symbols.items():
            if ',' in symbol or ' ' in symbol:
                continue
            escaped_symbol = symbol
            type_list = values[0] if isinstance(values[0], list) else [values[0]]
            type_str = ', '.join(f"{t}" for t in type_list)
            if escaped_symbol not in added_symbols:  # Avoid adding duplicates
                entry = CommentedMap([('symbol', escaped_symbol), ('type', type_str)])
                symbols_entries.append(entry)
                added_symbols.add(escaped_symbol)
        
        rename_entries = CommentedSeq()
        added_replacements = set()  # Track added replacements to avoid duplicates
        for symbol, data in self.symbols.items():
            if len(data) > 1:
                from_symbol = symbol if not isinstance(symbol, list) else list(symbol) 
                to_data_entries = data[1:]

                for to_entry in to_data_entries:
                    if not to_entry or (isinstance(to_entry, str) and to_entry.strip() == ''):
                        continue  # Skip empty replacements

                    # Handle comma-separated strings as lists
                    if isinstance(to_entry, str) and ',' in to_entry:
                        to_list = [item.strip() for item in to_entry.split(',') if item.strip()]
                        if not to_list:
                            continue
                        to_key = tuple(to_list)
                        to_yaml_value = to_list
                    elif isinstance(to_entry, list):
                        if not to_entry:
                            continue
                        to_key = tuple(to_entry)
                        to_yaml_value = to_entry
                    else:
                        to_key = to_entry
                        to_yaml_value = to_entry

                    if isinstance(from_symbol, str) and ',' in from_symbol:
                        from_list = [item.strip() for item in from_symbol.split(',') if item.strip()]
                        if not from_list:
                            continue
                        from_key = tuple(from_list)
                        from_yaml_value = from_list
                    elif isinstance(from_symbol, list):
                        if not from_symbol:
                            continue
                        from_key = tuple(from_symbol)
                        from_yaml_value = from_symbol
                    else:
                        from_key = from_symbol
                        from_yaml_value = from_symbol

                    replacement_key = (from_key, to_key)
                    if replacement_key not in added_replacements:
                        added_replacements.add(replacement_key)
                        entry = CommentedMap([
                            ('from', from_yaml_value),
                            ('to', to_yaml_value)
                        ])
                        rename_entries.append(entry)

        # Prepare new entries
        new_entries = CommentedSeq()
        for item in self.viewer_tree.get_children():
            item_values = self.viewer_tree.item(item, 'values')
            if len(item_values) >= 3:
                grapheme = item_values[1]
                phonemes = self.dictionary.get(grapheme, [])
                if self.lowercase_phonemes_var.get():
                    phonemes = [str(phoneme).lower() for phoneme in phonemes]
                if self.remove_numbered_accents_var.get():
                    phonemes = self.remove_numbered_accents(phonemes)
                # Convert phonemes to strings and format as list
                entry = CommentedMap([('grapheme', grapheme), ('phonemes', phonemes)])
                new_entries.append(entry)

        # If existing data has entries, clear them
        if 'symbols' in existing_data:
            del existing_data['symbols']
        if 'replacements' in existing_data:
            del existing_data['replacements']
        if 'entries' in existing_data:
            del existing_data['entries']

        # Ensure correct order: symbols, replacements, and entries
        existing_data['symbols'] = symbols_entries
        # Add 'replacements' only if there are rename_entries
        if rename_entries:  # Check if rename_entries is not empty
            existing_data['replacements'] = rename_entries
        existing_data['entries'] = new_entries

        # Configure YAML instance to use block style for specific parts
        yaml.default_flow_style = None
        yaml.indent(mapping=2, sequence=4, offset=2)
        '''
        def compact_representation(dumper, data):
            return dumper.represent_mapping(
                'tag:yaml.org,2002:map', data, flow_style=True
            )
        yaml.representer.add_representer(CommentedMap, compact_representation)
        '''
        # Save changes if the user has selected a file path
        if output_file_path:
            try:
                with open(output_file_path, 'w', encoding='utf-8') as file:
                    yaml.dump(existing_data, file)
                # Update cache file
                cache_dir = CACHE
                os.makedirs(cache_dir, exist_ok=True)
                cache_filename = (output_file_path).replace('/', '-').replace(':', '') + '.y\'all'
                cache_filepath = os.path.join(cache_dir, cache_filename)
                try:
                    with gzip.open(cache_filepath, 'wb') as cache_file:
                        pickle.dump(existing_data, cache_file)
                except Exception as e:
                    messagebox.showerror("Error", f"{self.localization.get('save_yaml_cache', 'Error occurred while saving cache: ')} {e}")
                self.saving_window.destroy()
                messagebox.showinfo("Success", f"{self.localization.get('save_yaml_saved', 'Dictionary saved to ')} {output_file_path}.")
            except Exception as e:
                messagebox.showerror("Error", f"{self.localization.get('save_yaml_f', 'Failed to save the file: ')} {e}")
            finally:
                self.saving_window.destroy()
        else:
            self.saving_window.destroy()
            messagebox.showinfo("Cancelled", f"{self.localization.get('yaml_cancel', 'Save operation cancelled.')}")
    
    def export_json(self):
        if not self.dictionary:
            messagebox.showinfo("Warning", f"{self.localization.get('save_json_m', 'No entries to save. Please add entries before saving.')}")
            return

        # Prompt user for output file path using a file dialog
        output_file_path = filedialog.asksaveasfilename(title="Save JSON File", defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not output_file_path:
            messagebox.showinfo("Cancelled", f"{self.localization.get('json_cancel', 'Save operation cancelled.')}")
            return
        
        self.save_window()
        self.saving_window.update_idletasks()
        self.after(100, self.process_save_json_file, output_file_path)

    def process_save_json_file(self, output_file_path):
        self.update_cache_button_text()
        # Prepare data for JSON format
        data = []
        for grapheme, phonemes in self.dictionary.items():
            if self.lowercase_phonemes_var.get():
                phonemes = [phoneme.lower() for phoneme in phonemes]
            if self.remove_numbered_accents_var.get():
                phonemes = self.remove_numbered_accents(phonemes)
            phoneme_str = ' '.join(map(str, phonemes))
            data.append({"w": grapheme, "p": phoneme_str})

        try:
            if output_file_path and not output_file_path.endswith('.json'):
                output_file_path += '.json'
            json_data = {"data": data}
            # Write JSON data to the selected file
            with open(output_file_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)  # Pretty print with indentation
                self.saving_window.destroy()

            # Update cache file
            cache_dir = CACHE
            cache_filename = (output_file_path).replace('/', '-').replace(':', '') + '.y\'all'
            cache_filepath = os.path.join(cache_dir, cache_filename)
            try:
                with gzip.open(cache_filepath, 'wb') as cache_file:
                    pickle.dump(data, cache_file)
            except Exception as e:
                messagebox.showerror("Error", f"{self.localization.get('json_cache_err', 'Error occurred while saving cache: ')} {e}")

            messagebox.showinfo("Success", f"{self.localization.get('json_save_dict', 'Dictionary saved to ')} {output_file_path}.")
        except Exception as e:
            self.saving_window.destroy()
            messagebox.showerror("Error", f"{self.localization.get('json_err_save', 'An error occurred while saving the JSON file: ')} {str(e)}")
    
    def export_cmudict(self):
        if not self.dictionary:
            messagebox.showinfo("Warning", f"{self.localization.get('save_cmudict_m', 'No entries to save. Please add entries before saving.')}")
            return
        # Prompt user for output file path using a file dialog
        output_file_path = filedialog.asksaveasfilename(title="Save CMUDict File", defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])

        if not output_file_path:
            messagebox.showinfo("Cancelled", f"{self.localization.get('cmudict_cancel', 'Save operation cancelled.')}")
            return
        self.save_window()
        self.saving_window.update_idletasks()
        self.after(100, self.process_save_cmudict_file, output_file_path)
    
    def process_save_cmudict_file(self, output_file_path):
        self.update_cache_button_text()
        # Prepare entries as formatted strings
        self.clear_entries()
        entries_text = []
        for grapheme, phonemes in self.dictionary.items():
            if self.lowercase_phonemes_var.get():
                phonemes = [phoneme.lower() for phoneme in phonemes]
            if self.remove_numbered_accents_var.get():
                phonemes = self.remove_numbered_accents(map(str, phonemes))
            formatted_phonemes = ' '.join(map(str, phonemes))
            entry_text = f"{grapheme}  {formatted_phonemes}\n"
            entries_text.append(entry_text)
        
        # Ensure the file path ends with .txt
        if output_file_path and not output_file_path.endswith('.txt'):
            output_file_path += '.txt'

        # Write entries to the selected file
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.writelines(entries_text)

            # Update cache file
            cache_dir = CACHE
            cache_filename = (output_file_path).replace('/', '-').replace(':', '') + '.y\'all'
            cache_filepath = os.path.join(cache_dir, cache_filename)
            try:
                with gzip.open(cache_filepath, 'wb') as cache_file:
                    pickle.dump((self.dictionary, self.comments), cache_file)
            except Exception as e:
                messagebox.showerror("Error", f"{self.localization.get('cmudict_cache_err', 'Error occurred while saving cache: ')} {e}")

            self.saving_window.destroy()
        messagebox.showinfo("Success", f"{self.localization.get('cmudict_saved_dict', 'Dictionary saved to ')} {output_file_path}.")

    def load_template(self, selection):
        # Build the full path to the template file
        file_path = os.path.join(self.Templates, selection)
        yaml = YAML(typ='safe')
        try:
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
            # Assuming the structure of the YAML file includes a dictionary key or similar
            self.dictionary.update(data.get('dictionary', {}))
            print(f"Loaded dictionary from {file_path}")
        except Exception as e:
            print(f"Failed to load file: {e}")
    
    def update_template_combobox(self, combobox):
        try:
            yaml_files = [f for f in os.listdir(TEMPLATES) if f.endswith('.yaml')]
            options = ["No Template"] + ["Current Template"] + yaml_files
            combobox['values'] = options
            self.template_var.set(options[0])

            if self.file_opened:
                self.template_var.set(options[1])
            elif self.file_opened == False and "Previous Template" not in options:
                options.insert(2, "Previous Template")
                self.template_var.set(options[2])
            else:
                self.template_var.set(options[0])
                
            self.template_combobox.bind("<<ComboboxSelected>>", self.on_template_selected)
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('temp_combo_err', 'Failed to read the directory: ')} {str(e)}")

    def on_template_selected(self, event):
        selected_template = self.template_var.get()
        if selected_template == "No Template":
            # Show a warning message to the user
            messagebox.showwarning("Notice", f"{self.localization.get('no_template', 'You have selected (No Template). All current symbols will be cleared.')}")
            self.clear_symbols_data()
            self.refresh_treeview_symbols()
        elif selected_template == "Current Template":
            self.refresh_treeview_symbols()
        elif selected_template == "Previous Template":
            self.refresh_treeview_symbols()
        else:
            self.load_symbols_from_yaml(os.path.join(TEMPLATES, selected_template))
    
    def clear_symbols_data(self):
        self.symbols.clear()
        self.symbols_list = []
        self.refresh_treeview_symbols()  # Update to reflect no data

    def load_symbols_from_yaml(self, yaml_file):
        yaml = YAML(typ='safe')
        with open(yaml_file, 'r') as file:
            data = yaml.load(file)
            symbols = data.get('symbols', [])
            replacements = data.get('replacements', [])
            self.process_symbols(symbols, replacements)
            if self.symbol_editor_window:
                self.refresh_treeview_symbols()

    def process_symbols(self, symbols, replacements):
        # Validate symbols entries
        if not all(isinstance(item, dict) for item in symbols):
            messagebox.showerror("Error", f"{self.localization.get('process_sym_m', 'All entries must be dictionaries.')}")
            return
        
        # Validate replacements entries
        if not all(isinstance(item, dict) and 'from' in item and 'to' in item for item in replacements):
            messagebox.showerror("Error", f"{self.localization.get('process_repl_sym_err', 'Each replacement entry must have a (from) and a (to) symbol (string).')}")
            return

        self.symbols.clear()
        self.symbols_list = []

        # Process symbols entries
        for item in symbols:
            symbol = item.get('symbol')
            type_ = item.get('type')
            rename_ = item.get('rename')
            if symbol is None or type_ is None or not isinstance(type_, str):
                messagebox.showerror("Error", f"{self.localization.get('process_sym_err', 'Each symbol entry must have a (symbol) and a (type) (string).')}")
                return
            if rename_:
                self.symbols[symbol] = [type_, rename_]
            else:
                self.symbols[symbol] = [type_]
            self.symbols_list.append({'symbol': symbol, 'type': type_, 'rename': rename_})

        # Process replacements entries
        for replacement in replacements:
            from_symbol = replacement.get('from')
            to_symbol = replacement.get('to')
            if from_symbol is None or to_symbol is None:
                messagebox.showerror("Error", f"{self.localization.get('process_sym_err', 'Each replacement entry must have a (from) and a (to).')}")
                return
            
            if from_symbol in self.symbols:
                # Update the existing symbol with new rename
                existing_type = self.symbols[from_symbol][0]
                existing_rename = self.symbols[from_symbol][1] if len(self.symbols[from_symbol]) > 1 else ''
                new_rename = f"{existing_rename}, {to_symbol}" if existing_rename else to_symbol
                self.symbols[from_symbol] = [existing_type, new_rename]
            else:
                # Add new symbol with the replacement as rename
                self.symbols[from_symbol] = ['', to_symbol]
            
            # Update symbols_list
            self.symbols_list = [{'symbol': k, 'type': v[0], 'rename': v[1] if len(v) > 1 else ''} for k, v in self.symbols.items()]
    
    def sort_entries(self, event):
        sort_by = self.sort_combobox.get()
        if sort_by == 'A-Z Sorting':
            sorted_items = sorted(self.dictionary.items(), key=lambda item: item[1])
        elif sort_by == 'Z-A Sorting':
            sorted_items = sorted(self.dictionary.items(), key=lambda item: item[1], reverse=True)
        else:
            # "Current Sorting" - Restore the manual order
            if self.current_order:
                sorted_items = [(key, self.dictionary[key]) for key in self.current_order]
            else:
                sorted_items = self.dictionary.items()

        # Clear the treeview
        self.viewer_tree.delete(*self.viewer_tree.get_children())
        # Rebuild the dictionary to reflect the sorted order
        new_dictionary = {}
        for grapheme, phonemes in sorted_items:
            phonemes_display = ', '.join(escape_special_characters(str(phoneme)) for phoneme in phonemes)
            self.viewer_tree.insert('', 'end', values=(grapheme, phonemes_display))
            new_dictionary[grapheme] = phonemes

        # Update the main dictionary to the new sorted one
        self.dictionary = new_dictionary
        self.update_entries_window()
    
    def it_closes(self, event):
        self.on_closing()
    
    def on_closing(self):
        # Check if self.entries_window is not None and still exists
        if self.entries_window and self.entries_window.winfo_exists():
            # Check if the dictionary is empty
            if not self.dictionary:
                self.quit()  # Quit the application if dictionary is empty
            else:
                # Ask for confirmation before quitting if dictionary is not empty
                response = messagebox.askyesno("Notice", f"{self.localization.get('gui_close', 'There are entries in the viewer. Closing this window will exit the application. Are you sure you want to proceed?')}")
                if response:
                    self.observer.stop()
                    self.observer.join()
                    self.destroy()
                    self.quit()
        else:
            self.observer.stop()
            self.observer.join()
            self.destroy()
            self.quit()

    def on_drop(self, event):
        # Retrieve raw data from the event
        raw_data = event.data
        print(f"Raw data: {raw_data}")

        # If the event data is a single path, handle it as is
        if isinstance(raw_data, str) and not raw_data.startswith('{'):
            # Simulated event or single file drop with possible spaces in the filename
            files = [raw_data]
        else:
            # Actual drop event here, the openned damn app
            files = self.tk.splitlist(raw_data)
        print(f"Files received: {files}")
        if len(files) > 1:
            messagebox.showinfo("Multiple Files", f"{self.localization.get('dnd_multi', 'Please drop only one file at a time.')}")
            return
        file = files[0]
        if not os.path.isfile(file):
            messagebox.showerror("Error Opening File", f"{self.localization.get('dnd_nf', 'File not found:')} {file}")
            return

        print(f"File dropped: {file}")
        file = os.path.normpath(file)
        ext = os.path.splitext(file)[1].lower()
        try:
            if ext == '.yaml':
                self.load_yaml_file(filepath=file)
            elif ext == '.txt':
                self.load_cmudict(filepath=file)
            elif ext == '.csv':
                self.load_cmudict(filepath=file)
            elif ext == '.tsv':
                self.load_cmudict(filepath=file)
            elif ext == '.json':
                self.load_json_file(filepath=file)
            elif ext == '.tmp':
                self.plugin_file = file
            else:
                messagebox.showerror("Error Opening File", f"{self.localization.get('dnd_file', 'Unsupported file type:')} {file}")
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('yaml_load_err', 'An error occurred:')} {str(e)}")
    
    def get_lyrics_from_tmp(self):
        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, self.load_process_lyrics)
    def load_process_lyrics(self):
        lyrics = []
        if self.plugin_file:
            with open(self.plugin_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith("Lyric="):
                        lyric = line.strip().split("=")[1]
                        if lyric and lyric not in {"R", "+", "-", "+~", "+*", "+-"}:
                            lyrics.append(lyric)

        if not self.plugin_file:
            messagebox.showerror("Error", f"{self.localization.get('no_temp_file', 'No Lyrics found on track and on the temp file.')}")
            self.loading_window.destroy()
            return None
        
        # Ensure G2P is enabled
        if not self.g2p_checkbox_var.get():
            self.g2p_checkbox_var.set(True)  # Enable G2P if it is off
            self.update_g2p_model()

        # Convert lyrics (graphemes) to phonemes using G2P
        if self.g2p_checkbox_var.get():
            word_phoneme_pairs = []
            for lyric in lyrics:
                phonemes = self.g2p_model.predict(lyric)
                joined_phonemes = ''.join(map(str, phonemes))
                word_phoneme_pairs.append((lyric, joined_phonemes))
        else:
            word_phoneme_pairs = [(lyric, lyric) for lyric in lyrics]

        # Update Treeview
        self.update_entries_window()
        selected = self.viewer_tree.selection()
        insert_index = self.viewer_tree.index(selected[-1]) + 1 if selected else 'end'

        for word, phoneme in word_phoneme_pairs:
            phonemes_list = [phon.strip("',[]\"") for phon in phoneme.split()]
            original_word = word.strip()
            count = 1
            match = re.match(r'^(.*)\((\d+)\)$', original_word)
            if match:
                original_word, count = match.groups()
                count = int(count) + 1

            while word in self.dictionary:
                word = f"{original_word}({count})"
                count += 1

            self.add_entry_treeview(new_word=word, new_phonemes=phonemes_list, insert_index=insert_index)
            if insert_index != 'end':
                insert_index += 1
                self.loading_window.destroy()
        self.loading_window.destroy()
    
    def get_yaml_from_temp(self):
        voice_dir = None
        if self.plugin_file:
            with open(self.plugin_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith("VoiceDir="):
                        voice_dir = line.strip().split("=")[1]
                        break
        if not self.plugin_file:
            messagebox.showerror("Error", f"{self.localization.get('voicedir', 'VoiceDir not found in the temp file.')}")
            return None

        # Find all .yaml files in the VoiceDir, including subfolders, excluding specific files
        excluded_files = {'character.yaml', 'dsconfig.yaml', 'enuconfig.yaml', 'config_rmdn.yaml', 'vocoder.yaml'}
        yaml_files = [file for file in glob.glob(os.path.join(voice_dir, '**', '*.yaml'), recursive=True) 
                    if os.path.basename(file) not in excluded_files]
        
        if not voice_dir:
            messagebox.showerror("Error", f"{self.localization.get('voicedir', 'VoiceDir not found in the temp file.')}")
            return None

        if not yaml_files:
            messagebox.showerror("Error", f"{self.localization.get('no_voicedir', 'No .yaml files found in the VoiceDir.')}")
            return None

        if len(yaml_files) > 1:
            messagebox.showinfo("Multiple YAML files found", f"{self.localization.get('multi_voicedir', 'Multiple .yaml files found in the VoiceDir. Opening the directory for you to choose.')}")
            selected_yaml_file = filedialog.askopenfilename(initialdir=voice_dir, title="Select YAML File", filetypes=(("YAML files", "*.yaml"), ("All files", "*.*")))
            if not selected_yaml_file:
                messagebox.showwarning("No file selected", f"{self.localization.get('yaml_nofile', 'No file was selected.')}")
                return None
        else:
            selected_yaml_file = yaml_files[0]
        
        # Load the single YAML file found
        self.load_yaml_file(selected_yaml_file)
        return selected_yaml_file

    def create_widgets(self):
        # Main notebook to contain tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        self.notebook.grid_columnconfigure(0, weight=1)
        self.notebook.grid_rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create the first tab which will contain existing widgets
        self.options_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.options_tab, text=f"{self.localization.get('tab1', 'Entry Editor')}")
        self.localizable_widgets['tab1'] = self.options_tab
        self.options_tab.grid_columnconfigure(0, weight=1)
        self.options_tab.grid_rowconfigure(0, weight=1)

        # Create a second tab for future additions
        self.additional_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.additional_tab, text=f"{self.localization.get('tab2', 'Settings')}")
        self.localizable_widgets['tab2'] = self.additional_tab 
        self.additional_tab.grid_columnconfigure(0, weight=1)
        self.additional_tab.grid_rowconfigure(0, weight=1)

        # Third Tab
        self.others_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.others_tab, text=f"{self.localization.get('tab3', 'Others')}")
        self.localizable_widgets['tab3'] = self.others_tab 
        self.others_tab.grid_columnconfigure(0, weight=1)
        self.others_tab.grid_rowconfigure(0, weight=1)

        # Fourth Tab
        self.plugins_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.plugins_tab, text=f"{self.localization.get('tab4', 'Plugins')}")
        self.localizable_widgets['tab4'] = self.plugins_tab 
        self.plugins_tab.grid_columnconfigure(0, weight=1)
        self.plugins_tab.grid_rowconfigure(0, weight=1)

        self.main_editor_widgets()
        self.settings_widgets()
        self.other_widgets()
        self.plugin_widgets()

        # Register the drop target
        self.notebook.drop_target_register(DND_FILES)
        self.notebook.dnd_bind('<<Drop>>', self.on_drop)

        self.bind("<Escape>", self.it_closes)
    
    def focus_on_plugins(self):
        self.notebook.select(self.plugins_tab)
        self.get_lyrics.focus_set()
        self.after(1000, self.vb_import_button.focus_set)
                
    def main_editor_widgets(self):
        # Options Frame setup
        options_frame = ttk.LabelFrame(self.options_tab, text="Entry options")
        options_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=2)
        self.localizable_widgets['entry_option'] = options_frame 

        # Populate the Options frame
        self.template_var = tk.StringVar()
        template_label = ttk.Label(options_frame, text="Select Template:", font=self.font)  # Default text
        template_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.localizable_widgets['select_template'] = template_label

        self.template_combobox = ttk.Combobox(options_frame, textvariable=self.template_var, state="readonly")
        self.template_combobox.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.update_template_combobox(self.template_combobox)
        self.create_tooltip(self.template_combobox, 'tp_temp_com', 'Select your pre-defined symbol template here')

        # Add localizable Checkbuttons
        remove_accents_cb = ttk.Checkbutton(options_frame, text="Remove Number Accents", style="TCheckbutton", variable=self.remove_numbered_accents_var)
        remove_accents_cb.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['remove_accents'] = remove_accents_cb
        self.create_tooltip(remove_accents_cb, 'tp_remove_accents_cb', '(Requires Refresh) Removes the vowel stress indicators found on CMUdict dictionaries (eg: [s t aa1 r] to [s t aa r])')

        lowercase_phonemes_cb = ttk.Checkbutton(options_frame, text="Make Phonemes Lowercase", style="TCheckbutton", variable=self.lowercase_phonemes_var)
        lowercase_phonemes_cb.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
        self.localizable_widgets['lowercase_phonemes'] = lowercase_phonemes_cb
        self.create_tooltip(lowercase_phonemes_cb, 'tp_lowercase_phonemes_cb', '(Requires Refresh) Makes all of the phonemes lowercased')

        # Create a checkbox to toggle tooltips
        self.tooltip_checkbox_var = tk.BooleanVar()
        self.tooltip_checkbox = ttk.Checkbutton(options_frame, text="Enable Tooltips", style='Switch.TCheckbutton', variable=self.tooltip_checkbox_var, command=self.toggle_tooltip)
        self.tooltip_checkbox.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['tooltip_checkbox'] = self.tooltip_checkbox
        self.create_tooltip(self.tooltip_checkbox, 'tp_tooltip_checkbox', 'Enables or Disables tooltip suggestions')
        self.load_tooltip_checkbox_state()

        edit_symbols = ttk.Button(options_frame, text="Edit Symbols", style='Accent.TButton', command=self.open_symbol_editor)
        edit_symbols.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['edit_sym'] = edit_symbols
        self.create_tooltip(edit_symbols, 'tp_edit_symbols', 'Edit, add, delete, replace the dictionary symbols')

        plugin_focus = ttk.Button(options_frame, text="Plugins", style='Accent.TButton', command=self.focus_on_plugins)
        plugin_focus.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['plugin_focus'] = plugin_focus
        self.create_tooltip(plugin_focus, 'tp_plugin_focus', 'Plugin feature for OpenUtau, this application must be configured on OUs plugin folder')
       
        # Sorting combobox
        self.sort_options_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(options_frame, textvariable=self.sort_options_var, state="readonly", values=('Default Sorting', 'A-Z Sorting', 'Z-A Sorting'))
        self.sort_combobox.set('Default Sorting')
        self.sort_combobox.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.sort_combobox.bind("<<ComboboxSelected>>", self.sort_entries)
        self.create_tooltip(self.sort_combobox, 'tp_sort_combobox', 'Sorts the entries')

        # Manual Entry Frame
        manual_frame = ttk.LabelFrame(self.options_tab, text="Manual Entry")  # Default text
        manual_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        manual_frame.columnconfigure(0, weight=1)
        manual_frame.columnconfigure(1, weight=1)
        self.localizable_widgets['man_entry'] = manual_frame  # Localizing the frame label

        # Entries and buttons for manual entries
        self.word_entry = ttk.Entry(manual_frame)
        self.word_entry.bind("<KeyRelease>", self.on_entry_change)
        self.word_entry.grid(row=1, column=0, padx=(15, 5), pady=10, sticky="nsew")
        self.create_tooltip(self.word_entry, 'tp_grapheme', 'Grapheme (word) entry')

        self.phoneme_entry = ttk.Entry(manual_frame)
        self.phoneme_entry.grid(row=1, column=1, padx=(5, 15), pady=10, sticky="nsew")
        self.word_entry.bind("<Return>", self.add_manual_entry_event)
        self.phoneme_entry.bind("<Return>", self.add_manual_entry_event)
        self.create_tooltip(self.phoneme_entry, 'tp_phoneme', 'Phoneme entry')

        add_entry_button = ttk.Button(manual_frame, text="Add Entry", style='Accent.TButton', command=self.add_manual_entry)
        add_entry_button.grid(row=2, column=1, columnspan=1, padx=5, pady=(5,15))
        self.localizable_widgets['add_entry'] = add_entry_button
        self.create_tooltip(add_entry_button, 'tp_add_entry', '(Enter key) Adds the entry to the Editor')

        delete_entry_button = ttk.Button(manual_frame, text="Delete Entry", style='Accent.TButton', command=self.delete_manual_entry)
        delete_entry_button.grid(row=2, column=0, columnspan=1, padx=5, pady=(5,15))
        self.localizable_widgets['delete_entry'] = delete_entry_button
        self.create_tooltip(delete_entry_button, 'tp_delete_entry', '(Delete key) Deletes the selected Entries')

        # Create frames for each set of buttons
        convert_frame = ttk.Frame(self)
        convert_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        convert_frame.columnconfigure(0, weight=1)
        convert_frame.columnconfigure(1, weight=1)
        load_frame = ttk.Frame(self)
        load_frame.grid(row=4, column=0, columnspan=1, padx=10, pady=5, sticky="ew")
        load_frame.columnconfigure(0, weight=1)
        load_frame.columnconfigure(1, weight=1)
        save_frame = ttk.Frame(self)
        save_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        cad_frame = ttk.Frame(self)
        cad_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        label_font = self.tree_font
        label_color = "gray"

        # Add buttons to each frame
        self.cmu = ttk.Button(convert_frame, text="Import CMUDict", style='TButton', command=self.load_cmudict)
        self.cmu.grid(column=1, row=0, padx=5, sticky="ew")
        self.localizable_widgets['convert_cmudict'] = self.cmu
        self.create_tooltip(self.cmu, 'tp_cmu', 'Imports CMUDict text files to the editor')

        cmux = ttk.Button(convert_frame, text="Export CMUDict", style='TButton', command=self.export_cmudict)
        cmux.grid(column=0, row=0, padx=5, sticky="ew")
        self.localizable_widgets['export_cmudict'] = cmux
        self.create_tooltip(cmux, 'tp_cmux', 'Saves and exports the CMUDict dictionary')

        self.ap_button = ttk.Button(load_frame, text= "Append Dictionary", style='TButton', command=self.append_file)
        self.ap_button.grid(column=0, row=0, padx=5, pady=5, sticky="ew")
        self.create_tooltip(self.ap_button, 'tp_append_d', 'Append or merge dictionary files to the editor')
        self.localizable_widgets['append_file'] = self.ap_button
        self.create_tooltip(cmux, 'tp_ap_button', 'Appends (add on) and merges the selected dictionary to the editor')

        open_yaml = ttk.Button(load_frame, text= "Open YAML File", style='TButton', command=self.load_yaml_file)
        open_yaml.grid(column=1, row=0, padx=5, sticky="ew")
        self.localizable_widgets['open_yaml'] = open_yaml
        self.create_tooltip(open_yaml, 'tp_open_yaml', 'Imports OpenUtau YAML dictionaries to the editor')
        
        # For saving, you might want distinct actions for each button, so specify them if they differ
        ds_save = ttk.Button(save_frame, text="Save OU Dictionary", style='Accent.TButton', command=self.save_as_ou_yaml)
        ds_save.pack(expand=True, fill="x", padx=(5), pady=(0,5))
        self.localizable_widgets['save_ou'] = ds_save
        self.create_tooltip(ds_save, 'tp_yaml_save', 'Saves the OpenUtau YAML dictionaries')

        label = ttk.Label(cad_frame, text=f"© Cadlaxa | OU Dictionary Editor {self.current_version}", font=label_font, foreground=label_color)
        label.grid(row=0, column=1, sticky="ew", pady=(0,10))
        cad_frame.columnconfigure(0, weight=1)
        cad_frame.columnconfigure(1, weight=0)
        cad_frame.columnconfigure(2, weight=1)
        self.create_tooltip(label, 'tp_label', 'hellour, cadlaxa here! q(≧▽≦q)')
        
        # Configure grid weight for overall flexibility
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=2)
        self.columnconfigure(0, weight=1)
    
    def settings_widgets(self):
        # LabelFrame for updates
        settings_frame = self.additional_tab
        update_frame = ttk.LabelFrame(settings_frame, text="Updates")
        update_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['update'] = update_frame
        update_frame.columnconfigure(0, weight=3)
        update_frame.columnconfigure(1, weight=1)

        # Button to check for updates
        update_button = ttk.Button(update_frame, text="Check for Updates", style='Accent.TButton', command=self.check_for_updates)
        update_button.grid(row=0, column=0, padx=(20,5), pady=20, sticky="ew",)
        self.localizable_widgets['update_b'] = update_button
        self.create_tooltip(update_button, 'tp_update_button', 'Checks for the latest update of this application')

        # Button to what's new
        nw_button = ttk.Button(update_frame, text="What's New", command=self.whats_new)
        nw_button.grid(row=0, column=1, padx=(5, 20), pady=20, sticky="ew",)
        self.localizable_widgets['whats_new'] = nw_button
        self.create_tooltip(nw_button, 'tp_nw_button', 'Shows the chronological changelogs of this application')

        # LabelFrame for themes
        theme_frame = ttk.LabelFrame(settings_frame, text="Themes")
        theme_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['theme'] = theme_frame
        theme_frame.columnconfigure(0, weight=1)
        theme_frame.columnconfigure(1, weight=1)

        # LabelFrame for themes
        tri_frame = ttk.Frame(theme_frame)
        tri_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        tri_frame.columnconfigure(0, weight=5)
        tri_frame.columnconfigure(2, weight=2)

        # Frame for theme combobox within the theme_frame
        self.theming = ttk.Frame(tri_frame)
        self.theming.grid(row=0, column=0, columnspan=1, padx=0, pady=0, sticky="ew")
        self.theming.columnconfigure(0, weight=1)

        self.theming1 = ttk.Frame(tri_frame)
        self.theming1.grid(row=0, column=1, columnspan=1, padx=5, pady=0)
        self.theming1.columnconfigure(0, weight=1)

        self.theming2 = ttk.Frame(tri_frame)
        self.theming2.grid(row=0, column=2, columnspan=2, padx=(5,10), pady=0, sticky="ew")
        self.theming2.columnconfigure(0, weight=1)
        self.theming2.columnconfigure(1, weight=1)

        self.theme_combobox = ttk.Combobox(self.theming, textvariable=self.accent_var, state="readonly", justify="right")
        self.theme_combobox.grid(row=0, column=0, padx=(10,5), pady=10, sticky="ew")
        self.create_tooltip(self.theme_combobox, 'tp_hex_combobox', 'Hex code of the current selected hue')

        # Hue Slider
        self.hue_slider = ttk.Scale(self.theming1, from_=0, to=360, orient="horizontal")
        self.hue_slider.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
        self.after(50, self.update_hue_slider)
        self.hue_slider.bind("<ButtonRelease-1>", lambda e: self.hex_value())
        self.create_tooltip(self.hue_slider, 'tp_theme_combobox', 'Change accent color')
        detected_hue = self.detect_hue_from_image(HUE_LUMEN)
        self.hue_slider.set(detected_hue)
        self.after(100, self.hex_value)

        self.hue_img = tk.PhotoImage(file="./Assets/track.png")
        hue_slider = tk.Canvas(self.theming1, highlightthickness = 0, width = self.hue_img.width(), height = self.hue_img.height())
        hue_slider.grid(row=1, column=0, padx=0, pady=5, sticky="ew")
        hue_slider.create_image(0, 0, image = self.hue_img, anchor = "nw")

        # Apply Button
        apply_button = ttk.Button(self.theming2, text="✓", style='Accent.TButton', command=lambda: self.apply_hue_to_sv_ttk(self.hue_slider.get()))
        apply_button.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
        self.create_tooltip(apply_button, 'tp_hex_apply', 'Apply the select hue to change the accent color')

        # Reset Button
        reset_button = ttk.Button(self.theming2, text="⟳", command=lambda: self.copy_folder_contents())
        reset_button.grid(row=0, column=1, padx=(5,0), pady=0, sticky="ew")
        self.create_tooltip(reset_button, 'tp_hex_reset', 'Resets the hue to the original color')

        radio_frame = ttk.Frame(theme_frame)
        radio_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,20), sticky="ew")
        radio_frame.columnconfigure(0, weight=1)
        radio_frame.columnconfigure(1, weight=1)
        radio_frame.columnconfigure(2, weight=1)

        # Radio button for light theme
        light_theme_button = ttk.Radiobutton(radio_frame, text="Light", value="Light", variable=self.theme_var, command=self.toggle_theme)
        light_theme_button.grid(row=1, column=0)
        self.create_tooltip(light_theme_button, 'tp_light_theme_button', 'Light Theme')

        # Radio button for dark theme
        dark_theme_button = ttk.Radiobutton(radio_frame, text="Dark", value="Dark", variable=self.theme_var, command=self.toggle_theme)
        dark_theme_button.grid(row=1, column=1)
        self.create_tooltip(dark_theme_button, 'tp_dark_theme_button', 'Dark Theme')

        # Radio button for system theme
        system_theme_button = ttk.Radiobutton(radio_frame, text="System", value="System", variable=self.theme_var, command=self.toggle_theme)
        system_theme_button.grid(row=1, column=2)
        self.create_tooltip(system_theme_button, 'tp_system_theme_button', '(Follows the system theme) Changes the Theme based on the device settings')

        t_frame = ttk.Frame(settings_frame)
        t_frame.grid(row=2, column=0, sticky="nsew")
        t_frame.columnconfigure(0, weight=5)
        t_frame.columnconfigure(1, weight=1)

        # LabelFrame for localization selection on the options tab
        localization_frame = ttk.LabelFrame(t_frame, text="Select Localization:")
        localization_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['select_local'] = localization_frame
        localization_frame.columnconfigure(0, weight=1)

        # Frame for localization combobox within the localization_frame
        self.save_loc = ttk.Frame(localization_frame)
        self.save_loc.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.save_loc.columnconfigure(1, weight=1)
        '''
        local_select = ttk.Label(self.save_loc, text="Select Localization:", font=self.font)
        local_select.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['select_local'] = local_select
        '''
        localization_combobox = ttk.Combobox(self.save_loc, textvariable=self.localization_var, state="readonly")
        localization_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.create_tooltip(localization_combobox, 'tp_localization_combobox', 'Select your language (languages are all saved in ./Templates/Localizations)')

        localization_combobox.bind("<<ComboboxSelected>>", self.localization_selected)
        self.update_localization_combobox(localization_combobox)

        # LabelFrame for localization selection on the options tab
        cache_frame = ttk.LabelFrame(t_frame, text="Clear Cache")
        cache_frame.grid(row=1, column=1, padx=(0,10), pady=10, sticky="nsew")
        #self.localizable_widgets['cache_op'] = cache_frame
        cache_frame.columnconfigure(0, weight=1)

        self.cache_b = ttk.Button(cache_frame, text="Cache", style='Accent.TButton', command=self.clear_cache)
        self.cache_b.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.create_tooltip(self.cache_b, 'tp_cache_b', 'Clears out the Cache folder')
        if not CACHE.exists():
            CACHE.mkdir(parents=True, exist_ok=True)
        self.observer = Observer()
        self.handler = CacheHandler(update_callback=self.update_cache_button_text)
        self.observer.schedule(self.handler, CACHE, recursive=True)
        self.observer.start()
        self.update_cache_button_text()
        if self.file_opened:
            self.update_cache_button_text()
    
    def get_cache_size(self):
        # Calculates the total size of the cache folder
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(CACHE):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size

    def format_size(self, size_bytes):
        # Formats the size in KB, MB, or GB 
        if size_bytes < 1024:
            return f"{size_bytes:.2f} bytes"
        elif size_bytes < 1024**2:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes / (1024**2):.2f} MB"
        else:
            return f"{size_bytes / (1024**3):.2f} GB"

    def update_cache_button_text(self):
        # Updates the cache button text to display the current cache folder size
        try:
            size = self.get_cache_size()
            size_text = self.format_size(size)
            # Ensure UI update happens on the main thread
            self.after(0, lambda: self.cache_b.config(text=f"Cache: {size_text}"))
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('err_update_cache', 'An error occurred while updating cache size:')} {e}")

    def clear_cache(self):
        # Clears the cache folder
        try:
            for dirpath, dirnames, filenames in os.walk(CACHE, topdown=False):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    os.remove(filepath)
                for dirname in dirnames:
                    os.rmdir(os.path.join(dirpath, dirname))
            # Update the cache size display after clearing
            self.update_cache_button_text()
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('err_cl_cache', 'An error occurred while clearing the cache:')} {e}")
        
    def other_widgets(self):
        self.other_frame = ttk.Frame(self.others_tab)
        self.other_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")
        self.other_frame.columnconfigure(0, weight=1)
        self.other_frame.columnconfigure(1, weight=1)

        # Frame for Synthv controls
        synthv_frame = ttk.LabelFrame(self.other_frame, text="Synthv")
        synthv_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        synthv_frame.columnconfigure(0, weight=1)

        # Synthv Import/Export
        synthv_export = ttk.Button(synthv_frame, style='Accent.TButton', text="Export Dictionary", command=self.export_json)
        synthv_export.grid(row=2, column=0, padx=10, pady=(5,10), sticky="ew")
        self.localizable_widgets['export'] = synthv_export

        synthv_import = ttk.Button(synthv_frame, text="Import Dictionary", style='TButton', command=self.load_json_file)
        synthv_import.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['import'] = synthv_import

        # Frame for CSV and TSV
        ui_frame = ttk.LabelFrame(self.other_frame, text="CVS and TSV")
        ui_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ui_frame.columnconfigure(0, weight=1)

        tsv = ttk.Button(ui_frame, style='Accent.TButton', text="Export TSV", command=self.export_csv_tsv)
        tsv.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['tsv'] = tsv

        csv = ttk.Button(ui_frame, text="Export CSV", style='TButton', command=self.export_csv_tsv)
        csv .grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['csv'] = csv 

        # Frame for UI controls (placeholder name)
        ui_frame = ttk.LabelFrame(self.other_frame, text="Adding more in the future")
        ui_frame.grid(row=1, column=0, padx=5, pady=10, sticky="nsew")
        ui_frame.columnconfigure(0, weight=1)

        ui_export_button = ttk.Button(ui_frame, state="disabled", style='Accent.TButton', text="Export Dictionary", command=self.export_json)
        ui_export_button.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        #self.localizable_widgets['export'] = ui_export_button

        ui_import_button = ttk.Button(ui_frame, state="disabled", text="Import Dictionary", style='TButton', command=self.load_json_file)
        ui_import_button.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        #self.localizable_widgets['import'] = ui_import_button

        self.other_frame1 = ttk.Frame(self.others_tab)
        self.other_frame1.grid(row=1, column=0, columnspan=1, padx=5, pady=10, sticky="nsew")
        self.other_frame1.columnconfigure(0, weight=1)

        # Frame for G2P
        g2p_frame = ttk.LabelFrame(self.other_frame1, text="G2P Suggestions:")
        g2p_frame.grid(row=0, column=0, padx=5, pady=0, sticky="nsew")
        g2p_frame.columnconfigure(0, weight=1)
        g2p_frame.columnconfigure(1, weight=1)
        self.localizable_widgets['g2p'] = g2p_frame

        # Adding Checkbox
        self.g2p_checkbox_var = tk.BooleanVar()
        g2p_checkbox = ttk.Checkbutton(g2p_frame, text="Enable G2P", style='Switch.TCheckbutton', variable=self.g2p_checkbox_var)
        g2p_checkbox.grid(row=0, column=0, padx=(20, 5), pady=15, sticky="w")
        self.localizable_widgets['g2p_check'] = g2p_checkbox
        self.create_tooltip(g2p_checkbox, 'tp_g2p_checkbox', 'Enable or Disable the G2p suggestions')
        self.load_g2p_checkbox_state()

        self.g2p_selection = ttk.Combobox(g2p_frame, state='readonly')
        self.g2p_selection.grid(row=0, column=1, padx=(5, 20), pady=5, sticky="ew")
        self.update_g2p_selection()
        self.load_last_g2p()
        self.create_tooltip(self.g2p_selection, 'tp_g2p_selection', 'Select your G2p model here')
        self.load_last_g2p()

        self.g2p_selection.bind("<<ComboboxSelected>>", self.update_g2p_model)
        self.update_g2p_model()

        # Bind checkbox variable to a callback function
        self.g2p_checkbox_var.trace_add("write", self.on_checkbox_change)
    
    def plugin_widgets(self):
        self.plugin_frame = ttk.Frame(self.plugins_tab)
        self.plugin_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")
        self.plugin_frame.columnconfigure(0, weight=1)
        self.plugin_frame.columnconfigure(1, weight=1)

        # Frame for OU Plugin
        self.plug_frame = ttk.LabelFrame(self.plugin_frame, text="Plug-in")
        self.plug_frame.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        self.plug_frame.columnconfigure(0, weight=1)
        self.localizable_widgets['plugin'] = self.plug_frame

        self.get_lyrics = ttk.Button(self.plug_frame, style='TButton', text="Get Lyrics from Track", command=self.get_lyrics_from_tmp)
        self.get_lyrics.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['get_lyrics'] = self.get_lyrics
        self.create_tooltip(self.get_lyrics, 'tp_get_lyrics', 'Imports all of the tracks lyrics with phonemes phonemized by the g2p model')

        self.vb_import_button = ttk.Button(self.plug_frame, style='Accent.TButton' , text="Import VB Dictionary", command=self.get_yaml_from_temp)
        self.vb_import_button.grid(row=2, column=0, padx=10, pady=(5,10), sticky="ew")
        self.localizable_widgets['import_vb'] = self.vb_import_button
        self.create_tooltip(self.vb_import_button, 'tp_vb_import_button', '(OpenUtau plugin) Imports the singers dictionary')

        # Frame for Terminal
        self.terminal = ttk.LabelFrame(self.plugin_frame, text="YAML Generator")
        self.terminal.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")
        self.terminal.columnconfigure(0, weight=1)
        self.localizable_widgets['console'] = self.terminal

        self.dict_gen = ttk.Button(self.terminal, style='TButton', text="Reclist to Yaml Template", command=self.import_gen_yaml_temp_data)
        self.dict_gen.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['rec_yaml_gen'] = self.dict_gen
        self.create_tooltip(self.terminal, 'tp_rec_yaml_gen', 'Generates the Symbols and its value using a reclist')

        #self.vb_import_button = ttk.Button(self.terminal, style='Accent.TButton' , text="Import VB Dictionary", command=self.get_yaml_from_temp)
        #self.vb_import_button.grid(row=2, column=0, padx=10, pady=(5,10), sticky="ew")
        #self.localizable_widgets['import_vb'] = self.vb_import_button
    
    def append_file(self):
        self.append_window = tk.Toplevel(self)
        self.append_window.resizable(False, False)
        self.append_window.overrideredirect(True)

        # Place the window near the button
        self.append_window.update_idletasks()  # Ensure dimensions are calculated

        window_width = self.append_window.winfo_width()
        window_height = self.append_window.winfo_height()
        x = self.ap_button.winfo_rootx() + (self.ap_button.winfo_width() // 2) - (window_width // 2)
        y = self.ap_button.winfo_rooty() - 230
        self.append_window.geometry(f"+{x}+{y}")

        border = ttk.Frame(self.append_window, borderwidth=2, relief="solid")
        border.pack(fill="both", expand=True)

        button_frame = ttk.Frame(border)
        button_frame.pack(padx=5, pady=5, fill="both", expand=True)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.rowconfigure(0, weight=1)
        button_frame.rowconfigure(1, weight=1)

        append_yaml = ttk.Button(button_frame, text="Append YAML File", style='Accent.TButton', command=self.append_yaml_file)
        append_yaml.grid(padx=5, pady=5, column=0, row=0, sticky="nsew")
        self.localizable_widgets['append_yaml'] = append_yaml
        self.create_tooltip(append_yaml, 'tp_append_yaml', 'Appends OpenUtau YAML dictionaries')

        append_cmu = ttk.Button(button_frame, text="Append CMUdict File", style='Accent.TButton', command=self.append_cmudict_file)
        append_cmu.grid(padx=5, pady=5, column=0, row=1, sticky="nsew")
        self.localizable_widgets['append_cmu'] = append_cmu
        self.create_tooltip(append_cmu, 'tp_append_vmu', 'Appends CMUdict text file')

        append_json = ttk.Button(button_frame, text="Append Synthv JSON File", style='Accent.TButton', command=self.append_json_file)
        append_json.grid(padx=5, pady=5, column=0, row=2, sticky="nsew")
        self.localizable_widgets['append_json'] = append_json
        self.create_tooltip(append_json, 'tp_append_json', 'Appends Synthv JSON Dictionaries')

        append_csv= ttk.Button(button_frame, text="Append CSV File", style='Accent.TButton', command=self.append_csv_tsv)
        append_csv.grid(padx=5, pady=5, column=0, row=3, sticky="nsew")
        self.localizable_widgets['append_csv'] = append_csv
        self.create_tooltip(append_csv, 'tp_append_csv', 'Appends CSV (Comma Separated Value) Files')

        append_tsv= ttk.Button(button_frame, text="Append TSV File", style='Accent.TButton', command=self.append_csv_tsv)
        append_tsv.grid(padx=5, pady=5, column=0, row=4, sticky="nsew")
        self.localizable_widgets['append_tsv'] = append_tsv
        self.create_tooltip(append_tsv, 'tp_append_tsv', 'Appends TSV (Tab Separated Value) Files')

        # Close the menu window when it loses focus
        self.append_window.focus_set()
        self.append_window.bind("<FocusOut>", lambda e: self.append_window.destroy())
        
        if self.append_window.winfo_exists():
            self.apply_localization()
    
    def import_gen_yaml_temp_data(self):
        localization, filepath, symbols = generate_yaml_template_from_reclist()
        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, self.process_reclist_data, localization, filepath, symbols)
    def process_reclist_data(self, localization, filepath, symbols):
        if symbols:
            self.open_symbol_editor()
            # Clear the Treeview before updating
            self.symbol_treeview.delete(*self.symbol_treeview.get_children())

            # Insert the symbols into the Treeview
            for symbol, symbol_type in symbols.items():
                self.add_symbols_treeview(word=symbol, value=[symbol_type])
                self.loading_window.destroy()
        if localization:
            self.localization.update(localization)

    def update_g2p_selection(self):
        # Updates the G2P model selection dropdown with built-in and external models
        built_in_models = [
            'Arpabet-Plus G2p', 'French G2p', 'German G2p', 'Italian G2p', 
            'Japanese Monophone G2p', 'Millefeuille (French) G2p', 'Portuguese G2p', 
            'Russian G2p', 'Spanish G2p', 'Russian HHSKT G2p'
        ]

        # Load external models using model names from config
        g2p_manager = G2pModelManager()
        external_models = sorted(g2p_manager.models.keys())  # Sort for better readability

        # Create dropdown values with a divider
        if external_models:
            dropdown_values = built_in_models + ["── External Models ──"] + external_models
        else:
            dropdown_values = built_in_models

        # Update Combobox values
        self.g2p_selection['values'] = tuple(dropdown_values)

        # Keep the previously selected model if valid, otherwise default to the first option
        last_selected = self.g2p_selection.get()
        if last_selected in dropdown_values:
            self.g2p_selection.set(last_selected)
        else:
            self.g2p_selection.set(built_in_models[0])

        print("🔄 G2P Model List Updated:", dropdown_values)

    def load_last_g2p(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        try:
            self.selected_g2p = config.get('Settings', 'g2p', fallback='Arpabet-Plus G2p').strip()
        except (configparser.NoSectionError, configparser.NoOptionError):
            messagebox.showinfo("Notice", f"{self.localization.get('g2p_m_err', 'No G2P Model Found')}")
            self.selected_g2p = 'Arpabet-Plus G2p'
        self.g2p_selection.set(self.selected_g2p)

    def on_entry_change(self, event):
        if self.g2p_checkbox_var.get() and self.word_entry.get().strip():
            self.transform_text()
        elif self.g2p_checkbox_var.get() and not self.word_entry.get().strip():
            self.phoneme_entry.delete(0, tk.END)  # Clear phoneme entry if word_entry is empty

    def on_checkbox_change(self, *args):
        if self.g2p_checkbox_var.get() and not self.g2p_selection.get():
            self.g2p_selection.current(0)  # Set default selection if combobox is empty
        self.update_g2p_model()

        if self.g2p_checkbox_var.get():
            if self.word_entry.get().strip():
                self.transform_text()
            else:
                self.phoneme_entry.delete(0, tk.END)  # Clear phoneme entry if word_entry is empty

    def transform_text(self):
        input_text = self.word_entry.get()
        transformed_text = self.g2p_model.predict(input_text)
        self.phoneme_entry.delete(0, tk.END)
        self.phoneme_entry.insert(0, transformed_text)
        
    def update_g2p_model(self, event=None):
        selected_value = self.g2p_selection.get()
        # Dictionary of built-in G2P models (predefined in Assets.G2p)
        g2p_models = {
            'Arpabet-Plus G2p': ('Assets.G2p.arpabet_plus', 'ArpabetPlusG2p'),
            'French G2p': ('Assets.G2p.frenchG2p', 'FrenchG2p'),
            'German G2p': ('Assets.G2p.germanG2p', 'GermanG2p'),
            'Italian G2p': ('', 'ItalianG2p'),
            'Japanese Monophone G2p': ('Assets.G2p.jp_mono', 'JapaneseMonophoneG2p'),
            'Millefeuille (French) G2p': ('Assets.G2p.millefeuilleG2p', 'MillefeuilleG2p'),
            'Portuguese G2p': ('Assets.G2p.portugueseG2p', 'PortugueseG2p'),
            'Russian G2p': ('Assets.G2p.russianG2p', 'RussianG2p'),
            'Russian HHSKT G2p': ('Assets.G2p.russian_hhsktG2p', 'Russian_hhsktG2p'),
            'Spanish G2p': ('Assets.G2p.spanishG2p', 'SpanishG2p'),
        }

        if self.g2p_checkbox_var.get():  # If G2P is enabled
            module_name, class_name = g2p_models.get(selected_value, (None, None))

            # Check if it's a built-in G2P model
            if module_name and class_name:
                try:
                    module = __import__(module_name, fromlist=[class_name])
                    self.g2p_model = getattr(module, class_name)()
                    print(f"✅ G2P model {selected_value} loaded successfully.")
                    self.save_g2p(selected_value)
                    self.transform_text()
                    return
                except Exception as e:
                    print(f"❌ Failed to load G2P model {selected_value}: {e}")

            # Try loading external G2P models from `G2Ps/`
            external_model = self.g2p_manager.get_model(selected_value)

            if external_model:
                self.g2p_model = external_model
                print(f"✅ External G2P model {selected_value} loaded successfully.")
                self.save_g2p(selected_value)
                self.transform_text()
            else:
                print(f"❌ No G2P model found for {selected_value}. Using default settings.")
        else:
            self.g2p_model = None
            print("🔕 G2P is disabled.")
            self.save_g2p(selected_value)
    
    def load_g2p_checkbox_state(self):
        # Load G2P checkbox state from config
        config = configparser.ConfigParser()
        config.read(self.config_file)
        try:
            g2p_enabled = config.getboolean('Settings', 'G2P_Enabled')
            self.g2p_checkbox_var.set(g2p_enabled)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.g2p_checkbox_var.set(True)
            print("G2P checkbox state not found in config. Using default.")

    def save_g2p(self, selected_value):
        # Save the selected G2P model to settings.ini
        config = configparser.ConfigParser()
        config.read(self.config_file)
        if 'Settings' not in config.sections():
            config['Settings'] = {}
        config['Settings']['G2P'] = selected_value
        config['Settings']['G2P_Enabled'] = str(self.g2p_checkbox_var.get())
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)
        print(f"G2P model {selected_value} saved to config file.")
            
    def is_connected(self):
        # Check internet connection by trying to reach Google lmao
        try:
            requests.get("http://www.google.com", timeout=3)
            return True
        except requests.RequestException:
            return False
    
    #Define a callback function
    def callback(self, url):
        webbrowser.open_new_tab(url)
    
    def whats_new(self):
        self.update_window = tk.Toplevel(self)
        self.icon(self.update_window)
        self.update_window.title("What's New")
        self.update_window.geometry("600x500")
        
        # Center the window
        self.update_window.update_idletasks()
        width = self.update_window.winfo_width()
        height = self.update_window.winfo_height()
        x = (self.update_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.update_window.winfo_screenheight() // 2) - (height // 2) - 30
        self.update_window.geometry(f'{width}x{height}+{x}+{y}')

        container = ttk.Frame(self.update_window)
        container.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Load and convert the markdown file
        with open("Readme.md", "r") as file:
            readme_content = file.read()
        html_content = markdown2.markdown(readme_content, extras=["fenced-code-blocks", "tables", "code-friendly", "footnotes", "toc", "cuddled-lists", "metadata"])

        # HTMLLabel to display the HTML content
        html_label = HTMLLabel(container, html=html_content)
        html_label.pack(fill=tk.BOTH, expand=True)

        # Add buttons below the scrollable content
        button_frame = ttk.Frame(container)
        button_frame.pack(pady=(10,0), fill=tk.X)

        btn_close = ttk.Button(button_frame, text="Close", command=self.on_closing_whats_new)
        btn_close.pack(side=tk.RIGHT, padx=5)
        self.localizable_widgets['close'] = btn_close

        btn_see = ttk.Button(button_frame, text="See Release on Github", style='Accent.TButton',
            command=lambda: self.callback("https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/releases/latest"))
        btn_see.pack(side=tk.RIGHT, padx=5)
        self.localizable_widgets['btn_git'] = btn_see
        self.create_tooltip(btn_see, 'tp_btn_see', 'Directs to the Github Repository for more information')

        # Add a checkbox to not show the "What's New" window next time
        self.show_whats_new_var = tk.BooleanVar(value=False)
        chk_show_whats_new = ttk.Checkbutton(button_frame, text="Do not show this again", variable=self.show_whats_new_var)
        chk_show_whats_new.pack(side=tk.LEFT, pady=10, anchor='w')
        self.localizable_widgets['whats_new_cb'] = chk_show_whats_new
        self.create_tooltip(chk_show_whats_new, 'tp_chk_show_whats_new', 'Do not show this window on startup (Checkbox resets once you open again this window)')

        self.update_window.protocol("WM_DELETE_WINDOW", self.on_closing_whats_new)
        if self.update_window.winfo_exists():
            self.apply_localization()

    def on_closing_whats_new(self):
        # Save the state when closing the "What's New" window
        self.save_whats_new_state(self.show_whats_new_var.get())
        self.update_window.destroy()
    
    def load_whats_new_state(self):
        # Load "What's New" state from config
        config = configparser.ConfigParser()
        config.read(self.config_file)
        try:
            self.whats_new_opened = config.getboolean('Settings', 'Whats_new')
            self.previous_version = config.get('Settings', 'App_Version', fallback=self.current_version)
        except (configparser.NoSectionError, configparser.NoOptionError):
            self.whats_new_opened = False  # Default to False if not found
            self.previous_version = '0.0.0'  # Default to an old version if not found

    def save_whats_new_state(self, state):
        # Save the "What's New" state to config
        config = configparser.ConfigParser()
        config.read(self.config_file)
        if 'Settings' not in config.sections():
            config['Settings'] = {}
        config['Settings']['Whats_new'] = str(state)
        config['Settings']['App_Version'] = self.current_version
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)
        print(f"'What's New' state {state} and version {self.current_version} saved to config file.")
    
    def update_localization_files(self):
        if not self.is_connected():
            return

        try:
            api_url = "https://api.github.com/repos/Cadlaxa/OpenUtau-Dictionary-Editor/contents/OU%20Dictionary%20Editor/Templates/Localizations"
            response = requests.get(api_url)
            response.raise_for_status()
            files = response.json()

            updated = False
            local_dir = os.path.join("Templates", "Localizations")
            os.makedirs(local_dir, exist_ok=True)

            for file_info in files:
                file_name = file_info['name']
                download_url = file_info['download_url']
                remote_sha = file_info['sha']
                local_file_path = os.path.join(local_dir, file_name)
                sha_file_path = local_file_path + ".sha"

                local_sha = None
                if os.path.exists(local_file_path) and os.path.exists(sha_file_path):
                    with open(sha_file_path, 'r', encoding='utf-8') as f:
                        local_sha = f.read().strip()

                if local_sha != remote_sha:
                    file_response = requests.get(download_url)
                    file_response.raise_for_status()
                    with open(local_file_path, 'wb') as local_file:
                        local_file.write(file_response.content)
                    with open(sha_file_path, 'w', encoding='utf-8') as sha_file:
                        sha_file.write(remote_sha)
                    updated = True

            if updated:
                messagebox.showinfo("Localization Updated", self.localization.get(
                    'localization_updated', 'Localization files have been updated successfully.'))

        except requests.RequestException as e:
            messagebox.showerror("Localization Error", self.localization.get(
                'localization_err', 'Failed to update localization files: ') + str(e))

    def check_and_update_version(self):
        # Check if the app version is updated and update the config
        self.is_new_version = self.current_version != self.previous_version
        if self.is_new_version:
            self.save_whats_new_state(self.whats_new_opened)
    
    def check_for_updates(self):
        if not self.is_connected():
            messagebox.showerror("Internet Error", f"{self.localization.get('no_internet', 'No internet connection. Please check your connection and try again.')}")
            return
        try:
            self.response = requests.get("https://api.github.com/repos/Cadlaxa/OpenUtau-Dictionary-Editor/releases/latest", timeout=5)
            self.response.raise_for_status()
            self.latest_release = self.response.json()
            self.latest_version_tag = self.latest_release['tag_name']
            self.latest_asset = self.latest_release['assets'][0]  # first asset is the zip file
            if self.latest_version_tag > self.current_version:
                if messagebox.askyesno("Update Available", f"Version {self.latest_version_tag} {self.localization.get('update_avail', 'is available. Do you want to update now?')}"):
                    self.download_and_install_update(self.latest_asset['browser_download_url'])
            else:
                messagebox.showinfo("No Updates", f"{self.localization.get('up_to_date', 'You are up to date!')}")
        except requests.RequestException as e:
            messagebox.showerror("Update Error", f"{self.localization.get('update_err_check', 'Could not check for updates: ')} {str(e)}")
    
    def get_remote_file_size(self, url):
        try:
            r = self.session.head(url, allow_redirects=True)
            return int(r.headers.get('content-length', 0))
        except requests.RequestException:
            return 0

    def dl_window(self, parent, max_value):
        return DownloadProgressDialog(parent, max_value)
    
    def download_and_install_update(self, download_url):
        downloads_path = P("./Downloads")
        if not downloads_path.exists():
            downloads_path.mkdir(parents=True, exist_ok=True)

        local_zip_path = downloads_path / f"OU Dict Editor {self.latest_version_tag}.zip"
        temp_extraction_path = downloads_path / "temp_extract"

        try:
            # Initialize progress dialog
            total_size = self.get_remote_file_size(download_url)
            progress_dialog = self.dl_window(self, total_size)
            
            # Download the file
            with self.session.get(download_url, stream=True) as r:
                r.raise_for_status()
                downloaded_size = 0
                with open(local_zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024 * 6): # 6MB chunk size
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            progress_dialog.set_progress(downloaded_size)

            # Close progress dialog
            progress_dialog.close()

            # Extract ZIP file
            with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extraction_path)

            # Move contents to target folder
            first_directory = next(os.walk(temp_extraction_path))[1][0]
            source_path = temp_extraction_path / first_directory
            target_path = downloads_path / "OU DICTIONARY EDITOR"

            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)

            for item in os.listdir(source_path):
                s = source_path / item
                d = target_path / item
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            # Clean up temporary files
            os.remove(local_zip_path)
            shutil.rmtree(temp_extraction_path)
            
            # Offer to open the directory
            if messagebox.showinfo("Application Close", f"{self.localization.get('app_close', 'The application will now close. Please move the downloaded file manually.')}"):
                if os.name == 'nt':
                    os.startfile(target_path)
                    self.destroy()
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.Popen([opener, str(target_path)])
                    self.destroy()

        except requests.RequestException as e:
            messagebox.showerror("Download Error", f"{self.localization.get('dl_cannot', 'Could not download the update: ')} {str(e)}")
        except zipfile.BadZipFile:
            messagebox.showerror("Unzip Error", f"{self.localization.get('zip_extr', 'The downloaded file was not a valid zip file.')}")
        except Exception as e:
            messagebox.showerror("Update Error", f"{self.localization.get('update_process_err', 'An error occurred during the update process: ')} {str(e)}")

    def init_localization(self):
        # Read the last used localization file path
        last_used_file = self.read_last_selected_localization()
        if last_used_file:
            # Load the localization from the file
            self.load_localization(last_used_file)
            # Apply the loaded localization data
            self.apply_localization()

    def update_localization_combobox(self, combobox):
        yaml = YAML()
        template_dir = self.read_template_directory()
        localization_dir = os.path.join(template_dir, 'Localizations') if template_dir else None
        self.current_local = self.local_var.get()

        if localization_dir and os.path.isdir(localization_dir):
            # List all YAML files in the localization directory
            yaml_files = [file for file in os.listdir(localization_dir) if file.endswith('.yaml')]
            language_dict = {}
            for yaml_file in yaml_files:
                file_path = os.path.join(localization_dir, yaml_file)
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = yaml.load(file)
                    # Assuming that each YAML file contains 'Language' and 'File' keys
                    if 'Language' in data and 'File' in data:
                        language_dict[data['Language']] = data['File']
                    else:
                        language_dict[yaml_file.replace('.yaml', '')] = yaml_file
            if language_dict:
                sorted_languages = sorted(language_dict.keys())
                # Setting ComboBox values to the sorted list of languages
                combobox['values'] = sorted_languages
                if self.current_local in language_dict:
                    combobox.set(self.current_local)
                else:
                    combobox.set(sorted_languages[0])
                self.language_file_map = language_dict
            else:
                messagebox.showinfo("No Localizations Found", f"{self.localization.get('localization_subfolder', 'No valid YAML files found in (Localizations) subfolder.')}")
        else:
            messagebox.showinfo("No Localizations Found", f"{self.localization.get('loc_folder_err', 'No (Localizations) subfolder found or it is empty.')}")

    def load_localization(self, file_path):
        template_dir = self.read_template_directory()
        localization_dir = os.path.join(LOCAL) if template_dir else None
        yaml = YAML(typ='safe')
        if localization_dir and os.path.isdir(localization_dir):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = yaml.load(file) 
                self.localization = data 
            except Exception as e:
                messagebox.showerror("Localization Error", f"{self.localization.get('loc_load_err', 'Failed to load localization file: ')} {str(e)}")
                self.localization = {}
        else:
            messagebox.showinfo("No Localizations Found", f"{self.localization.get('load_loc_err', 'No (Localizations) subfolder found or it is empty.')}")
            self.localization = {}

    def localization_selected(self, event):
        selected_language = self.localization_var.get()

        # Check if the language is in the dictionary mapping languages to filenames
        if selected_language in self.language_file_map:
            selected_file = self.language_file_map[selected_language]
            template_dir = self.read_template_directory()
            localization_file_path = os.path.join(template_dir, 'Localizations', selected_file)
            
            # Load and apply the localization
            self.load_localization(localization_file_path)
            self.apply_localization()
            
            # Save the human-readable language name and the full path to the config
            self.save_localization_file_to_config(localization_file_path, selected_language)
        else:
            messagebox.showinfo("Localization Error", f"{self.localization.get('loc_s_config', 'Selected language configuration not found.')}")

    def save_localization_file_to_config(self, get_local, selected_local):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        if 'Settings' not in config.sections():
            config['Settings'] = {}
        config['Settings']['localization'] = get_local
        config['Settings']['current_local'] = selected_local
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

    def read_last_selected_localization(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        try:
            # This should retrieve the full path to the last selected localization file
            return config.get('Settings', 'localization')
        except (configparser.NoSectionError, configparser.NoOptionError):
            return None

    def apply_localization(self):
        if not hasattr(self, 'en_US.yaml'):
            # Load default localization if not already loaded
            yaml = YAML()
            with open('./Templates/Localizations/en_US.yaml', 'r', encoding='utf-8') as file:
                self.default_localization = yaml.load(file)

        if self.localizable_widgets:
            for key, widget in self.localizable_widgets.items():
                text = self.localization.get(key, self.default_localization.get(key))
                if widget.winfo_exists():
                    if isinstance(widget, ttk.LabelFrame):
                        widget.config(text=text)
                    elif isinstance(widget, (ttk.Label, ttk.Button, ttk.Checkbutton)):
                        widget.config(text=text)
                    elif isinstance(widget, ttk.Notebook):
                        for index in range(widget.index("end")):
                            tab_text_key = f'tab_text_{index}'
                            tab_text = self.localization.get(tab_text_key, self.default_localization.get(tab_text_key))
                            widget.tab(index, text=tab_text)
                    elif isinstance(widget, ttk.Frame):
                        pass
                    else:
                        print(f"Widget type not handled for localization: {type(widget)}")
        else:
            print("No localizable widgets defined.")
        self.styling()
    
class Event:
    def __init__(self, data):
        self.data = data

def process_files(file_paths):
    app = Dictionary()
    app.update()
    # Process each file path individually
    for path in file_paths:
        # Ensure the path is correctly formatted
        path = os.path.normpath(path)
        print(f"Processing file: {path}")
        # Create the event with the path
        simulated_event = Event(path)
        app.on_drop(simulated_event)

    app.mainloop()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        try:
            # Prepare file paths
            file_paths = [arg for arg in sys.argv[1:]]
            process_files(file_paths)
        except Exception as e:
            print(f"Error processing files: {str(e)}")
    else:
        app = Dictionary()
        app.mainloop()