import tkinter as tk
from Assets.modules.sv_ttk import sv_ttk
from tkinter import filedialog, messagebox, ttk, Toplevel, BOTH, scrolledtext
import os, sys, re
sys.path.append('.')
from pathlib import Path as P
from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.compat import StringIO
import tkinter.font as tkFont
import configparser
from Assets.modules import requests
import zipfile
from zipfile import ZipFile
import shutil, threading, subprocess, copy, platform, gzip, pyglet, pyperclip, io, csv
import ctypes as ct
import json, pickle, darkdetect, webbrowser, markdown2, glob, chardet
from tkhtmlview import HTMLLabel
from collections import defaultdict, OrderedDict
import onnxruntime as ort
import numpy as np
from tkinterdnd2 import TkinterDnD, DND_FILES

# Plugins
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
        
        config = configparser.ConfigParser()
        config.read('settings.ini')
        selected_theme = config.get('Settings', 'theme', fallback='Dark')
        selected_accent = config.get('Settings', 'accent', fallback='Mint')
        self.theme_var = tk.StringVar(value=selected_theme)
        self.accent_var = tk.StringVar(value=selected_accent)
        selected_local = config.get('Settings', 'localization', fallback='English')
        self.localization_var = tk.StringVar(value=selected_local)
        self.current_local = config.get('Settings', 'current_local', fallback='English')
        self.local_var = tk.StringVar(value=self.current_local)
        self.selected_g2p = config.get('Settings', 'g2p', fallback="Arpabet-Plus G2p")
        self.g2p_var = tk.StringVar(value=self.selected_g2p)
        self.current_version = "v1.4.2"

        # Set window title
        self.base_title = "OpenUTAU Dictionary Editor"
        self.title(self.base_title)
        self.current_filename = None
        self.file_modified = False
        self.localizable_widgets = {}
        self.current_entry_widgets = {}
        self.session = requests.Session()
        
        # Template folder directory
        sv_ttk.set_theme("dark")
        self.Templates = self.read_template_directory()
        self.config_file = "settings.ini"
        self.load_last_theme()

        # Dictionary to hold the data
        self.dictionary = {}
        self.comments = {}
        self.localization = {}
        self.symbols = {}
        self.symbols_list = []
        self.undo_stack = []
        self.redo_stack = []
        self.copy_stack = []
        self.plugin_file = None
        self.phoneme_map = {}
        self.systems = []

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
        self.current_order = [] # To store the manual order of entries
        self.styling()
        self.create_widgets()
        self.init_localization()
        t = threading.Thread(target=darkdetect.listener, args=(self.toggle_theme,))
        t.daemon = True
        t.start()

        self.icon()
        # Start update check in a non-blocking way
        threading.Thread(target=self.bg_updates, daemon=True).start()

        self.load_whats_new_state()
        self.check_and_update_version()
        # Check if "What's New" should be displayed
        if not self.whats_new_opened or self.is_new_version:
            self.whats_new()
    
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
    
    # Directory for the YAML Templates via settings.ini
    def read_template_directory(self, config_file="settings.ini"):
        config = configparser.ConfigParser()
        # Check if the config file exists
        if os.path.exists(config_file):
            config.read(config_file)
            try:
                return config.get('Paths', 'template_location')
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass
        # Save the directory
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
    
    def toggle_theme(self, event=None):
        # Read the current theme selection from the combobox
        theme_name = self.theme_var.get()
        accent_name = self.accent_var.get()
        theme_map = {
            ("Electric Blue", "Dark"): "sun-valley-dark",
            ("Electric Blue", "Light"): "sun-valley-light",
            ("Amaranth", "Light"): "amaranth_light",
            ("Amaranth", "Dark"): "amaranth_dark",
            ("Amethyst", "Light"): "amethyst_light",
            ("Amethyst", "Dark"): "amethyst_dark",
            ("Burnt Sienna", "Light"): "burnt-sienna_light",
            ("Burnt Sienna", "Dark"): "burnt-sienna_dark",
            ("Dandelion", "Light"): "dandelion_light",
            ("Dandelion", "Dark"): "dandelion_dark",
            ("Denim", "Light"): "denim_light",
            ("Denim", "Dark"): "denim_dark",
            ("Fern", "Light"): "fern_light",
            ("Fern", "Dark"): "fern_dark",
            ("Lemon Ginger", "Light"): "lemon-ginger_light",
            ("Lemon Ginger", "Dark"): "lemon-ginger_dark",
            ("Lightning Yellow", "Light"): "lightning-yellow_light",
            ("Lightning Yellow", "Dark"): "lightning-yellow_dark",
            ("Mint", "Light"): "mint_light",
            ("Mint", "Dark"): "mint_dark",
            ("Orange", "Light"): "orange_light",
            ("Orange", "Dark"): "orange_dark",
            ("Pear", "Light"): "pear_light",
            ("Pear", "Dark"): "pear_dark",
            ("Persian Red", "Light"): "persian-red_light",
            ("Persian Red", "Dark"): "persian-red_dark",
            ("Pink", "Light"): "pink_light",
            ("Pink", "Dark"): "pink_dark",
            ("Salmon", "Light"): "salmon_light",
            ("Salmon", "Dark"): "salmon_dark",
            ("Sapphire", "Light"): "sapphire_light",
            ("Sapphire", "Dark"): "sapphire_dark",
            ("Sea Green", "Light"): "sea-green_light",
            ("Sea Green", "Dark"): "sea-green_dark",
            ("Seance", "Light"): "seance_light",
            ("Seance", "Dark"): "seance_dark",
            ("Sunny Yellow", "Light"): "sunny-yellow_light",
            ("Sunny Yellow", "Dark"): "sunny-yellow_dark",
            ("Moonstone", "Light"): "moonstone_light",
            ("Moonstone", "Dark"): "moonstone_dark",
            ("Dark Red", "Light"): "dark-red_light",
            ("Dark Red", "Dark"): "dark-red_dark",
            ("Beaver", "Light"): "beaver_light",
            ("Beaver", "Dark"): "beaver_dark",
            ("Liver", "Light"): "liver_light",
            ("Liver", "Dark"): "liver_dark",
            ("Yellow Green", "Light"): "yellow-green_light",
            ("Yellow Green", "Dark"): "yellow-green_dark",
            ("Payne's Gray", "Light"): "payne's-gray_light",
            ("Payne's Gray", "Dark"): "payne's-gray_dark",
            ("Hunter Green", "Light"): "hunter-green_light",
            ("Hunter Green", "Dark"): "hunter-green_dark",
            ("Sky Magenta", "Light"): "sky-magenta_light",
            ("Sky Magenta", "Dark"): "sky-magenta_dark",
            ("Light See Green", "Light"): "l-see-green_light",
            ("Light See Green", "Dark"): "l-see-green_dark",
            ("Middle Green Yellow", "Light"): "middle-gy_light",
            ("Middle Green Yellow", "Dark"): "middle-gy_dark"
        }
        # Apply the theme using sv_ttk
        if theme_name == 'System':
            system_theme = darkdetect.theme()
            theme_key = (accent_name, system_theme)
        else:
            theme_key = (accent_name, theme_name)

        if theme_key in theme_map:
            ttk.Style().theme_use(theme_map[theme_key])
            self.widget_style()
            self.save_theme_to_config(accent_name, theme_name)
    
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
            #theme_name = self.theme_var.get()
            accent_name = config.get('Settings', 'accent')
            theme_map = {
                ("Electric Blue", "Dark"): "sun-valley-dark",
                ("Electric Blue", "Light"): "sun-valley-light",
                ("Amaranth", "Light"): "amaranth_light",
                ("Amaranth", "Dark"): "amaranth_dark",
                ("Amethyst", "Light"): "amethyst_light",
                ("Amethyst", "Dark"): "amethyst_dark",
                ("Burnt Sienna", "Light"): "burnt-sienna_light",
                ("Burnt Sienna", "Dark"): "burnt-sienna_dark",
                ("Dandelion", "Light"): "dandelion_light",
                ("Dandelion", "Dark"): "dandelion_dark",
                ("Denim", "Light"): "denim_light",
                ("Denim", "Dark"): "denim_dark",
                ("Fern", "Light"): "fern_light",
                ("Fern", "Dark"): "fern_dark",
                ("Lemon Ginger", "Light"): "lemon-ginger_light",
                ("Lemon Ginger", "Dark"): "lemon-ginger_dark",
                ("Lightning Yellow", "Light"): "lightning-yellow_light",
                ("Lightning Yellow", "Dark"): "lightning-yellow_dark",
                ("Mint", "Light"): "mint_light",
                ("Mint", "Dark"): "mint_dark",
                ("Orange", "Light"): "orange_light",
                ("Orange", "Dark"): "orange_dark",
                ("Pear", "Light"): "pear_light",
                ("Pear", "Dark"): "pear_dark",
                ("Persian Red", "Light"): "persian-red_light",
                ("Persian Red", "Dark"): "persian-red_dark",
                ("Pink", "Light"): "pink_light",
                ("Pink", "Dark"): "pink_dark",
                ("Salmon", "Light"): "salmon_light",
                ("Salmon", "Dark"): "salmon_dark",
                ("Sapphire", "Light"): "sapphire_light",
                ("Sapphire", "Dark"): "sapphire_dark",
                ("Sea Green", "Light"): "sea-green_light",
                ("Sea Green", "Dark"): "sea-green_dark",
                ("Seance", "Light"): "seance_light",
                ("Seance", "Dark"): "seance_dark",
                ("Sunny Yellow", "Light"): "sunny-yellow_light",
                ("Sunny Yellow", "Dark"): "sunny-yellow_dark",
                ("Moonstone", "Light"): "moonstone_light",
                ("Moonstone", "Dark"): "moonstone_dark",
                ("Dark Red", "Light"): "dark-red_light",
                ("Dark Red", "Dark"): "dark-red_dark",
                ("Beaver", "Light"): "beaver_light",
                ("Beaver", "Dark"): "beaver_dark",
                ("Liver", "Light"): "liver_light",
                ("Liver", "Dark"): "liver_dark",
                ("Yellow Green", "Light"): "yellow-green_light",
                ("Yellow Green", "Dark"): "yellow-green_dark",
                ("Payne's Gray", "Light"): "payne's-gray_light",
                ("Payne's Gray", "Dark"): "payne's-gray_dark",
                ("Hunter Green", "Light"): "hunter-green_light",
                ("Hunter Green", "Dark"): "hunter-green_dark",
                ("Sky Magenta", "Light"): "sky-magenta_light",
                ("Sky Magenta", "Dark"): "sky-magenta_dark",
                ("Light See Green", "Light"): "l-see-green_light",
                ("Light See Green", "Dark"): "l-see-green_dark",
                ("Middle Green Yellow", "Light"): "middle-green-yellow_light",
                ("Middle Green Yellow", "Dark"): "middle-green-yellow_dark"
            }
            # Apply the theme using sv_ttk
            if theme_name == 'System':
                system_theme = darkdetect.theme()
                theme_key = (accent_name, system_theme)
            else:
                theme_key = (accent_name, theme_name)
            if theme_key in theme_map:
                ttk.Style().theme_use(theme_map[theme_key])
        except (configparser.NoSectionError, configparser.NoOptionError):
            sv_ttk.set_theme("dark")
            ttk.Style().theme_use("mint_dark")
        
    def load_cmudict(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not filepath:
            messagebox.showinfo("No File", f"{self.localization.get('cmudict_nofile', 'No file was selected.')}")
            return
        
        self.load_window()
        self.loading_window.update_idletasks()
        self.after(100, self.load_process_cmudict_file, filepath)
    def load_process_cmudict_file(self, filepath):
        if filepath:
            self.current_filename = filepath
            self.file_modified = False  # Reset modification status
            self.update_title()
            self.current_order = list(self.dictionary.keys())

        # Ensure Cache directory exists
        cache_dir = CACHE
        os.makedirs(cache_dir, exist_ok=True)

        # Create a unique cache file path
        cache_filename = (filepath).replace('/', '-').replace(':', '').replace('\\', '-') + '.y\'all'
        cache_filepath = os.path.join(cache_dir, cache_filename)

        # Check if the cache file exists and is up-to-date
        if os.path.exists(cache_filepath) and os.path.getmtime(cache_filepath) >= os.path.getmtime(filepath):
            try:
                with gzip.open(cache_filepath, 'rb') as cache_file:
                    self.dictionary, self.comments = pickle.load(cache_file)
                    self.update_entries_window()
                    self.loading_window.destroy()
                    return
            except Exception as e:
                messagebox.showerror("Error", f"{self.localization.get('cmudict_err_read', 'Error occurred while reading from cache: ')} {e}")

        # Load from original file if cache is not available or outdated
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            try:
                with open(filepath, 'r', encoding='ANSI') as file:
                    lines = file.readlines()
            except Exception as e:
                self.loading_window.destroy()
                messagebox.showerror("Error", f"{self.localization.get('cmudict_err_enc', 'Error occurred while reading file with alternate encoding: ')} {e}")
                return
        except Exception as e:
            self.loading_window.destroy()
            messagebox.showerror("Error", f"{self.localization.get('cmudict_err_1', 'Error occurred while reading file: ')} {e}")
            return

        dictionary = {}
        comments = []  # Store comments here if needed
        error_occurred = False
        for line_number, line in enumerate(lines, start=1):
            try:
                if line.strip().startswith(';;;'):
                    comments.append(line.strip()[3:])
                    continue

                parts = line.strip().split('  ')  # Two spaces separate the key and values
                if len(parts) == 2:
                    grapheme, phonemes = parts[0], parts[1].split()
                    dictionary[grapheme] = phonemes
                else:
                    self.loading_window.destroy()
                    raise ValueError(f"{self.localization.get('cmudict_invL', 'Invalid format in line:')} {line.strip()}")
            except Exception as e:
                self.loading_window.destroy()
                messagebox.showerror("Error", f"{self.localization.get('load_cmudict_procc', 'Error occurred while processing line')} {line_number}: '{line.strip()}'\n{str(e)}")
                error_occurred = True
                break

        if not error_occurred:
            self.dictionary = dictionary  # Update the main dictionary only if no errors occurred
            self.comments = comments
            self.update_entries_window()

            # Save to cache (regardless of whether it was updated from the file or not)
            try:
                with gzip.open(cache_filepath, 'wb') as cache_file:
                    pickle.dump((self.dictionary, self.comments), cache_file)
            except Exception as e:
                messagebox.showerror("Error", f"{self.localization.get('cmudict_cache_err', 'Error occurred while saving to cache: ')} {e}")

        self.loading_window.destroy()

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
        self.current_filename = filepath
        self.file_modified = False
        self.update_title()
        self.current_order = list(self.dictionary.keys())

        # Load JSON data
        try:
            cache_dir = CACHE
            os.makedirs(cache_dir, exist_ok=True)
            
            # Create a unique cache file path
            cache_filename = (filepath).replace('/', '-').replace(':', '').replace('\\', '-') + '.y\'all'
            cache_filepath = os.path.join(cache_dir, cache_filename)

            # Check if the cache file exists and is up-to-date
            if os.path.exists(cache_filepath) and os.path.getmtime(cache_filepath) >= os.path.getmtime(filepath):
                try:
                    with gzip.open(cache_filepath, 'rb') as cache_file:
                        entries = pickle.load(cache_file)
                except Exception as e:
                    self.loading_window.destroy()
                    messagebox.showerror("Error", f"{self.localization.get('json_cache_err', 'Error occurred while reading from cache: ')} {e}")
                    return
            else:
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    entries = data.get('data', [])
                    if not entries:
                        self.loading_window.destroy()
                        messagebox.showinfo("Empty Data", f"{self.localization.get('json_empty', 'The JSON file contains no data.')}")
                        return
                # Save to cache
                try:
                    with gzip.open(cache_filepath, 'wb') as cache_file:
                        pickle.dump(entries, cache_file)
                except Exception as e:
                    self.loading_window.destroy()
                    messagebox.showerror("Error", f"{self.localization.get('json_save_cache', 'Error occurred while saving to cache: ')} {e}")

            # Process entries
            self.dictionary.clear()
            for item in entries:
                grapheme = item.get('w')
                phonemes = item.get('p')
                if not (isinstance(grapheme, str) and isinstance(phonemes, str)):
                    messagebox.showerror("Invalid Entry", f"{self.localization.get('json_inv_entry', 'Each entry must have a (w) key with a string value and a (p) key with a string value.')}")
                    continue
                phoneme_list = [phoneme.strip() for phoneme in phonemes.split()]
                self.dictionary[grapheme] = phoneme_list

            self.update_entries_window()
        except json.JSONDecodeError as je:
            messagebox.showerror("JSON Syntax Error", f"{self.localization.get('json_parse_file', 'An error occurred while parsing the JSON file: ')} {str(je)}")
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('json_read_ex', 'An error occurred while reading the JSON file: ')} {str(e)}")
        finally:
            self.loading_window.destroy()

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
        try:
            # Handle file opening to update title
            self.current_filename = filepath
            self.file_modified = False
            self.update_title()
            self.current_order = list(self.dictionary.keys())
            cache_dir = CACHE
            os.makedirs(cache_dir, exist_ok=True)

            # Create a unique cache file path
            cache_filename = filepath.replace('/', '-').replace(':', '').replace('\\', '-') + '.y\'all'
            cache_filepath = os.path.join(cache_dir, cache_filename)

            # Check if the cache file exists and is up-to-date
            if os.path.exists(cache_filepath) and os.path.getmtime(cache_filepath) >= os.path.getmtime(filepath):
                try:
                    with gzip.open(cache_filepath, 'rb') as cache_file:
                        data = pickle.load(cache_file)
                except Exception as e:
                    self.loading_window.destroy()
                    raise ValueError(f"{self.localization.get('yaml_cache_rv', 'Error occurred while reading from cache:')} {e}")
            else:
                yaml = YAML(typ='safe')
                yaml.prefix_colon = True
                yaml.preserve_quotes = True
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = yaml.load(file)
                    if data is None:
                        self.loading_window.destroy()
                        raise ValueError({self.localization.get('yaml_inc_format_rv', 'The YAML file is empty or has an incorrect format.')})
                # Save to cache
                try:
                    with gzip.open(cache_filepath, 'wb') as cache_file:
                        pickle.dump(data, cache_file)
                except Exception as e:
                    self.loading_window.destroy()
                    raise ValueError(f"{self.localization.get('yaml_err_save_rv', 'Error occurred while saving to cache:')} {e}")

            # Load entries
            entries = data.get('entries', [])
            if not isinstance(entries, list):
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'grapheme' in item and 'phonemes' in item:
                            entries.append(item)
                elif isinstance(data, dict):
                    if 'grapheme' in data and 'phonemes' in data:
                        entries.append(data)

            self.dictionary = {}
            self.data_list = []  # Initialize data_list
            for item in entries:
                if not isinstance(item, dict):
                    self.loading_window.destroy()
                    raise ValueError({self.localization.get('yaml_dict_fromat_rv', 'Entry format incorrect. Each entry must be a dictionary.')})
                grapheme = item.get('grapheme')
                phonemes = item.get('phonemes', [])
                if grapheme is None or not isinstance(phonemes, list):
                    self.loading_window.destroy()
                    raise ValueError({self.localization.get('yaml_type_rv', 'Each entry must have a (grapheme) key and a list of (phonemes).')})
                self.dictionary[grapheme] = phonemes
                # Append the loaded data to data_list
                self.data_list.append({'grapheme': grapheme, 'phonemes': phonemes})

            # Load symbols if available
            symbols = data.get('symbols', [])
            if isinstance(symbols, list):
                self.symbols = {}
                self.symbols_list = []  # Initialize symbols_list
                
                for item in symbols:
                    if not isinstance(item, dict):
                        self.loading_window.destroy()
                        raise ValueError({self.localization.get('sym_inc_rv', 'Symbol entry format incorrect. Each entry must be a dictionary.')})
                    symbol = item.get('symbol')
                    type_ = item.get('type')
                    rename = item.get('rename')
                    if symbol is None or type_ is None:
                        self.loading_window.destroy()
                        raise ValueError({self.localization.get('sym_ent_inc_rv', 'Symbol entry is incomplete.')})
                    if not isinstance(type_, str):
                        self.loading_window.destroy()
                        raise ValueError({self.localization.get('sym_str_rv', 'Type must be a string representing the category.')})
                    if rename:  # If 'rename' exists, add it to symbols dictionary
                        self.symbols[symbol] = [type_, rename]
                        self.symbols_list.append({'symbol': symbol, 'type': [type_], 'rename': rename})
                    else:  # If 'rename' does not exist, load only the symbol and type
                        self.symbols[symbol] = [type_]
                        self.symbols_list.append({'symbol': symbol, 'type': [type_]})
            
            # Load and process replacements
            replacements = data.get('replacements', [])
            for replacement in replacements:
                from_symbol = replacement.get('from')
                to_symbol = replacement.get('to')
                if from_symbol is None or to_symbol is None:
                    messagebox.showerror("Error", f"{self.localization.get('process_repl_sym_err', 'Each replacement entry must have a (from) and a (to) symbol (string)')}")
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

            # Update symbols_list after processing replacements
            self.symbols_list = [{'symbol': k, 'type': v[0], 'rename': v[1] if len(v) > 1 else ''} for k, v in self.symbols.items()]

            self.update_entries_window()
        except (YAMLError, ValueError) as e:
            self.loading_window.destroy()
            messagebox.showerror("Error", f"{self.localization.get('yaml_load_err', 'An error occurred: ')} {str(e)}")
        except Exception as e:
            self.loading_window.destroy()
            messagebox.showerror("Error", f"{self.localization.get('yaml_unex_err', 'An unexpected error occurred: ')} {str(e)}")
        finally:
            self.loading_window.destroy()

    def merge_yaml_files(self):
        filepaths = filedialog.askopenfilenames(title="Open YAML Files", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
        if not filepaths:
            messagebox.showinfo("No File", f"{self.localization.get('merge_yaml_nofile', 'No files were selected.')}")
            return
        yaml = YAML(typ='safe')
        for filepath in filepaths:
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    self.load_window()
                    data = yaml.load(file)
                    if data is None:
                        self.loading_window.destroy()
                        raise ValueError({self.localization.get('yaml_merge_empt_rv', 'The YAML file is empty or has an incorrect format.')})

                    entries = []
                    if 'entries' in data and isinstance(data['entries'], list):
                        entries = data['entries']
                    else:
                        # Attempt to collect entries assuming various possible data structures
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and 'grapheme' in item and 'phonemes' in item:
                                    entries.append(item)
                        elif isinstance(data, dict) and 'grapheme' in data and 'phonemes' in data:
                            entries.append(data)

                    for item in entries:
                        if not isinstance(item, dict):
                            self.loading_window.destroy()
                            messagebox.showerror(
                                "Error",
                                "Entry format incorrect in file: {}. Each entry must be a dictionary.".format(filepath)
                            )
                            continue

                        grapheme = item.get('grapheme')
                        phonemes = item.get('phonemes', [])
                        if grapheme is None or not isinstance(phonemes, list):
                            self.loading_window.destroy()
                            messagebox.showerror(
                                "Error",
                                "Each entry must have a 'grapheme' key and a list of 'phonemes' in file: {}".format(filepath)
                            )
                            continue

                        # Merge data into the dictionary
                        if grapheme in self.dictionary:
                            # Optionally handle duplicate graphemes (e.g., merge phonemes)
                            self.dictionary[grapheme].extend(x for x in phonemes if x not in self.dictionary[grapheme])
                        else:
                            self.dictionary[grapheme] = phonemes

            except YAMLError as ye:
                self.loading_window.destroy()
                messagebox.showerror("YAML Syntax Error", f"{self.localization.get('merge_yaml_err_parse', 'An error occurred while parsing the YAML file ')} {filepath}: {str(ye)}")
                continue
            except Exception as e:
                self.loading_window.destroy()
                messagebox.showerror("Error", f"{self.localization.get('merge_yaml_read_err', 'An error occurred while reading the YAML file ')} {filepath}: {str(e)}")
                continue
        self.update_entries_window()
        self.loading_window.destroy()
    
    def open_symbol_editor(self):
        if self.symbol_editor_window is None or not self.symbol_editor_window.winfo_exists():
            self.symbol_editor_window = tk.Toplevel(self)
            self.symbol_editor_window.title("Symbols Editor")
            self.symbol_editor_window.protocol("WM_DELETE_WINDOW", self.symbol_editor_window.destroy)
            self.save_state_before_change()
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

            # Create a Frame to hold the Treeview and the Scrollbar
            treeview_frame = tk.Frame(self.symbol_editor_window)
            treeview_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
            treeview_frame.columnconfigure(0, weight=1)
            treeview_frame.rowconfigure(0, weight=1)

            # Create the Treeview
            self.symbol_treeview = ttk.Treeview(treeview_frame, columns=('Symbol', 'Type', 'Rename'), show='headings', height=14)
            self.symbol_treeview.heading('Symbol', text='Symbol')
            self.symbol_treeview.heading('Type', text='Type')
            self.symbol_treeview.heading('Rename', text='Rename')
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
            sym_entry_frame.grid_columnconfigure(1, weight=1)

            action_button_frame1 = ttk.Frame(self.symbol_editor_window)
            action_button_frame1.grid(row=4, column=0, padx=10, pady=(5,15), sticky="nsew")
            action_button_frame1.grid_columnconfigure(0, weight=1)

            delete_button = ttk.Button(action_button_frame, style='TButton', text="Delete", command=self.delete_symbol_entry)
            delete_button.grid(row=1, column=0, padx=5, pady=0, sticky="nsew")
            self.localizable_widgets['del'] = delete_button

            self.word_edit = ttk.Entry(sym_entry_frame)
            self.word_edit.grid(row=0, column=0, padx=5, pady=0, sticky="nsew")
            
            self.phoneme_edit = ttk.Entry(sym_entry_frame)
            self.phoneme_edit.grid(row=0, column=1, padx=5, pady=0, sticky="nsew")

            self.rename_edit = ttk.Entry(sym_entry_frame)
            self.rename_edit.grid(row=0, column=2, padx=5, pady=0, sticky="nsew")

            add_button = ttk.Button(action_button_frame, style='TButton', text="Add", command=self.add_symbol_entry)
            add_button.grid(row=1, column=1, padx=5, pady=0, sticky="nsew")
            self.localizable_widgets['add'] = add_button

            self.word_edit.bind("<Return>", self.add_symbol_entry_event)
            self.phoneme_edit.bind("<Return>", self.add_symbol_entry_event)
            self.rename_edit.bind("<Return>", self.add_symbol_entry_event)

            save_templ = ttk.Button(action_button_frame1, style='Accent.TButton', text="Save to Templates", command=self.save_yaml_template)
            save_templ.grid(row=3, column=0, padx=5, pady=0, sticky="ew")
            self.localizable_widgets['save_templ'] = save_templ

            self.symbol_editor_window.bind("<Escape>", lambda event: self.symbol_editor_window.destroy())

        self.refresh_treeview_symbols()
        if self.symbol_editor_window.winfo_exists():
            self.apply_localization()
    
    def start_drag_sym(self, event):
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

                if not hasattr(self, 'drag_window') or not self.drag_window_sym:
                    self.drag_window_sym = tk.Toplevel(self)
                    self.drag_window_sym.overrideredirect(True)
                    self.drag_window_sym.attributes("-alpha", 0.8)

                    # Create the label with the selected item's text
                    label = ttk.Label(self.drag_window_sym, text=f"{selected_text}", style='Accent.TButton')
                    label.pack(expand=True)

                    self.drag_window_sym.config(borderwidth=1, relief="solid")
                    self.drag_window_sym.wm_attributes("-topmost", True)
                    self.drag_window_sym.wm_attributes("-toolwindow", True)

                self.save_state_before_change()

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
            # Identify the target item
            target_item = self.symbol_treeview.identify_row(event.y)
            if target_item and self.dragged_symbols != target_item:
                # Get the indices of the dragged and target items
                dragged_index = self.symbol_treeview.index(self.dragged_symbols)
                target_index = self.symbol_treeview.index(target_item)
                # Move the dragged item in the Treeview
                self.symbol_treeview.move(self.dragged_symbols, '', target_index)
                # Update the symbols dictionary to reflect the new order
                dragged_data = self.symbol_treeview.item(self.dragged_symbols, 'values')
                dragged_grapheme = dragged_data[0]
                # Remove the dragged entry from its original position in the symbols_list
                dragged_entry = self.symbols.pop(dragged_grapheme, None)
                if dragged_entry is not None:
                    # Convert the symbols dictionary into a list of keys to reorder
                    symbol_keys = list(self.symbols.keys())
                    symbol_keys.insert(target_index, dragged_grapheme)  # Insert at the new index
                    
                    reordered_symbols = {}
                    for key in symbol_keys:
                        if key == dragged_grapheme:
                            reordered_symbols[key] = dragged_entry
                        else:
                            reordered_symbols[key] = self.symbols[key]
                    self.symbols = reordered_symbols  # Update the symbols dictionary

            # Select the dragged item and ensure it's visible
            self.symbol_treeview.selection_set(self.dragged_symbols)
            self.symbol_treeview.see(self.dragged_symbols)

        # Close and clean up the drag window
        if hasattr(self, 'drag_window_sym') and self.drag_window_sym:
            self.drag_window_sym.destroy()
            self.drag_window_sym = None

        # Reset the drag state
        self.drag_initiated_sym = False

    def save_yaml_template(self):
        if not self.symbols and not self.replacements:
            messagebox.showinfo("Warning", f"{self.localization.get('yaml_temp_ns', 'No entries to save. Please add entries before saving.')}")
            return

        # Ensure the templates directory exists
        templates_dir = os.path.join(os.getcwd(), TEMPLATES)
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        # Prompt user for file path using a file dialog with the default directory set to 'templates'
        template_path = filedialog.asksaveasfilename(
            title="Saving symbols to Template YAML",
            initialdir=templates_dir,
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if not template_path:
            return

        # Ensure the file path ends with .yaml
        if not template_path.endswith('.yaml'):
            template_path += '.yaml'
        self.save_window()
        self.saving_window.update_idletasks()
        self.after(100, self.save_template_process, template_path)
    def save_template_process(self, template_path):
        # Read existing data from the template as text, ignoring the entries section
        existing_data_text = []
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if 'symbols:' in line.strip() or 'replacements:' in line.strip():
                        break
                    existing_data_text.append(line)

        # Prepare new entries for symbols without rename
        symbols_entries = []
        for symbol, data in self.symbols.items():
            escaped_symbol = escape_symbols(symbol)
            type_list = data[0] if isinstance(data[0], list) else [data[0]]
            type_str = ', '.join(f"{t}" for t in type_list)
            symbols_entries.append(f"- {{symbol: {escaped_symbol}, type: {type_str}}}\n")

        existing_data_text.append('symbols:\n')
        existing_data_text.extend(symbols_entries)
        existing_data_text.append('\n')

        # Prepare new entries for replacements
        rename_entries = []
        for symbol, data in self.symbols.items():
            if len(data) > 1 and data[1]:  # Check if rename data exists
                from_symbol = escape_symbols(symbol)
                to_data = escape_symbols(data[1])
                rename_entries.append(f"- {{from: {from_symbol}, to: {to_data}}}\n")

        if rename_entries:
            existing_data_text.append('replacements:\n')
            existing_data_text.extend(rename_entries)
            existing_data_text.append('\n')

        existing_data_text.append('entries:\n')

        # Validate the YAML data
        yaml = YAML()
        try:
            yaml.load('\n'.join(existing_data_text))
        except YAMLError as exc:
            self.saving_window.destroy()
            messagebox.showerror("Error", f"{self.localization.get('yaml_template_inv', 'Invalid YAML data: ')} {exc}")
            return

        # Save changes if the user has selected a file path
        with open(template_path, 'w', encoding='utf-8') as file:
            file.writelines(existing_data_text)
            self.update_template_combobox(self.template_combobox)
        self.saving_window.destroy()
        messagebox.showinfo("Success", f"{self.localization.get('templ_saved', 'Templates saved to ')} {template_path}")

    def deselect_symbols(self, event):
        # Check if there is currently a selection
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
        value = self.phoneme_edit.get().strip()
        rname = self.rename_edit.get().strip()
        self.save_state_before_change()
        if symbol and value:
            if not self.symbol_editor_window or not self.symbol_editor_window.winfo_exists():
                self.open_symbol_editor()
            self.add_symbols_treeview(symbol, value.split(), rname)  # Pass rename to the method
            self.phoneme_edit.delete(0, tk.END)
            self.word_edit.delete(0, tk.END)
            self.rename_edit.delete(0, tk.END)
        else:
            messagebox.showinfo("Error", f"{self.localization.get('add_sym_ent', 'Please provide both phonemes and its respective value for the entry.')}")

    def delete_symbol_entry(self):
        selected_items = self.symbol_treeview.selection()
        for item_id in selected_items:
            self.save_state_before_change()
            item_data = self.symbol_treeview.item(item_id, 'values')
            if item_data:
                symbol = item_data[0]
                if symbol in self.symbols:
                    del self.symbols[symbol]  # Delete the entry from the symbols dictionary
                    self.symbol_treeview.delete(item_id)  # Remove the item from the treeview
                    self.phoneme_edit.delete(0, tk.END)
                    self.word_edit.delete(0, tk.END)
                    self.rename_edit.delete(0, tk.END)
                else:
                    messagebox.showinfo("Notice", f"Symbol: {symbol} {self.localization.get('del_sym_nf', ' not found in symbols.')}")
            else:
                messagebox.showinfo("Notice", f"{self.localization.get('del_sym_id', 'No data found for item ID ')} {item_id}.")

    def add_symbols_treeview(self, word=None, value=None, rename=None):
        if word and value is not None:
            # Convert phonemes list to a string for display
            phoneme_display = ', '.join(value)
            new_item_ids = []
            selected_item = self.symbol_treeview.selection()
            item_to_select = None  # Keep track of the item to select

            if word in self.symbols:
                # Update the existing item's phonemes and rename
                self.symbols[word] = [value, rename]
                for item in self.symbol_treeview.get_children():
                    if self.symbol_treeview.item(item, 'values')[0] == word:
                        self.symbol_treeview.item(item, values=(word, phoneme_display, rename))
                        item_to_select = item  # Set the existing item to be selected
                        break
            else:
                if selected_item:
                    insert_index = self.symbol_treeview.index(selected_item[0]) + 1
                else:
                    insert_index = 'end'

                # Insert the new entry
                item_id = self.symbol_treeview.insert('', insert_index, values=(word, phoneme_display, rename), tags=('normal',))
                new_item_ids.append(item_id)
                self.symbols[word] = [value, rename]
                item_to_select = item_id  # Set the newly added item to be selected

            # Update symbols_list to reflect changes
            self.symbols_list = []
            for k, v in self.symbols.items():
                # Ensure each entry has at least two elements
                if len(v) >= 2:
                    self.symbols_list.append({'symbol': k, 'type': v[0], 'rename': v[1]})
                else:
                    # Handle cases where the data might be incomplete
                    self.symbols_list.append({'symbol': k, 'type': v[0], 'rename': ''})

            # Re-index items to maintain order consistency
            for item in self.symbol_treeview.get_children():
                values = self.symbol_treeview.item(item, 'values')
                if len(values) == 3:
                    self.symbol_treeview.item(item, values=(values[0], values[1], values[2]))

            # Select the newly added or updated item
            if item_to_select:
                self.symbol_treeview.selection_set(item_to_select)
                self.symbol_treeview.see(item_to_select)  # Ensure the item is visible

            # Refresh the Treeview to reflect the changes visually
            self.refresh_treeview_symbols()

    def edit_cell_symbols(self, event):
        selected_item = self.symbol_treeview.selection()[0]
        column = self.symbol_treeview.identify_column(event.x)

        # Define the column identifiers
        grapheme_column = "#1"
        phoneme_column = "#2"
        rename_column = "#3"

        # Calculate the positions and sizes of the cells
        x_g, y_g, width_g, height_g = self.symbol_treeview.bbox(selected_item, grapheme_column)
        x_p, y_p, width_p, height_p = self.symbol_treeview.bbox(selected_item, phoneme_column)
        x_r, y_r, width_r, height_r = self.symbol_treeview.bbox(selected_item, rename_column)

        # Retrieve initial values from Treeview, removing commas from phoneme
        item_values = self.symbol_treeview.item(selected_item, "values")
        initial_grapheme = item_values[0]
        initial_phoneme = item_values[1]
        initial_rename = item_values[2] if len(item_values) > 2 else ''

        # Destroy currently open widgets if they exist
        if self.current_entry_widgets:
            for widget in self.current_entry_widgets.values():
                widget.destroy()
            self.current_entry_widgets = {}

        # Create entry widgets for editing grapheme, phoneme, and rename
        self.entry_popup_sym = ttk.Entry(self.symbol_treeview)
        self.entry_popup_sym.place(x=x_g, y=y_g-5, width=width_g, height=height_g+10)
        self.entry_popup_sym.insert(0, initial_grapheme)
        self.entry_popup_sym.focus_set()
        self.current_entry_widgets['entry_popup_sym'] = self.entry_popup_sym

        self.entry_popup_val = ttk.Entry(self.symbol_treeview)
        self.entry_popup_val.place(x=x_p, y=y_p-5, width=width_p, height=height_p+10)
        self.entry_popup_val.insert(0, initial_phoneme)
        self.current_entry_widgets['entry_popup_val'] = self.entry_popup_val

        # The rename entry will be created regardless of whether initial_rename is empty or not
        self.entry_popup_rn = ttk.Entry(self.symbol_treeview)
        self.entry_popup_rn.place(x=x_r, y=y_r-5, width=width_r, height=height_r+10)
        self.entry_popup_rn.insert(0, initial_rename)
        self.current_entry_widgets['entry_popup_rn'] = self.entry_popup_rn

        def on_validate(event):
            self.save_state_before_change()

            # Get the edited values from entry widgets
            new_grapheme = self.entry_popup_sym.get()
            new_phoneme = self.entry_popup_val.get()
            new_rename = self.entry_popup_rn.get()

            # Update Treeview with edited values
            self.symbol_treeview.set(selected_item, grapheme_column, new_grapheme)
            self.symbol_treeview.set(selected_item, phoneme_column, new_phoneme)
            self.symbol_treeview.set(selected_item, rename_column, new_rename)

            # Destroy entry widgets after editing
            for widget in self.current_entry_widgets.values():
                widget.destroy()
            self.current_entry_widgets = {}

           # Split phonemes into a list
            phoneme_list = new_phoneme.split()

            # Update the symbols dictionary, ensuring the rename is saved
            self.symbols[new_grapheme] = [phoneme_list]  # Ensure the phonemes are stored as a list

            # Check if a rename value exists, and update accordingly
            if new_rename:
                self.symbols[new_grapheme].append(new_rename)  # Add rename if it exists

            # Update symbols_list
            for entry in self.symbols_list:
                if entry['symbol'] == initial_grapheme:
                    entry['symbol'] = new_grapheme
                    entry['type'] = phoneme_list
                    entry['rename'] = new_rename.split()  # Always update the rename field
                    break

            # Re-index and select the newly edited item
            self.refresh_treeview_symbols()

        self.entry_popup_sym.bind("<Return>", on_validate)
        self.entry_popup_val.bind("<Return>", on_validate)
        self.entry_popup_rn.bind("<Return>", on_validate)
        self.symbol_treeview.bind("<Return>", on_validate)
    
    def delete_selected_symbols(self):
        selected_items = self.symbol_treeview.selection()
        if not selected_items:
            messagebox.showinfo("Info", f"{self.localization.get('del_symb', 'No symbols selected.')}")
            return

        # Delete from the dictionary if you are syncing it with the tree view
        for item in selected_items:
            item_values = self.symbol_treeview.item(item, 'values')
            self.save_state_before_change()
            if item_values:
                key = item_values[1]  # Assuming the first column in tree view is the key for the dictionary
                if key in self.symbols:
                    del self.symbols[key]
        # Delete from the tree view
        self.symbol_treeview.delete(*selected_items)
        self.phoneme_edit.delete(0, tk.END)
        self.word_edit.delete(0, tk.END)
        self.rename_edit.delete(0, tk.END)
        self.refresh_treeview_symbols()
    
    def filter_symbols_treeview(self):
        search_symbol = self.search_var.get().lower().replace(",", "")
        self.refresh_treeview_symbols()
        if search_symbol:
            for item in self.symbol_treeview.get_children():
                item_sym_values = self.symbol_treeview.item(item, "values")
                if not (search_symbol in item_sym_values[0].lower().replace(",", "") or
                        search_symbol in item_sym_values[1].lower().replace(",", "")):
                    self.symbol_treeview.delete(item)
    
    def refresh_treeview_symbols(self):
        # Setup tag configurations for normal and bold fonts
        self.symbol_treeview.tag_configure('normal', font=self.tree_font)
        self.symbol_treeview.tag_configure('selected', font=self.tree_font_b)

        # Capture the symbol of the currently selected item before clearing entries
        selected = self.symbol_treeview.selection()
        selected_symbol = None
        if selected:
            selected_item_id = selected[0]
            selected_item_values = self.symbol_treeview.item(selected_item_id, "values")
            selected_symbol = selected_item_values[0] if selected_item_values else None

        # Clear all current entries from the treeview
        self.symbol_treeview.delete(*self.symbol_treeview.get_children())

        # Insert new entries into the treeview
        new_selection_id = None
        for entry in self.symbols_list:
            symbol = entry['symbol']
            type_list = entry['type']
            rename = entry.get('rename', '')  # Get 'rename' if it exists, else use an empty string
            
            # Prepare the values tuple based on whether 'rename' is present
            values = (symbol, type_list)
            if rename:
                values = (symbol, type_list, rename)
            
            item_id = self.symbol_treeview.insert('', 'end', values=values, tags=('normal',))

            # Check if this was the previously selected symbol
            if symbol == selected_symbol:
                new_selection_id = item_id

        # If there was a previously selected symbol, reselect its new corresponding item ID
        if new_selection_id:
            self.symbol_treeview.selection_set(new_selection_id)
            self.symbol_treeview.item(new_selection_id, tags=('selected',))
            self.symbol_treeview.see(new_selection_id)

    def on_tree_symbol_selection(self, event):
        # Reset styles for all items
        for item in self.symbol_treeview.get_children():
            self.symbol_treeview.item(item, tags=('normal',))
        self.symbol_treeview.tag_configure('normal', font=self.tree_font)

        # Apply bold font to selected items
        selected_items = self.symbol_treeview.selection()
        for item in selected_items:
            self.symbol_treeview.item(item, tags=('selected',))
        self.symbol_treeview.tag_configure('selected', font=self.tree_font_b)
        
        # Handle multiple selections for displaying grapheme and phoneme data
        if selected_items:
            graphemes = []
            phoneme_lists = []
            renames = []
            
            for item_id in selected_items:
                item_data = self.symbol_treeview.item(item_id, 'values')
                if item_data:
                    # Handle cases where item_data may not have all expected elements
                    if len(item_data) >= 3:
                        grapheme, phonemes, rename = item_data[:3]
                    elif len(item_data) == 2:
                        grapheme, phonemes = item_data
                        rename = ''  # Default value if rename is missing
                    else:
                        grapheme = phonemes = rename = ''  # Default values if data is insufficient
                    
                    graphemes.append(grapheme)
                    phoneme_lists.append(phonemes)
                    renames.append(rename)
            
            # Concatenate all graphemes for display
            graphemes_text = ', '.join(graphemes)

            # Formatting phonemes appropriately based on selection count
            if len(phoneme_lists) > 1:
                phonemes_text = '] ['.join(' '.join(str(phoneme) for phoneme in phoneme_list.split(', ')) for phoneme_list in phoneme_lists)
                phonemes_text = f"[{phonemes_text}]"
            else:
                phonemes_text = ' '.join(str(phoneme) for phoneme in phoneme_lists[0].split(', '))

            # Handle rename - show the first rename value or concatenate if needed
            if len(renames) > 1:
                rename_text = ', '.join(renames)
            else:
                rename_text = renames[0] if renames else ''

            # Update the UI elements with the selected data
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
        phonemes = self.phoneme_entry.get().strip()
        self.save_state_before_change()
        if word and phonemes:
            if not self.entries_window or not self.entries_window.winfo_exists():
                self.update_entries_window()
            self.add_entry_treeview(word, phonemes.split())
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
        else:
            messagebox.showinfo("Error", f"{self.localization.get('add_manual_ent', 'Please provide both word and phonemes for the entry.')}")

    def delete_manual_entry(self):
        selected_items = self.viewer_tree.selection()
        if not selected_items:
            messagebox.showinfo("Notice", self.localization.get('del_no_sel', 'No items selected.'))
            return
        self.save_state_before_change()
        items_to_delete = []
        for item_id in selected_items:
            item_data = self.viewer_tree.item(item_id, 'values')
            if item_data:
                grapheme = item_data[1]
                if grapheme in self.dictionary:
                    items_to_delete.append(item_id)
                else:
                    messagebox.showinfo("Notice", f"Grapheme: {grapheme} {self.localization.get('del_ent_nf', ' not found in dictionary.')}")
            else:
                messagebox.showinfo("Notice", f"{self.localization.get('del_ent_id', 'No data found for item ID ')} {item_id}.")
        # If all selected items are to be deleted, we can clear the dictionary and Treeview
        if len(items_to_delete) == len(self.dictionary):
            self.dictionary.clear()
            self.viewer_tree.delete(*self.viewer_tree.get_children())
        else:
            # Otherwise, delete items one by one
            for item_id in items_to_delete:
                item_data = self.viewer_tree.item(item_id, 'values')
                if item_data:
                    grapheme = item_data[1]
                    if grapheme in self.dictionary:
                        del self.dictionary[grapheme]
            self.viewer_tree.delete(*items_to_delete)
        # Clear the entries once after all deletions
        self.word_entry.delete(0, tk.END)
        self.phoneme_entry.delete(0, tk.END)
        self.refresh_treeview()

    def delete_all_entries(self):
        if not self.dictionary:
            messagebox.showinfo("Info", f"{self.localization.get('del_all_ent', 'No entries to delete.')}")
            return

        if messagebox.askyesno("Confirm", f"{self.localization.get('dell_all_ques', 'Are you sure you want to delete all entries?')}"):
            self.save_state_before_change()
            self.dictionary.clear()
            self.viewer_tree.delete(*self.viewer_tree.get_children())
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
            self.update_entries_window()
    
    def delete_selected_entries(self):
        selected_items = self.viewer_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", f"{self.localization.get('dell_s_ent', 'No entries selected.')}")
            return
        self.save_state_before_change()
        # Check if all selected items are in the dictionary
        all_items_in_dict = all(
            self.viewer_tree.item(item, 'values')[1] in self.dictionary
            for item in selected_items
            if self.viewer_tree.item(item, 'values')
        )
        # If all selected items are in the dictionary, clear the dictionary and treeview in one go
        if all_items_in_dict and len(selected_items) == len(self.viewer_tree.get_children()):
            self.dictionary.clear()
            self.viewer_tree.delete(*self.viewer_tree.get_children())
        else:
            # Otherwise, delete items one by one
            for item in selected_items:
                item_values = self.viewer_tree.item(item, 'values')
                if item_values:
                    key = item_values[1]  # Assuming the first column in tree view is the key for the dictionary
                    if key in self.dictionary:
                        del self.dictionary[key]
            self.viewer_tree.delete(*selected_items)

        self.word_entry.delete(0, tk.END)
        self.phoneme_entry.delete(0, tk.END)
        self.update_entries_window()
    
    def update_entries_window(self):
        if self.entries_window is None or not self.entries_window.winfo_exists():
            self.entries_window = tk.Toplevel(self)
            self.entries_window.title("Entries Viewer")
            self.entries_window.protocol("WM_DELETE_WINDOW", self.close)
            #self.save_state_before_change()
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
            rep2 = ttk.Button(search_frame, text="Replace", style='Accent.TButton', command=self.regex_replace_dialog)
            rep2.pack(side=tk.LEFT, padx=(5,10), pady=10)
            self.localizable_widgets['rep_button'] = rep2

            # Create a Frame to hold the Treeview and the Scrollbar
            frame = tk.Frame(self.entries_window)
            frame.pack(fill=tk.BOTH, expand=True)

            # Create the Treeview
            self.viewer_tree = ttk.Treeview(frame, columns=('Index', 'Grapheme', 'Phonemes'),show='headings', height=20)
            self.viewer_tree.heading('Index', text='Index')
            self.viewer_tree.heading('Grapheme', text='Grapheme')
            self.viewer_tree.heading('Phonemes', text='Phonemes')
            self.viewer_tree.column('Index', width=50, anchor='center', stretch=False)
            self.viewer_tree.column('Grapheme', width=170, anchor='w')
            self.viewer_tree.column('Phonemes', width=230, anchor='w')

            # Create and pack the Scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.viewer_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(5))
            self.viewer_tree.configure(yscrollcommand=scrollbar.set)

            # deselect
            self.viewer_tree.bind("<Button-2>", self.deselect_entry)
            #self.viewer_tree.bind("<Button-3>", self.deselect_entry)
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
                self.entries_window.bind('<Control-z>', lambda event: self.undo())
                self.entries_window.bind('<Control-y>', lambda event: self.redo())
                self.entries_window.bind("<Control-c>", lambda event: self.copy_entry())
                self.entries_window.bind("<Control-x>", lambda event: self.cut_entry())
                self.entries_window.bind("<Control-v>", lambda event: self.paste_entry())
                self.entries_window.bind('<Control-f>', lambda event: self.search_entry.focus_set())
                self.entries_window.bind('<Control-h>', lambda event: self.regex_replace_dialog())
            elif os_name == "Darwin":
                # macOS key bindings (uses Command key)
                self.entries_window.bind("<Command-a>", lambda event: self.select_all_entries())
                self.entries_window.bind('<Command-z>', lambda event: self.undo())
                self.entries_window.bind('<Command-y>', lambda event: self.redo())
                self.entries_window.bind("<Command-c>", lambda event: self.copy_entry())
                self.entries_window.bind("<Command-x>", lambda event: self.cut_entry())
                self.entries_window.bind("<Command-v>", lambda event: self.paste_entry())
                self.entries_window.bind('<Command-f>', lambda event: self.search_entry.focus_set())
                self.entries_window.bind('<Command-h>', lambda event: self.regex_replace_dialog())
            else:
                self.entries_window.bind('<Control-z>', lambda event: self.undo())
                self.entries_window.bind('<Control-y>', lambda event: self.redo())
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
            ref = ttk.Button(button_frame, text="Refresh", style='TButton', command=self.update_entries_window)
            ref.pack(side=tk.RIGHT, padx=5, pady=10)
            self.localizable_widgets['refresh'] = ref
            close = ttk.Button(button_frame, text="Close", style='TButton', command=self.close)
            close.pack(side=tk.RIGHT, padx=5, pady=10)
            self.localizable_widgets['close'] = close
            ttk.Button(button_frame, text="-", style='Accent.TButton', command=lambda: self.change_font_size(-1)).pack(side="left", padx=(15,5), pady=10)
            ttk.Button(button_frame, text="+", style='Accent.TButton', command=lambda: self.change_font_size(1)).pack(side="left", padx=5, pady=10)

            # Insert entries in batches
            if self.load_cmudict or self.load_json_file or self.load_yaml_file:
                batch_size = 10000
                entries = list(self.dictionary.items())
                for i in range(0, len(entries), batch_size):
                    batch = entries[i:i+batch_size]
                    for index, (grapheme, phonemes) in enumerate(batch, start=i):
                        self.viewer_tree.insert("", "end", values=(index+1, grapheme, phonemes))
                        self.viewer_tree.update()

            # Refresh the Treeview
            self.viewer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15,0))
        if self.entries_window.winfo_exists():
            self.apply_localization()
        self.refresh_treeview()
    
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
            command=self.undo)
        self.context_menu.add_command(
            label=self.localization.get('cont_redo', 'Redo'), 
            command=self.redo)
        
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
        selected_item = self.viewer_tree.selection()[0]
        #column = self.viewer_tree.identify_column(event.x)

        # Define the column identifiers
        G2P_column = "#1"
        grapheme_column = "#2"
        phoneme_column = "#3"

        # Calculate the positions and sizes of the cells
        x_gr, y_gr, width_gr, height_gr = self.viewer_tree.bbox(selected_item, G2P_column)
        x_g, y_g, width_g, height_g = self.viewer_tree.bbox(selected_item, grapheme_column)
        x_p, y_p, width_p, height_p = self.viewer_tree.bbox(selected_item, phoneme_column)

        # Retrieve initial values from Treeview, removing commas from phoneme
        g2p_b = self.viewer_tree.item(selected_item, "values")[0]
        initial_grapheme = self.viewer_tree.item(selected_item, "values")[1]
        initial_phoneme = self.viewer_tree.item(selected_item, "values")[2].replace(",", "").replace("'", "")

        # Destroy currently open widgets if they exist
        if self.current_entry_widgets:
            for widget in self.current_entry_widgets.values():
                widget.destroy()
            self.current_entry_widgets = {}
        
        # Create a button for G2P correction
        g2p_correction = ttk.Button(self.viewer_tree, text="G2P", style="Accent.TButton", command=self.is_g2p)
        g2p_correction.place(x=x_gr, y=y_gr-5, width=width_gr, height=height_gr+10)
        self.current_entry_widgets['g2p_correction'] = g2p_correction

        # Create entry widgets for editing grapheme and phoneme
        self.entry_popup_g = ttk.Entry(self.viewer_tree)
        self.entry_popup_g.place(x=x_g, y=y_g-5, width=width_g, height=height_g+10)
        self.entry_popup_g.insert(0, initial_grapheme)
        self.entry_popup_g.focus_set()
        self.current_entry_widgets['self.entry_popup_g'] = self.entry_popup_g

        self.entry_popup_p = ttk.Entry(self.viewer_tree)
        self.entry_popup_p.place(x=x_p, y=y_p-5, width=width_p, height=height_p+10)
        self.entry_popup_p.insert(0, initial_phoneme)
        self.current_entry_widgets['self.entry_popup_p'] = self.entry_popup_p

        def on_validate(event):
            self.save_state_before_change()

            # Get the edited values from entry widgets
            new_grapheme = self.entry_popup_g.get()
            new_phoneme = self.entry_popup_p.get().replace("'", "")
            phoneme_list = [phoneme.replace(" ", ",") if " " in phoneme else phoneme for phoneme in new_phoneme.split()]

            # Update Treeview with edited values
            self.viewer_tree.set(selected_item, grapheme_column, new_grapheme)
            self.viewer_tree.set(selected_item, phoneme_column, new_phoneme)

            # Destroy entry widgets after editing
            self.entry_popup_g.destroy()
            self.entry_popup_p.destroy()
            g2p_correction.destroy()
            self.current_entry_widgets = {}

            # Preserve the index and update the dictionary
            if initial_grapheme in self.dictionary:
                # Get the current index of the initial grapheme
                items = list(self.dictionary.items())
                index = [i for i, (k, v) in enumerate(items) if k == initial_grapheme][0]
                # Create an ordered dictionary to preserve the order
                ordered_dict = OrderedDict()

                # Populate the ordered dictionary with entries, updating or adding the new entry at the correct index
                for i, (key, value) in enumerate(items):
                    if i == index:
                        ordered_dict[new_grapheme] = phoneme_list
                    elif key != initial_grapheme:
                        ordered_dict[key] = value
                self.dictionary = ordered_dict
                self.refresh_treeview()

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
                selected_phoneme = values[2]

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

                self.save_state_before_change()

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
            # Identify the target item
            target_item = self.viewer_tree.identify_row(event.y)
            if target_item and self.dragged_item != target_item:
                # drag logic here
                dragged_index = self.viewer_tree.index(self.dragged_item)
                target_index = self.viewer_tree.index(target_item)
                self.viewer_tree.move(self.dragged_item, '', target_index)
                
                dragged_data = self.viewer_tree.item(self.dragged_item, 'values')
                dragged_grapheme = dragged_data[1]
                if dragged_grapheme in self.dictionary:
                    dragged_entry = self.dictionary.pop(dragged_grapheme)
                    new_keys = list(self.dictionary.keys())
                    new_keys.insert(target_index, dragged_grapheme)
                    new_dict = {}
                    for key in new_keys:
                        new_dict[key] = dragged_entry if key == dragged_grapheme else self.dictionary[key]
                    self.dictionary = new_dict

            # Close and clean up the drag window if it was opened
            self.viewer_tree.selection_set(self.dragged_item)  # Restore selection
            self.update_entries_window()  # Refresh view
        if hasattr(self, 'drag_window') and self.drag_window:
            self.drag_window.destroy()
            self.drag_window = None
        self.drag_initiated = False  # Reset the drag initiated flag
                
    def regex_replace_dialog(self):
        if self.replace_window is None or not self.replace_window.winfo_exists():
            self.replace_window = tk.Toplevel(self)
            self.replace_window.resizable(False, False)
            self.replace_window.title("Regex Replace")
            self.save_state_before_change()
            self.load_csv()
  
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

            reg_rep = ttk.Label(reg_frame1, text="Replacement:", font=self.font)
            reg_rep.grid(row=1, column=0, padx=10, pady=5)
            self.localizable_widgets['replacement'] = reg_rep
            replace_var = tk.StringVar()
            replace_entry = ttk.Entry(reg_frame1, textvariable=replace_var, width=30)
            replace_entry.grid(row=1, column=1, padx=15, pady=5, sticky="ew")

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

            to_tove_lo = ttk.Button(phone_frame_from, style='Accent.TButton', text="▶", command=self.system_phonemes)
            to_tove_lo.grid(row=0, column=1, padx=10)

            # Combobox for `To Selected Phonetic System`
            phone_frame_to = ttk.Frame(reg_frame)
            phone_frame_to.grid(padx=(0,15), pady=(10,0), sticky='nsew', row=3, column=1)
            phone_frame_to.grid_columnconfigure(0, weight=1)
            phone_frame_to.grid_columnconfigure(1, weight=0)

            self.combo_to = ttk.Combobox(phone_frame_to, values=self.systems, state="readonly")
            self.combo_to.grid(row=0, column=0, sticky='nsew')
            self.combo_to.set("Phonetic System")

            rep_frame = ttk.Frame(reg_frame)
            rep_frame.grid(padx=(5,15), pady=5, sticky="nsew", row=4, column=1)
            rep_frame.grid_columnconfigure(0, weight=1)
            rep_frame.grid_columnconfigure(1, weight=3)

            # Button to execute the replace operation
            apply_button = ttk.Button(rep_frame, text="Replace", style="Accent.TButton", command=lambda: replace_selected())
            apply_button.grid(row=0, column=0, padx=(0,3), pady=10, sticky="ew")
            self.localizable_widgets['apply'] = apply_button

            apply_button1 = ttk.Button(rep_frame, text="Replace All", style="Accent.TButton", command=lambda: apply_replace())
            apply_button1.grid(row=0, column=1, padx=(3,0), sticky="ew")
            self.localizable_widgets['apply1'] = apply_button1

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

            self.replace_window.bind("<Escape>", lambda event: self.replace_window.destroy())

        if self.replace_window.winfo_exists():
            self.apply_localization()

        def apply_replace():
            self.save_state_before_change()
            pattern = regex_var.get()
            replacement = replace_var.get()
            target = target_var.get()
            # Compile regex pattern to catch errors early
            try:
                compiled_pattern = re.compile(pattern)
            except re.error as e:
                print(f"Regex error: {e}")
                return
            # Prepare to track modifications
            items_modified = 0
            # Iterate over all items in the tree view
            for grapheme, phonemes in list(self.dictionary.items()):
                if target == "Graphemes":
                    new_grapheme = compiled_pattern.sub(replacement, grapheme)
                    if new_grapheme != grapheme:
                        self.dictionary[new_grapheme] = self.dictionary.pop(grapheme)
                        items_modified += 1
                elif target == "Phonemes":
                    phonemes_string = ', '.join(phonemes)
                    modified_phoneme_string = compiled_pattern.sub(replacement, phonemes_string)
                    if modified_phoneme_string != phonemes_string:
                        new_phoneme_list = [phoneme.strip() for phoneme in modified_phoneme_string.split(',')]
                        self.dictionary[grapheme] = new_phoneme_list
                        items_modified += 1
            self.refresh_treeview()
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
        def replace_selected():
            self.save_state_before_change()
            selected_items = self.viewer_tree.selection()
            if selected_items:
                pattern = regex_var.get()
                replacement = replace_var.get()
                target = target_var.get()

                # Same mechanics to replace all but only on the selected entries
                try:
                    compiled_pattern = re.compile(pattern)
                except re.error as e:
                    print(f"Regex error: {e}")
                    return

                items_modified = 0
                for item in selected_items:
                    item_values = self.viewer_tree.item(item, "values")
                    if target == "Graphemes":
                        new_grapheme = compiled_pattern.sub(replacement, item_values[1])
                        if new_grapheme != item_values[1]:
                            self.viewer_tree.item(item, values=(new_grapheme, item_values[2]))
                            if item_values[1] in self.dictionary:
                                self.dictionary[new_grapheme] = self.dictionary.pop(item_values[1])
                            items_modified += 1
                    elif target == "Phonemes":
                        phonemes_string = item_values[2].strip()
                        modified_phoneme_string = compiled_pattern.sub(replacement, phonemes_string)
                        if modified_phoneme_string != phonemes_string:
                            self.viewer_tree.item(item, values=(item_values[1], modified_phoneme_string))
                            new_phoneme_list = [phoneme.strip() for phoneme in modified_phoneme_string.split(',')]
                            self.dictionary[item_values[1]] = new_phoneme_list
                            items_modified += 1
                self.refresh_treeview()
                self.word_entry.delete(0, tk.END)
                self.phoneme_entry.delete(0, tk.END)
            else:
                apply_replace()
            if self.search_var.get():
                self.filter_treeview()
        self.icon(self.replace_window)
        self.apply_localization()
    
    def system_phonemes(self):
        system_from = self.combo_from.get()
        system_to = self.combo_to.get()
        self.save_state_before_change()

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

        # Create a reverse mapping for phoneme_map_to
        inverse_phoneme_map_to = {v: k for k, v in phoneme_map_to.items()}

        def replace_phonemes(phoneme_sequence):
            replaced_sequence = []
            i = 0
            while i < len(phoneme_sequence):
                match_found = False
                # Check for the longest possible match from current position
                for j in range(len(phoneme_sequence), i, -1):
                    substring = ' '.join(phoneme_sequence[i:j])
                    if substring in phoneme_map_from:
                        source_phoneme = phoneme_map_from[substring]
                        replacement = inverse_phoneme_map_to.get(source_phoneme, substring)
                        # Split multi-phoneme replacements by commas
                        if ' ' in replacement:
                            replaced_sequence.extend(replacement.split(' '))
                        else:
                            replaced_sequence.append(replacement)
                        i = j
                        match_found = True
                        break
                if not match_found:
                    replaced_sequence.append(phoneme_sequence[i])
                    i += 1
            return replaced_sequence

        # Iterate through the dictionary and update phonemes
        for key, value in self.dictionary.items():
            if isinstance(value, list):
                self.dictionary[key] = replace_phonemes(value)
            else:
                print(f"Unexpected value type for key {key}: {type(value)}")
        self.refresh_treeview()
    
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
            self.systems = next(reader)
            for row in reader:
                for i, system in enumerate(self.systems):
                    if system not in self.phoneme_map:
                        self.phoneme_map[system] = {}
                    if row[i]:
                        self.phoneme_map[system][row[i]] = row[0]  # Map phoneme to its replacement

    def find_matches(self, pattern, target):
        items_to_highlight = []
        compiled_pattern = re.compile(pattern)

        for index, (grapheme, phonemes) in enumerate(self.dictionary.items()):
            if target == "Graphemes" and compiled_pattern.search(grapheme):
                item_id = self.viewer_tree.get_children()[index]
                items_to_highlight.append(item_id)
            elif target == "Phonemes":
                phoneme_string = ", ".join(phonemes)
                if compiled_pattern.search(phoneme_string):
                    item_id = self.viewer_tree.get_children()[index]
                    items_to_highlight.append(item_id)
        # Clear the current selection to ensure only new results are highlighted
        self.viewer_tree.selection_remove(self.viewer_tree.selection())
        # Set the selection to the items found
        self.viewer_tree.selection_set(items_to_highlight)
        if items_to_highlight:
            self.viewer_tree.see(items_to_highlight[0])  # Ensure the first match is visible
        else:
            messagebox.showinfo("No Matches", self.localization.get('find_matches', 'No matches found.'))

    def find_next(self, direction=None, pattern=None, target=None):
        compiled_pattern = re.compile(pattern)
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
            if target == "Phonemes" and compiled_pattern.search(", ".join(phonemes)):
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
                    self.title(self.base_title)
                    self.viewer_tree.delete(*self.viewer_tree.get_children())
                    self.entries_window.destroy()
                    self.word_entry.delete(0, tk.END)
                    self.phoneme_entry.delete(0, tk.END)
                    self.dictionary.clear()
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
                    phonemes = values[2].split(', ')
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
        
        # Attempt to parse the custom entry format
        entries = re.findall(r"- \{grapheme: (.*?), phonemes: (.*?)\}", clipboard_content)
        if not entries:
            # Attempt to parse the CMUDict format
            entries = re.findall(r"(\S+)\s+((?:\S+\s*)+)", clipboard_content)
        
        if entries:
            selected = self.viewer_tree.selection()
            insert_index = self.viewer_tree.index(selected[-1]) + 1 if selected else 'end'
            
            for grapheme, phonemes in entries:
                phonemes_list = [phoneme.strip("',[] \"") for phoneme in phonemes.split()]
                grapheme = grapheme.strip("\"")
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
            messagebox.showinfo("Paste", f"{self.localization.get('paste_mess', 'Clipboard is empty or data is invalid.')}")
    
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
                    phoneme_lists.append(phonemes)
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
        if new_word and new_phonemes:
            phoneme_display = ', '.join(new_phonemes)

            # Determine the actual insert index if 'end' and there are selected items
            if insert_index == 'end' and self.viewer_tree.selection():
                insert_index = self.viewer_tree.index(self.viewer_tree.selection()[-1]) + 1

            if new_word in self.dictionary:
                # Update the existing item's phonemes
                self.dictionary[new_word] = new_phonemes
                for idx, item in enumerate(self.viewer_tree.get_children()):
                    if self.viewer_tree.item(item, 'values')[1] == new_word:
                        self.viewer_tree.item(item, values=(idx + 1, new_word, phoneme_display))
                        break
            else:
                # Insert new entry if the grapheme does not exist
                new_item_ids = []
                if insert_index == 'end':
                    item_id = self.viewer_tree.insert('', 'end', values=(len(self.dictionary) + 1, new_word, phoneme_display), tags=('normal',))
                    new_item_ids.append(item_id)
                    self.dictionary[new_word] = new_phonemes
                else:
                    item_id = self.viewer_tree.insert('', insert_index, values=(insert_index, new_word, phoneme_display), tags=('normal',))
                    new_item_ids.append(item_id)
                    # Insert the new entry into the dictionary at the correct position
                    items = list(self.dictionary.items())
                    items.insert(insert_index, (new_word, new_phonemes))
                    self.dictionary.clear()
                    self.dictionary.update(items)

                self.viewer_tree.selection_set(new_item_ids)
            self.refresh_treeview()

    def filter_treeview(self, exact_search=False):
        search_text = self.search_var.get().strip().lower()  # Get and normalize search text
        # Clear previous selections
        self.viewer_tree.selection_remove(self.viewer_tree.selection())
        if search_text:
            closest_item = None
            closest_distance = float('inf')  # Start with a large distance

            for item in self.viewer_tree.get_children():
                item_values = self.viewer_tree.item(item, "values")
                matched = False
                for value in item_values:
                    value_lower = value.lower().strip().replace(",", "")
                    if exact_search:
                        # Perform exact match search
                        if search_text == value_lower:
                            closest_item = item
                            matched = True
                            break
                    else:
                        # Perform closest match search
                        if search_text in value_lower:
                            # Calculate distance
                            distance = abs(len(value_lower) - len(search_text))
                            if distance < closest_distance:
                                closest_item = item
                                closest_distance = distance
                            matched = True

                if exact_search and matched:
                    # If exact match found and exact_search is True, stop iterating
                    break
            # Select the closest matching item
            if closest_item:
                self.viewer_tree.selection_set(closest_item)
                self.viewer_tree.see(closest_item)
            # Optionally iterate through all items if used by a button
            elif not exact_search:
                items_to_select = []
                for item in self.viewer_tree.get_children():
                    item_values = self.viewer_tree.item(item, "values")
                    for value in item_values:
                        value_lower = value.lower().strip().replace(",", "")
                        if search_text in value_lower:
                            items_to_select.append(item)
                            break

                # Set the selection to items found in the iteration
                if items_to_select:
                    self.viewer_tree.selection_set(items_to_select)
                    self.viewer_tree.see(items_to_select[0])
    
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
        if selected_template == "Current Template":
            template_path = filedialog.askopenfilename(title="Using the current YAML file as a template", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
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
        yaml = YAML()
        yaml.width = 4096
        yaml.preserve_quotes = True
        existing_data = CommentedMap()
        yaml.allow_duplicate_keys = True  # Allow duplicated keys, but we'll handle duplicates manually

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
            escaped_symbol = escape_symbols(symbol)
            type_list = values[0] if isinstance(values[0], list) else [values[0]]
            type_str = ', '.join(f"{t}" for t in type_list)

            if escaped_symbol not in added_symbols:  # Avoid adding duplicates
                entry = CommentedMap([('symbol', escaped_symbol), ('type', type_str)])
                symbols_entries.append(entry)
                added_symbols.add(escaped_symbol)
        
        rename_entries = CommentedSeq()
        added_replacements = set()  # Track added replacements to avoid duplicates
        for symbol, data in self.symbols.items():
            if len(data) > 1 and data[1]:  # Check if rename data exists
                from_symbol = escape_symbols(symbol)
                to_data = escape_symbols(data[1])
                replacement_key = (from_symbol, to_data)  # Create a key to check for duplicates

                if replacement_key not in added_replacements:  # Avoid adding duplicates
                    entry = CommentedMap([('from', from_symbol), ('to', to_data)])
                    rename_entries.append(entry)

        # Prepare new entries
        new_entries = CommentedSeq()
        for item in self.viewer_tree.get_children():
            item_values = self.viewer_tree.item(item, 'values')
            if len(item_values) >= 3:
                grapheme = item_values[1]
                phonemes = self.dictionary.get(grapheme, [])
                if self.lowercase_phonemes_var.get():
                    phonemes = [phoneme.lower() for phoneme in phonemes]
                if self.remove_numbered_accents_var.get():
                    phonemes = self.remove_numbered_accents(phonemes)
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

        # Configure YAML instance to use flow style for specific parts
        def compact_representation(dumper, data):
            return dumper.represent_mapping(
                'tag:yaml.org,2002:map', data, flow_style=True
            )
        yaml.representer.add_representer(CommentedMap, compact_representation)

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
        # Prepare data for JSON format
        data = []
        for grapheme, phonemes in self.dictionary.items():
            if self.lowercase_phonemes_var.get():
                phonemes = [phoneme.lower() for phoneme in phonemes]
            if self.remove_numbered_accents_var.get():
                phonemes = self.remove_numbered_accents(phonemes)
            phoneme_str = ' '.join(phonemes)
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
        # Prepare entries as formatted strings
        self.clear_entries()
        entries_text = []
        for grapheme, phonemes in self.dictionary.items():
            if self.lowercase_phonemes_var.get():
                phonemes = [phoneme.lower() for phoneme in phonemes]
            if self.remove_numbered_accents_var.get():
                phonemes = self.remove_numbered_accents(phonemes)
            formatted_phonemes = ' '.join(phonemes)
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
            options = ["Current Template"] + yaml_files
            combobox['values'] = options
            self.template_var.set(options[0])
            self.template_combobox.bind("<<ComboboxSelected>>", self.on_template_selected)
        except Exception as e:
            messagebox.showerror("Error", f"{self.localization.get('temp_combo_err', 'Failed to read the directory: ')} {str(e)}")

    def on_template_selected(self, event):
        selected_template = self.template_var.get()
        if selected_template == "Current Template":
            self.clear_symbols_data()
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
                    self.quit()
        else:
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
                joined_phonemes = ''.join(phonemes)
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

        # Add localizable Checkbuttons
        remove_accents_cb = ttk.Checkbutton(options_frame, text="Remove Number Accents", style="TCheckbutton", variable=self.remove_numbered_accents_var)
        remove_accents_cb.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['remove_accents'] = remove_accents_cb

        lowercase_phonemes_cb = ttk.Checkbutton(options_frame, text="Make Phonemes Lowercase", style="TCheckbutton", variable=self.lowercase_phonemes_var)
        lowercase_phonemes_cb.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['lowercase_phonemes'] = lowercase_phonemes_cb

        edit_symbols = ttk.Button(options_frame, text="Edit Symbols", style='Accent.TButton', command=self.open_symbol_editor)
        edit_symbols.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['edit_sym'] = edit_symbols

        plugin_focus = ttk.Button(options_frame, text="Plugins", style='Accent.TButton', command=self.focus_on_plugins)
        plugin_focus.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['plugin_focus'] = plugin_focus
       
        # Sorting combobox
        self.sort_options_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(options_frame, textvariable=self.sort_options_var, state="readonly", values=('Default Sorting', 'A-Z Sorting', 'Z-A Sorting'))
        self.sort_combobox.set('Default Sorting')
        self.sort_combobox.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.sort_combobox.bind("<<ComboboxSelected>>", self.sort_entries)

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
        self.phoneme_entry = ttk.Entry(manual_frame)
        self.phoneme_entry.grid(row=1, column=1, padx=(5, 15), pady=10, sticky="nsew")
        self.word_entry.bind("<Return>", self.add_manual_entry_event)
        self.phoneme_entry.bind("<Return>", self.add_manual_entry_event)

        add_entry_button = ttk.Button(manual_frame, text="Add Entry", style='Accent.TButton', command=self.add_manual_entry)
        add_entry_button.grid(row=2, column=1, columnspan=1, padx=5, pady=(5,15))
        self.localizable_widgets['add_entry'] = add_entry_button

        delete_entry_button = ttk.Button(manual_frame, text="Delete Entry", style='Accent.TButton', command=self.delete_manual_entry)
        delete_entry_button.grid(row=2, column=0, columnspan=1, padx=5, pady=(5,15))
        self.localizable_widgets['delete_entry'] = delete_entry_button

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
        cmux = ttk.Button(convert_frame, text="Export CMUDict", style='TButton', command=self.export_cmudict)
        cmux.grid(column=0, row=0, padx=5, sticky="ew")
        self.localizable_widgets['export_cmudict'] = cmux
        ap_yaml = ttk.Button(load_frame, text= "Append YAML File", style='TButton', command=self.merge_yaml_files)
        ap_yaml.grid(column=0, row=0, padx=5, pady=5, sticky="ew")
        self.localizable_widgets['append_yaml'] = ap_yaml
        open_yaml = ttk.Button(load_frame, text= "Open YAML File", style='TButton', command=self.load_yaml_file)
        open_yaml.grid(column=1, row=0, padx=5, sticky="ew")
        self.localizable_widgets['open_yaml'] = open_yaml
        
        # For saving, you might want distinct actions for each button, so specify them if they differ
        ds_save = ttk.Button(save_frame, text="Save OU Dictionary", style='Accent.TButton', command=self.save_as_ou_yaml)
        ds_save.pack(expand=True, fill="x", padx=(5), pady=(0,5))
        self.localizable_widgets['save_ou'] = ds_save
        label = ttk.Label(cad_frame, text=f"© Cadlaxa | OU Dictionary Editor {self.current_version}", font=label_font, foreground=label_color)
        label.grid(row=0, column=1, sticky="ew", pady=(0,10))
        cad_frame.columnconfigure(0, weight=1)
        cad_frame.columnconfigure(1, weight=0)
        cad_frame.columnconfigure(2, weight=1)
        
        # Configure grid weight for overall flexibility
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=2)
        self.columnconfigure(0, weight=1)
    
    def settings_widgets(self):
        # LabelFrame for updates
        update_frame = ttk.LabelFrame(self.additional_tab, text="Updates")
        update_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['update'] = update_frame
        update_frame.columnconfigure(0, weight=3)
        update_frame.columnconfigure(1, weight=1)

        # Button to check for updates
        update_button = ttk.Button(update_frame, text="Check for Updates", style='Accent.TButton', command=self.check_for_updates)
        update_button.grid(row=0, column=0, padx=(20,5), pady=20, sticky="ew",)
        self.localizable_widgets['update_b'] = update_button

        # Button to what's new
        nw_button = ttk.Button(update_frame, text="What's New", command=self.whats_new)
        nw_button.grid(row=0, column=1, padx=(5, 20), pady=20, sticky="ew",)
        self.localizable_widgets['whats_new'] = nw_button

        # LabelFrame for themes
        theme_frame = ttk.LabelFrame(self.additional_tab, text="Themes")
        theme_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['theme'] = theme_frame
        theme_frame.columnconfigure(0, weight=1)
        theme_frame.columnconfigure(1, weight=1)

        # Frame for theme combobox within the theme_frame
        self.theming = ttk.Frame(theme_frame)
        self.theming.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.theming.columnconfigure(1, weight=1)
        self.theming.columnconfigure(1, weight=1)
        

        # Label and combobox for Accent selection
        theme_select = ttk.Label(self.theming, text="Select Theme:", font=self.font)
        theme_select.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['def_theme'] = theme_select
        theme_options = ["Amaranth", "Amethyst", "Burnt Sienna", "Dandelion", "Denim",
                         "Electric Blue", "Fern", "Lemon Ginger", "Light See Green", "Lightning Yellow",
                         "Mint","Orange", "Payne's Gray", "Pear",
                         "Persian Red", "Pink", "Salmon", "Sapphire", "Sea Green", "Seance", "Sky Magenta", "Sunny Yellow",
                         "Yellow Green"] # Theme options
        theme_combobox = ttk.Combobox(self.theming, textvariable=self.accent_var, values=theme_options, state="readonly")
        theme_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        theme_combobox.bind("<<ComboboxSelected>>", self.toggle_theme)

        radio_frame = ttk.Frame(theme_frame)
        radio_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,20), sticky="ew")
        radio_frame.columnconfigure(0, weight=1)
        radio_frame.columnconfigure(1, weight=1)
        radio_frame.columnconfigure(2, weight=1)

        # Radio button for light theme
        light_theme_button = ttk.Radiobutton(radio_frame, text="Light", value="Light", variable=self.theme_var, command=self.toggle_theme)
        light_theme_button.grid(row=1, column=0)

        # Radio button for dark theme
        dark_theme_button = ttk.Radiobutton(radio_frame, text="Dark", value="Dark", variable=self.theme_var, command=self.toggle_theme)
        dark_theme_button.grid(row=1, column=1)

        # Radio button for system theme
        dark_theme_button = ttk.Radiobutton(radio_frame, text="System", value="System", variable=self.theme_var, command=self.toggle_theme)
        dark_theme_button.grid(row=1, column=2)

        # LabelFrame for localization selection on the options tab
        localization_frame = ttk.LabelFrame(self.additional_tab, text="Localization Options")
        localization_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['local_op'] = localization_frame
        localization_frame.columnconfigure(0, weight=1)
        localization_frame.columnconfigure(1, weight=1)

        # Frame for localization combobox within the localization_frame
        self.save_loc = ttk.Frame(localization_frame)
        self.save_loc.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.save_loc.columnconfigure(1, weight=1)

        local_select = ttk.Label(self.save_loc, text="Select Localization:", font=self.font)
        local_select.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['select_local'] = local_select
        localization_combobox = ttk.Combobox(self.save_loc, textvariable=self.localization_var, state="readonly")
        localization_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        localization_combobox.bind("<<ComboboxSelected>>", self.localization_selected)
        self.update_localization_combobox(localization_combobox)
    
    def other_widgets(self):
        self.other_frame = ttk.Frame(self.others_tab)
        self.other_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")
        self.other_frame.columnconfigure(0, weight=1)
        self.other_frame.columnconfigure(1, weight=1)

        # Frame for Synthv controls
        synthv_frame = ttk.LabelFrame(self.other_frame, text="Synthv")
        synthv_frame.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        synthv_frame.columnconfigure(0, weight=1)

        # Synthv Import/Export
        synthv_export = ttk.Button(synthv_frame, style='Accent.TButton', text="Export Dictionary", command=self.export_json)
        synthv_export.grid(row=2, column=0, padx=10, pady=(5,10), sticky="ew")
        self.localizable_widgets['export'] = synthv_export

        synthv_import = ttk.Button(synthv_frame, text="Import Dictionary", style='TButton', command=self.load_json_file)
        synthv_import.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['import'] = synthv_import

        # Frame for UI controls (placeholder name)
        ui_frame = ttk.LabelFrame(self.other_frame, text="Adding more in the future")
        ui_frame.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")
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
        self.load_g2p_checkbox_state()

        self.g2p_selection = ttk.Combobox(g2p_frame, state='readonly')
        self.g2p_selection.grid(row=0, column=1, padx=(5, 20), pady=5, sticky="ew")
        self.g2p_selection['values'] = tuple(sorted(['Arpabet-Plus G2p', 'French G2p', 'German G2p', 'Marzipan (German) G2p', 'Italian G2p', 'Japanese Monophone G2p'
                                        , 'Millefeuille (French) G2p', 'Portuguese G2p', 'Russian G2p', 'Spanish G2p']))
        
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

        self.vb_import_button = ttk.Button(self.plug_frame, style='Accent.TButton' , text="Import VB Dictionary", command=self.get_yaml_from_temp)
        self.vb_import_button.grid(row=2, column=0, padx=10, pady=(5,10), sticky="ew")
        self.localizable_widgets['import_vb'] = self.vb_import_button

        # Frame for Terminal
        self.terminal = ttk.LabelFrame(self.plugin_frame, text="YAML Generator")
        self.terminal.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")
        self.terminal.columnconfigure(0, weight=1)
        self.localizable_widgets['console'] = self.terminal

        self.dict_gen = ttk.Button(self.terminal, style='TButton', text="Reclist to Yaml Template", command=self.import_gen_yaml_temp_data)
        self.dict_gen.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['rec_yaml_gen'] = self.dict_gen

        #self.vb_import_button = ttk.Button(self.terminal, style='Accent.TButton' , text="Import VB Dictionary", command=self.get_yaml_from_temp)
        #self.vb_import_button.grid(row=2, column=0, padx=10, pady=(5,10), sticky="ew")
        #self.localizable_widgets['import_vb'] = self.vb_import_button
    
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
            self.symbol_treeview['columns'] = ('symbol', 'type')
            self.symbol_treeview.heading('symbol', text='Symbol')
            self.symbol_treeview.heading('type', text='Type')

            # Insert the symbols into the Treeview
            for symbol, symbol_type in symbols.items():
                self.add_symbols_treeview(word=symbol, value=[symbol_type])
                self.loading_window.destroy()
        if localization:
            self.localization.update(localization)

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
        if self.g2p_checkbox_var.get():
            g2p_models = {
                'Arpabet-Plus G2p': ('Assets.G2p.arpabet_plus', 'ArpabetPlusG2p'),
                'French G2p': ('Assets.G2p.frenchG2p', 'FrenchG2p'),
                'German G2p': ('Assets.G2p.germanG2p', 'GermanG2p'),
                'Marzipan (German) G2p': ('Assets.G2p.marzipanG2p', 'MarzipanG2p'),
                'Italian G2p': ('', 'ItalianG2p'),
                'Japanese Monophone G2p': ('Assets.G2p.jp_mono', 'JapaneseMonophoneG2p'),
                'Millefeuille (French) G2p': ('Assets.G2p.millefeuilleG2p', 'MillefeuilleG2p'),
                'Portuguese G2p': ('Assets.G2p.portugueseG2p', 'PortugueseG2p'),
                'Russian G2p': ('Assets.G2p.russianG2p', 'RussianG2p'),
                'Spanish G2p': ('Assets.G2p.spanishG2p', 'SpanishG2p'),
            }
            module_name, class_name = g2p_models.get(selected_value, (None, None))
            if module_name and class_name:
                try:
                    module = __import__(module_name, fromlist=[class_name])
                    self.g2p_model = getattr(module, class_name)()
                    print(f"G2P model {selected_value} loaded successfully.")
                    self.save_g2p(selected_value)
                    self.transform_text()
                except Exception as e:
                    print(f"Failed to load G2P model {selected_value}: {e}")
            else:
                print(f"No G2P model found for {selected_value}")
        else:
            self.g2p_model = None
            print("G2P is disabled.")
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
        with open("readme.md", "r") as file:
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

        btn_see = ttk.Button(button_frame, text="See Release on Github", style='Accent.TButton')
        btn_see.pack(side=tk.RIGHT, padx=5)
        self.localizable_widgets['btn_git'] = btn_see
        btn_see.bind("<Button-1>", lambda e:
        self.callback("https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/releases/latest"))

        # Add a checkbox to not show the "What's New" window next time
        self.show_whats_new_var = tk.BooleanVar(value=False)
        chk_show_whats_new = ttk.Checkbutton(button_frame, text="Do not show this again", variable=self.show_whats_new_var)
        chk_show_whats_new.pack(side=tk.LEFT, pady=10, anchor='w')
        self.localizable_widgets['whats_new_cb'] = chk_show_whats_new
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
            with open('./Templates/Localizations/en_US.yaml', 'r') as file:
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