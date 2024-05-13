import tkinter as tk
from Assets.modules.sv_ttk import sv_ttk
from tkinter import filedialog, messagebox, ttk, PhotoImage, BOTH
import os, sys, re
sys.path.append('.')
from pathlib import Path as P
from ruamel.yaml import YAML, YAMLError
import tkinter.font as tkFont
import configparser
from Assets.modules import requests
import zipfile
import shutil
import threading
import copy
import subprocess
import ctypes as ct
import platform

# Directories
TEMPLATES = P('./Templates')
LOCAL = P('./Templates/Localizations')
ASSETS = P('./Assets')
ICON = P('./Assets/icon.png')

def escape_special_characters(text):
    # Convert non-string text to string
    if not isinstance(text, str):
        text = str(text)
    special_characters = r"[{}\@#\$%\^&\*\(\)\+=<>\|\[\\\];'\",\./\?・]+"
    # Use regex to find sequences of special characters and wrap them in single quotes
    escaped_text = re.sub(special_characters, lambda match: "'" + match.group(0) + "'", text)
    return escaped_text

def escape_grapheme(grapheme):
        # Check if the first character is a special character that might require quoting
        if grapheme[0] in r"[{}\@#\$%\^&\*\(\)\+=<>\|\[\\\];'\",\./\?・]+":
            return f'"{grapheme}"'
        if re.search(r"\b(true|false|yes|no|on|off)\b", grapheme, re.IGNORECASE):
            return f'"{grapheme}"'
        return grapheme

class Dictionary(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Initialize the sv_ttk theme
        sv_ttk.set_theme("dark")
        config = configparser.ConfigParser()
        config.read('settings.ini')
        selected_theme = config.get('Settings', 'theme', fallback='Dark')
        selected_accent = config.get('Settings', 'accent', fallback='Electric Blue')
        self.theme_var = tk.StringVar(value=selected_theme)
        self.accent_var = tk.StringVar(value=selected_accent)
        selected_local = config.get('Settings', 'localization', fallback='English')
        self.localization_var = tk.StringVar(value=selected_local)
        current_local = config.get('Settings', 'current_local', fallback='English')
        self.local_var = tk.StringVar(value=current_local)
        self.current_version = "v0.6.3"

        # Set window title
        self.base_title = "OpenUTAU Dictionary Editor"
        self.title(self.base_title)
        self.current_filename = None
        self.file_modified = False
        self.localizable_widgets = {}
        
        # Template folder directory
        self.Templates = self.read_template_directory()
        self.config_file = "settings.ini"
        self.load_last_theme()

        # Dictionary to hold the data
        self.dictionary = {}
        self.comments = {}
        self.localization = {}
        self.symbols = {}
        self.undo_stack = []
        self.redo_stack = []
        self.copy_stack = []

        # Fonts
        self.tree_font = tkFont.Font(family="Helvetica", size=10, weight="normal")
        self.tree_font_b = tkFont.Font(family="Helvetica", size=10, weight="bold")
        self.font = tkFont.Font(family="Helvetica", size=10, weight="normal")
        self.font_b = tkFont.Font(family="Helvetica", size=10, weight="bold")
        
        self.template_var = tk.StringVar(value="Custom Template")
        self.entries_window = None
        self.text_widget = None
        self.replace_window = None
        self.drag_window = None
        self.symbol_editor_window = None
        self.remove_numbered_accents_var = tk.BooleanVar()
        self.remove_numbered_accents_var.set(False)  # Default is off
        self.lowercase_phonemes_var = tk.BooleanVar()
        self.lowercase_phonemes_var.set(False)  # Default is off
        self.current_order = [] # To store the manual order of entries
        self.icon()
        self.create_widgets()
        self.init_localization()

        # Start update check in a non-blocking way
        threading.Thread(target=self.bg_updates, daemon=True).start()
    
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
            messagebox.showerror("Update Error", f"Could not check for updates: {str(e)}")
    
    def icon(self, window=None):
        if window is None:
            window = self
        img = tk.PhotoImage(file=ICON)
        window.tk.call('wm', 'iconphoto', window._w, img)

    def change_font_size(self, delta):
        for font in [self.tree_font, self.tree_font_b]:
            current_size = font['size']
            new_size = max(10, current_size + delta)
            font.configure(size=new_size)
    
    # Directory for the YAML Templates via templae.ini
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
            ("Seance", "Dark"): "seance_dark"
        }
        # Apply the theme using sv_ttk
        theme_key = (accent_name, theme_name)
        if theme_key in theme_map:
            ttk.Style().theme_use(theme_map[theme_key])
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
                ("Seance", "Dark"): "seance_dark"
            }
            # Apply the theme using sv_ttk
            theme_key = (accent_name, theme_name)
            if theme_key in theme_map:
                ttk.Style().theme_use(theme_map[theme_key])
        except (configparser.NoSectionError, configparser.NoOptionError):
            sv_ttk.set_theme("dark")
    
    def load_cmudict(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not filepath:
            messagebox.showinfo("No File", "No file was selected.")
            return
        if filepath:
            self.current_filename = filepath
            self.file_modified = False  # Reset modification status
            self.update_title()
            self.current_order = list(self.dictionary.keys())

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            try:
                with open(filepath, 'r', encoding='ANSI') as file:
                    lines = file.readlines()
            except Exception as e:
                messagebox.showerror("Error", f"Error occurred while reading file with alternate encoding: {e}")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred while reading file: {e}")
            return

        dictionary = {}
        comments = []  # Store comments here if needed
        error_occurred = False
        for line in lines:
            try:
                if line.strip().startswith(';;;'):
                    comments.append(line.strip()[3:]) 
                    continue

                parts = line.strip().split('  ')  # Two spaces separate the key and values
                if len(parts) == 2:
                    grapheme, phonemes = parts[0], parts[1].split()
                    dictionary[grapheme] = phonemes
                else:
                    raise ValueError(f"Invalid format in line: {line.strip()}")
            except Exception as e:
                messagebox.showerror("Error", f"Error occurred while processing line '{line.strip()}'")
                error_occurred = True
                break

        if not error_occurred:
            self.dictionary = dictionary  # Update the main dictionary only if no errors occurred
            self.comments = comments
            self.update_entries_window()

    def remove_numbered_accents(self, phonemes):
        return [phoneme[:-1] if phoneme[-1].isdigit() else phoneme for phoneme in phonemes]

    def load_yaml_file(self):
        filepath = filedialog.askopenfilename(title="Open YAML File", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
        if not filepath:
            messagebox.showinfo("No File", "No file was selected.")
            return
        # Handle file opening to update title
        if filepath:
            self.current_filename = filepath
            self.file_modified = False  # Reset modification status
            self.update_title()
            self.current_order = list(self.dictionary.keys())

        yaml = YAML(typ='safe')
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = yaml.load(file)
                if data is None:
                    raise ValueError("The YAML file is empty or has an incorrect format.")
        except YAMLError as ye:
            messagebox.showerror("YAML Syntax Error", f"An error occurred while parsing the YAML file: {str(ye)}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading the YAML file: {str(e)}")
            return

        entries = []
        if 'entries' in data and isinstance(data['entries'], list):
            entries = data['entries']
        else:
            # Attempt to collect entries as a list of entries
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'grapheme' in item and 'phonemes' in item:
                        entries.append(item)
            elif isinstance(data, dict):
                if 'grapheme' in data and 'phonemes' in data:
                    entries.append(data)

        if not isinstance(entries, list):
            messagebox.showerror("Error", "The 'entries' key must be associated with a list.")
            return

        self.dictionary = {}
        self.data_list = []  # Initialize data_list

        if 'symbols' in data and isinstance(data['symbols'], list):
            symbols = data['symbols']
        else:
            messagebox.showerror("Error", "The 'symbols' key must be associated with a list.")
            return
        
        self.symbols = {}
        self.symbols_list = []  # Initialize symbols_list

        for item in symbols:
            if not isinstance(item, dict):
                messagebox.showerror("Error", "Entry format incorrect. Each entry must be a dictionary.")
                return
            symbol = item.get('symbol')
            type_ = item.get('type')
            if symbol is None or type_ is None:
                messagebox.showerror("Error", "Symbol entry is incomplete.")
                return
            if not isinstance(type_, str):  # Change to check if type is a string
                messagebox.showerror("Error", "Type must be a string representing the category.")
                return
            self.symbols[symbol] = [type_]  # Store type in a list for compatibility with other code parts
            # Append the loaded data to symbols_list
            self.symbols_list.append({'symbol': symbol, 'type': [type_]})

        for item in entries:
            if not isinstance(item, dict):
                messagebox.showerror("Error", "Entry format incorrect. Each entry must be a dictionary.")
                return
            grapheme = item.get('grapheme')
            phonemes = item.get('phonemes', [])
            if grapheme is None or not isinstance(phonemes, list):
                messagebox.showerror("Error", "Each entry must have a 'grapheme' key and a list of 'phonemes'.")
                return
            self.dictionary[grapheme] = phonemes
            # Append the loaded data to data_list
            self.data_list.append({'grapheme': grapheme, 'phonemes': phonemes})
        self.update_entries_window()

    def merge_yaml_files(self):
        filepaths = filedialog.askopenfilenames(title="Open YAML Files", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
        if not filepaths:
            messagebox.showinfo("No File", "No files were selected.")
            return
        
        yaml = YAML(typ='safe')

        for filepath in filepaths:
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = yaml.load(file)
                    if data is None:
                        raise ValueError("The YAML file is empty or has an incorrect format.")

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
                            messagebox.showerror(
                                "Error",
                                "Entry format incorrect in file: {}. Each entry must be a dictionary.".format(filepath)
                            )
                            continue

                        grapheme = item.get('grapheme')
                        phonemes = item.get('phonemes', [])
                        if grapheme is None or not isinstance(phonemes, list):
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
                messagebox.showerror("YAML Syntax Error", f"An error occurred while parsing the YAML file {filepath}: {str(ye)}")
                continue
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while reading the YAML file {filepath}: {str(e)}")
                continue

        self.update_entries_window()
    
    def open_symbol_editor(self):
        if self.symbol_editor_window is None or not self.symbol_editor_window.winfo_exists():
            self.symbol_editor_window = tk.Toplevel(self)
            self.symbol_editor_window.title("Symbols Viewer")
            self.symbol_editor_window.protocol("WM_DELETE_WINDOW")
            self.icon(self.symbol_editor_window)

            # Create a Frame for the search bar
            search_bar_frame = ttk.Frame(self.symbol_editor_window, style='Card.TFrame')
            search_bar_frame.pack(fill=tk.X, padx=15, pady=10)
            search_button = ttk.Button(search_bar_frame, text="Search:", style='Accent.TButton', command=self.filter_symbols_treeview)
            search_button.pack(side=tk.LEFT, padx=(10), pady=10)
            self.localizable_widgets['search'] = search_button
            self.search_var = tk.StringVar()
            self.search_var.trace("w", lambda name, index, mode, sv=self.search_var: self.filter_symbols_treeview())
            search_entry = ttk.Entry(search_bar_frame, textvariable=self.search_var)
            search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

            # Create a Frame to hold the Treeview and the Scrollbar
            treeview_frame = tk.Frame(self.symbol_editor_window)
            treeview_frame.pack(fill=tk.BOTH, expand=True)

            # Create the Treeview
            self.symbol_treeview = ttk.Treeview(treeview_frame, columns=('Symbol', 'Type'), show='headings', height=16)
            self.symbol_treeview.heading('Symbol', text='Symbol')
            self.symbol_treeview.heading('Type', text='Type')
            self.symbol_treeview.column('Symbol', width=120, anchor='w')
            self.symbol_treeview.column('Type', width=180, anchor='w')
            self.symbol_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15,0))

            # Create and pack the Scrollbar
            treeview_scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.symbol_treeview.yview)
            treeview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(5))
            self.symbol_treeview.configure(yscrollcommand=treeview_scrollbar.set)
            
            # Keyboard entries
            self.symbol_treeview.bind("<Escape>", lambda event: self.close())

            # Buttons for saving or discarding changes
            action_button_frame = tk.Frame(self.symbol_editor_window)
            action_button_frame.pack(fill=tk.X, expand=False)
            refresh_button = ttk.Button(action_button_frame, text="Refresh", command=self.refresh_treeview_symbols)
            refresh_button.pack(side=tk.RIGHT, padx=5, pady=10)
            self.localizable_widgets['refresh'] = refresh_button
            close_button = ttk.Button(action_button_frame, text="Close", command=self.close_sym)
            close_button.pack(side=tk.RIGHT, padx=5, pady=10)
            self.localizable_widgets['close'] = close_button
            ttk.Button(action_button_frame, text="-", style='Accent.TButton', command=lambda: self.change_font_size(-1)).pack(side="left", padx=(15,5), pady=10)
            ttk.Button(action_button_frame, text="+", style='Accent.TButton', command=lambda: self.change_font_size(1)).pack(side="left", padx=5, pady=10)
        self.refresh_treeview_symbols()
        if self.symbol_editor_window.winfo_exists():
            self.apply_localization()

    def add_manual_entry(self):
        word = self.word_entry.get().strip()
        phonemes = self.phoneme_entry.get().strip()
        if word and phonemes:
            if not self.entries_window or not self.entries_window.winfo_exists():
                self.update_entries_window()
            self.add_entry_treeview(word, phonemes.split())
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
        else:
            messagebox.showinfo("Error", "Please provide both word and phonemes for the entry.")

    def delete_manual_entry(self):
        selected_items = self.viewer_tree.selection()
        for item_id in selected_items:
            item_data = self.viewer_tree.item(item_id, 'values')
            if item_data:
                grapheme = item_data[1]
                if grapheme in self.dictionary:
                    del self.dictionary[grapheme]  # Delete the entry from the dictionary
                    self.viewer_tree.delete(item_id)  # Remove the item from the treeview
                    self.word_entry.delete(0, tk.END)
                    self.phoneme_entry.delete(0, tk.END)
                else:
                    messagebox.showinfo("Notice", f"Grapheme: {grapheme} not found in dictionary.")
            else:
                messagebox.showinfo("Notice", f"No data found for item ID {item_id}.")

    def delete_all_entries(self):
        if not self.dictionary:
            messagebox.showinfo("Info", "No entries to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete all entries?"):
            self.dictionary.clear()
            self.viewer_tree.delete(*self.viewer_tree.get_children())
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
            self.update_entries_window()
    
    def delete_selected_entries(self):
        selected_items = self.viewer_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "No entries selected.")
            return

        # Delete from the dictionary if you are syncing it with the tree view
        for item in selected_items:
            item_values = self.viewer_tree.item(item, 'values')
            if item_values:
                key = item_values[1]  # Assuming the first column in tree view is the key for the dictionary
                if key in self.dictionary:
                    del self.dictionary[key]
        # Delete from the tree view
        self.viewer_tree.delete(*selected_items)
        self.word_entry.delete(0, tk.END)
        self.phoneme_entry.delete(0, tk.END)
        self.update_entries_window()
    
    def update_entries_window(self):
        if self.entries_window is None or not self.entries_window.winfo_exists():
            self.entries_window = tk.Toplevel(self)
            self.entries_window.title("Entries Viewer")
            self.entries_window.protocol("WM_DELETE_WINDOW", self.close)
            self.save_state_before_change()
            self.icon(self.entries_window)

            # Create a Frame for the search bar
            search_frame = ttk.Frame(self.entries_window, style='Card.TFrame')
            search_frame.pack(fill=tk.X, padx=15, pady=10)
            search_label = ttk.Button(search_frame, text="Search:", style='Accent.TButton', command=self.filter_treeview)
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
            self.viewer_tree = ttk.Treeview(frame, columns=('Index', 'Grapheme', 'Phonemes'), show='headings', height=18)
            self.viewer_tree.heading('Index', text='Index')
            self.viewer_tree.heading('Grapheme', text='Grapheme')
            self.viewer_tree.heading('Phonemes', text='Phonemes')
            self.viewer_tree.column('Index', width=50, anchor='center')
            self.viewer_tree.column('Grapheme', width=180, anchor='w')
            self.viewer_tree.column('Phonemes', width=240, anchor='w')
            self.viewer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15,0))

            # Create and pack the Scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.viewer_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(5))
            self.viewer_tree.configure(yscrollcommand=scrollbar.set)
            
            # deselect
            self.viewer_tree.bind("<Button-2>", self.deselect_entry)
            self.viewer_tree.bind("<Button-3>", self.deselect_entry)
            # select
            self.viewer_tree.bind("<<TreeviewSelect>>", self.on_tree_selection)
            self.entries_window.bind("<Control-a>", lambda event: self.select_all_entries())
            self.entries_window.bind("<Command-a>", lambda event: self.select_all_entries())
            # mouse drag
            self.viewer_tree.bind("<ButtonPress-1>", self.start_drag)
            self.viewer_tree.bind("<B1-Motion>", self.on_drag)
            self.viewer_tree.bind("<ButtonRelease-1>", self.stop_drag)
            # keyboard entries
            self.viewer_tree.bind("<Delete>", lambda event: self.delete_manual_entry())
            self.entries_window.bind("<Escape>", lambda event: self.close())
            os_name = platform.system()
            if os_name == "Windows":
                # Windows key bindings
                self.entries_window.bind('<Control-z>', lambda event: self.undo())
                self.entries_window.bind('<Control-y>', lambda event: self.redo())
                self.entries_window.bind("<Control-c>", lambda event: self.copy_entry())
                self.entries_window.bind("<Control-x>", lambda event: self.cut_entry())
                self.entries_window.bind("<Control-v>", lambda event: self.paste_entry())
            elif os_name == "Darwin":
                # macOS key bindings (uses Command key)
                self.entries_window.bind('<Command-z>', lambda event: self.undo())
                self.entries_window.bind('<Command-y>', lambda event: self.redo())
                self.entries_window.bind("<Command-c>", lambda event: self.copy_entry())
                self.entries_window.bind("<Command-x>", lambda event: self.cut_entry())
                self.entries_window.bind("<Command-v>", lambda event: self.paste_entry())
            else:
                self.entries_window.bind('<Control-z>', lambda event: self.undo())
                self.entries_window.bind('<Control-y>', lambda event: self.redo())
                self.entries_window.bind("<Control-c>", lambda event: self.copy_entry())
                self.entries_window.bind("<Control-x>", lambda event: self.cut_entry())
                self.entries_window.bind("<Control-v>", lambda event: self.paste_entry())
            # Buttons for saving or discarding changes
            button_frame = tk.Frame(self.entries_window)
            button_frame.pack(fill=tk.X, expand=False)
            clear = ttk.Button(button_frame, text="Clear all entries", style='Accent.TButton', command=self.delete_all_entries)
            clear.pack(side=tk.RIGHT, padx=(5,25), pady=10)
            self.localizable_widgets['clear_all'] = clear
            ref = ttk.Button(button_frame, text="Refresh", command=self.update_entries_window)
            ref.pack(side=tk.RIGHT, padx=5, pady=10)
            self.localizable_widgets['refresh'] = ref
            close = ttk.Button(button_frame, text="Close", command=self.close)
            close.pack(side=tk.RIGHT, padx=5, pady=10)
            self.localizable_widgets['close'] = close
            ttk.Button(button_frame, text="-", style='Accent.TButton', command=lambda: self.change_font_size(-1)).pack(side="left", padx=(15,5), pady=10)
            ttk.Button(button_frame, text="+", style='Accent.TButton', command=lambda: self.change_font_size(1)).pack(side="left", padx=5, pady=10)
        self.refresh_treeview()
        if self.entries_window.winfo_exists():
            self.apply_localization()
    
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
            self.drag_window.geometry(f"+{event.x_root}+{event.y_root}")
            self.autoscroll(event)

    def create_drag_window(self, event):
        if not hasattr(self, 'drag_window') or not self.drag_window:
            self.drag_window = tk.Toplevel(self)
            self.drag_window.overrideredirect(True)
            self.drag_window.attributes("-alpha", 0.8)
            label = tk.Label(self.drag_window, text="Aesthetic drag", bg='#FFD700', fg='#000000', font=("Helvetica", 8, "bold"))
            label.pack(ipadx=3, ipady=3, expand=True)
            self.localizable_widgets['drag'] = label
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
                # Perform your drag logic here
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
            self.replace_window.title("Regex Replace")
            self.icon(self.replace_window)
            self.save_state_before_change()

            reg_frame = ttk.Frame(self.replace_window, style='Card.TFrame')
            reg_frame.pack(fill=tk.X, padx=10, pady=10)
            reg_frame.grid_columnconfigure(0, weight=1)
            reg_frame.grid_columnconfigure(1, weight=1)
            
            # Fields for entering regex pattern and replacement text
            reg_pat = ttk.Label(reg_frame, text="Regex Pattern:")
            reg_pat.grid(row=0, column=0, padx=10, pady=20)
            self.localizable_widgets['reg_pattern'] = reg_pat
            regex_var = tk.StringVar()
            regex_entry = ttk.Entry(reg_frame, textvariable=regex_var, width=30)
            regex_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

            reg_rep = ttk.Label(reg_frame, text="Replacement:")
            reg_rep.grid(row=1, column=0, padx=10, pady=5)
            self.localizable_widgets['replacement'] = reg_rep
            replace_var = tk.StringVar()
            replace_entry = ttk.Entry(reg_frame, textvariable=replace_var, width=30)
            replace_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

            # Radio buttons to select target (graphemes or phonemes)
            target_var = tk.StringVar(value="Phonemes")
            ttk.Radiobutton(reg_frame, text="Graphemes", variable=target_var, value="Graphemes").grid(row=2, column=0, padx=10, pady=(20, 5), sticky="w")
            ttk.Radiobutton(reg_frame, text="Phonemes", variable=target_var, value="Phonemes").grid(row=2, column=1, padx=10, pady=(20, 5), sticky="w")

            # Button to execute the replace operation
            apply_button = ttk.Button(reg_frame, text="Replace", style="Accent.TButton", command=lambda: apply_replace())
            apply_button.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
            self.localizable_widgets['apply'] = apply_button

            # Find button to highlight matching entries
            find_button = ttk.Button(reg_frame, text="Find", command=lambda: self.find_matches(regex_var.get(), target_var.get()))
            find_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
            self.localizable_widgets['find'] = find_button

        if self.replace_window.winfo_exists():
            self.apply_localization()

        def apply_replace():
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
            for item in self.viewer_tree.get_children():
                item_values = self.viewer_tree.item(item, "values")
                if target == "Graphemes":
                    # Direct replacement for graphemes
                    new_grapheme = compiled_pattern.sub(replacement, item_values[1])
                    if new_grapheme != item_values[1]:
                        self.viewer_tree.item(item, values=(new_grapheme, item_values[2]))
                        if item_values[1] in self.dictionary:
                            self.dictionary[new_grapheme] = self.dictionary.pop(item_values[1])
                        items_modified += 1
                elif target == "Phonemes":
                    # Handle phoneme list, considering sequences like 'ax, r'
                    phonemes_string = item_values[2].strip()
                    # Perform regex replacement directly on the whole phoneme string
                    modified_phoneme_string = compiled_pattern.sub(replacement, phonemes_string)
                    if modified_phoneme_string != phonemes_string:
                        # Updating tree and dictionary
                        self.viewer_tree.item(item, values=(item_values[1], modified_phoneme_string))
                        # Update dictionary: Split to list, removing extra spaces
                        new_phoneme_list = [phoneme.strip() for phoneme in modified_phoneme_string.split(',')]
                        self.dictionary[item_values[1]] = new_phoneme_list
                        items_modified += 1
            self.refresh_treeview()
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
            if self.search_var.get():
                self.filter_treeview()
            self.replace_window.destroy()
        self.apply_localization()

    def find_matches(self, pattern, target):
        items_to_highlight = []
        for item in self.viewer_tree.get_children():
            item_values = self.viewer_tree.item(item, "values")
            if target == "Graphemes" and re.search(pattern, item_values[1]):
                items_to_highlight.append(item)
            elif target == "Phonemes":
                phoneme_string = " ".join(item_values[2].split())
                if re.search(pattern, phoneme_string):
                    items_to_highlight.append(item)
        # Clear the current selection to ensure only new results are highlighted
        self.viewer_tree.selection_remove(self.viewer_tree.selection())
        # Set the selection to the items found
        self.viewer_tree.selection_set(items_to_highlight)
    
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
                response = messagebox.askyesno("Notice", "There are entries in the viewer. Closing this window will clear them all. Are you sure you want to proceed?")
                if response:
                    self.title(self.base_title)
                    self.viewer_tree.delete(*self.viewer_tree.get_children())
                    self.update_entries_window()
                    self.entries_window.destroy()
                    self.word_entry.delete(0, tk.END)
                    self.phoneme_entry.delete(0, tk.END)
                    self.dictionary.clear()
                else:
                    return
        else:
            return
    
    def close_sym(self):
        self.symbol_editor_window.destroy()
              
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
            item_id = self.symbol_treeview.insert('', 'end', values=(symbol, type_list), tags=('normal',))
            # Check if this was the previously selected symbol
            if symbol == selected_symbol:
                new_selection_id = item_id

        # If there was a previously selected symbol, reselect its new corresponding item ID
        if new_selection_id:
            self.symbol_treeview.selection_set(new_selection_id)
            self.symbol_treeview.item(new_selection_id, tags=('selected',))
            self.symbol_treeview.see(new_selection_id) 
    
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
            messagebox.showinfo("Undo", "No more actions to undo.")

    def redo(self):
        if self.redo_stack:
            current_state = copy.deepcopy(self.dictionary)
            self.undo_stack.append(current_state)  # Save current state to undo stack before redoing

            self.dictionary = self.redo_stack.pop()
            self.refresh_treeview()
        else:
            messagebox.showinfo("Redo", "No more actions to redo.")
    
    def copy_entry(self):
        selected_items = self.viewer_tree.selection()
        if selected_items:
            # Clear previous copies if you want to copy new entries only
            self.copy_stack.clear()

            # Iterate over all selected items to copy their data
            for selected_id in selected_items:
                item = self.viewer_tree.item(selected_id)
                values = item['values']
                if len(values) >= 2:
                    grapheme = values[1]
                    phonemes = values[2].split(', ')
                    # Create a dictionary from each selected entry
                    entry_dict = {
                        'grapheme': grapheme,
                        'phonemes': phonemes
                    }
                    # Append this dictionary to the copy_stack for later use
                    self.copy_stack.append(entry_dict)
        else:
            messagebox.showinfo("Copy", "No entry selected.")

    def cut_entry(self):
        selected_items = self.viewer_tree.selection()
        if selected_items:
            self.copy_entry()  # Copy entry first
            self.delete_selected_entries()
        else:
            messagebox.showinfo("Cut", "No entry selected.")

    def paste_entry(self):
        if self.copy_stack:
            selected = self.viewer_tree.selection()
            insert_index = self.viewer_tree.index(selected[-1]) + 1 if selected else 'end'

            for entry in self.copy_stack:  # Loop through all copied entries
                if 'grapheme' in entry and 'phonemes' in entry:
                    grapheme = entry['grapheme']
                    phonemes = entry['phonemes']
                    original_grapheme = grapheme
                    count = 1
                    
                    # Extract the existing count from the grapheme (if any)
                    match = re.match(r'^(.*)\((\d+)\)$', original_grapheme)
                    if match:
                        original_grapheme, count = match.groups()
                        count = int(count) + 1
                    
                    while grapheme in self.dictionary:
                        grapheme = f"{original_grapheme}({count})"
                        count += 1

                    # Use the helper function to add or update the entry
                    self.add_entry_treeview(new_word=grapheme, new_phonemes=phonemes, insert_index=insert_index)
                    
                    # Update the insert index for sequential pasting
                    if insert_index != 'end':
                        insert_index += 1
                else:
                    messagebox.showinfo("Error", "Clipboard data is invalid.")
        else:
            messagebox.showinfo("Paste", "Clipboard is empty.")

    def refresh_treeview(self):
        # Setup tag configurations for normal and bold fonts
        self.viewer_tree.tag_configure('normal', font=self.tree_font)
        self.viewer_tree.tag_configure('selected', font=self.tree_font_b)
        # Capture the grapheme of the currently selected item before clearing entries
        selected = self.viewer_tree.selection()
        selected_grapheme = None
        if selected:
            selected_item_id = selected[0]
            selected_item_values = self.viewer_tree.item(selected_item_id, "values")
            selected_grapheme = selected_item_values[1] if selected_item_values else None
        
        # Disable the treeview update during data loading
        self.viewer_tree.configure(displaycolumns=())

        # Clear all current entries from the treeview
        self.viewer_tree.delete(*self.viewer_tree.get_children())

        # Insert new entries into the treeview
        new_selection_id = None
        items = []
        for index, (grapheme, phonemes) in enumerate(self.dictionary.items(), start=1):
            if self.lowercase_phonemes_var.get():
                phonemes = [phoneme.lower() for phoneme in phonemes]
            if self.remove_numbered_accents_var.get():
                phonemes = self.remove_numbered_accents(phonemes)
            escaped_phonemes = ', '.join(escape_special_characters(str(phoneme)) for phoneme in phonemes)
            item_id = self.viewer_tree.insert('', 'end', values=(index, grapheme, escaped_phonemes), tags=('normal',))
            # Check if this was the previously selected grapheme
            if grapheme == selected_grapheme:
                new_selection_id = item_id
        
        # Bulk insert for performance
        for item in items:
            iid = self.viewer_tree.insert('', 'end', values=item, tags=('normal',))
            if item == new_selection_id:
                new_selection_id = iid
        
        # Re-enable the treeview
        self.viewer_tree.configure(displaycolumns="#all")

        # If there was a previously selected grapheme, reselect its new corresponding item ID
        if new_selection_id:
            self.viewer_tree.selection_set(new_selection_id)
            self.viewer_tree.item(new_selection_id, tags=('selected',))
            self.viewer_tree.see(new_selection_id) 

    def add_entry_treeview(self, new_word=None, new_phonemes=None, insert_index='end'):
        if new_word and new_phonemes:
            # Convert phonemes list to a string for display
            phoneme_display = ', '.join(new_phonemes)

            if insert_index == 'end' and self.viewer_tree.selection():
                insert_index = self.viewer_tree.index(self.viewer_tree.selection()[-1]) + 1  # Adjust to insert after the last selected item

            new_item_ids = [] 
            if new_word in self.dictionary:
                # Update the existing item's phonemes
                self.dictionary[new_word] = new_phonemes
                for idx, item in enumerate(self.viewer_tree.get_children()):
                    if self.viewer_tree.item(item, 'values')[1] == new_word:
                        self.viewer_tree.item(item, values=(idx + 1, new_word, phoneme_display))
                        break
            else:
                # Insert new entry if the grapheme does not exist
                if insert_index == 'end':
                    item_id = self.viewer_tree.insert('', 'end', values=(len(self.dictionary) + 1, new_word, phoneme_display), tags=('normal',))
                    new_item_ids.append(item_id)  # Add the item ID to the list
                    self.dictionary[new_word] = new_phonemes 
                else:
                    # Insert at the specific position
                    item_id = self.viewer_tree.insert('', insert_index, values=(insert_index, new_word, phoneme_display), tags=('normal',))
                    new_item_ids.append(item_id)
                    # Update dictionary and increment insert_index for possible next insertions
                    items = list(self.dictionary.items())
                    items.insert(insert_index, (new_word, new_phonemes))
                    self.dictionary.clear()
                    self.dictionary.update(items)
                    insert_index += 1

            # Select the newly added items
            self.viewer_tree.selection_set(new_item_ids) 
        self.refresh_treeview()

    def filter_treeview(self):
        search_text = self.search_var.get().replace(",", "")  # Remove commas from search text
        self.refresh_treeview()
        if search_text:
            for item in self.viewer_tree.get_children():
                item_values = self.viewer_tree.item(item, "values")
                if not (search_text in item_values[0].lower().replace(",", "") or
                        search_text in item_values[1].lower().replace(",", "") or
                        search_text in item_values[2].replace(",", "")):
                    self.viewer_tree.delete(item)
    
    def filter_symbols_treeview(self):
        search_symbol = self.search_var.get().lower().replace(",", "")
        self.refresh_treeview()
        if search_symbol:
            for item in self.symbol_treeview.get_children():
                item_sym_values = self.viewer_tree.item(item, "values")
                if not (search_symbol in item_sym_values[0].lower().replace(",", "") or
                        search_symbol in item_sym_values[1].lower().replace(",", "")):
                    self.viewer_tree.delete(item)

    def on_tree_selection(self, event):
        # Reset styles for all items
        for item in self.viewer_tree.get_children():
            self.viewer_tree.item(item, tags=('normal',))
        self.viewer_tree.tag_configure('normal', font=self.tree_font)

        # Apply bold font to selected items
        selected_items = self.viewer_tree.selection()
        for item in selected_items:
            self.viewer_tree.item(item, tags=('selected',))
        self.viewer_tree.tag_configure('selected', font=self.tree_font_b)
        
        # Handle multiple selections for displaying grapheme and phoneme data
        if selected_items:
            graphemes = []
            phoneme_lists = []
            for item_id in selected_items:
                item_data = self.viewer_tree.item(item_id, 'values')
                if item_data:
                    grapheme, phonemes = item_data[1], self.dictionary.get(item_data[1], [])
                    graphemes.append(grapheme)
                    phoneme_lists.append(phonemes)

            # Concatenate all graphemes for display
            graphemes_text = ', '.join(graphemes)

            # Formatting phonemes appropriately based on selection count
            if len(phoneme_lists) > 1:
                phonemes_text = '] ['.join(' '.join(str(phoneme) for phoneme in phoneme_list) for phoneme_list in phoneme_lists)
                phonemes_text = f"[{phonemes_text}]"
            else:
                phonemes_text = ' '.join(str(phoneme) for phoneme in phoneme_lists[0])

            self.word_entry.delete(0, tk.END)
            self.word_entry.insert(0, graphemes_text)

            self.phoneme_entry.delete(0, tk.END)
            self.phoneme_entry.insert(0, phonemes_text)
        
    def deselect_entry(self, event):
        # Check if there is currently a selection
        selected_items = self.viewer_tree.selection()
        if selected_items:
            self.viewer_tree.selection_remove(selected_items)

            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)

    def save_as_yaml(self):
        selected_template = self.template_var.get()
        # If "Current Template" is selected, ask the user to select a file to load and save.
        if not self.dictionary:
            messagebox.showinfo("Warning", "No entries to save. Please add entries before saving.")
            return

        if selected_template == "Current Template":
            template_path = filedialog.askopenfilename(title="Using the current YAML file as a template", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
            if not template_path:
                return
        else:
            # Define the base directory for templates and construct the file path
            data_folder = self.Templates
            template_path = os.path.join(data_folder, selected_template)
        
        # Read existing data from the template as text, ignoring the entries section
        existing_data_text = []
        entries_start = False
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if 'entries:' in line.strip():
                        entries_start = True
                        break
                    existing_data_text.append(line)

        # Prepare new entries as formatted strings
        self.clear_entries()
        new_entries_text = []
        # Ensure the order of entries in the dictionary matches the order in the TreeView
        for item in self.viewer_tree.get_children():
            item_values = self.viewer_tree.item(item, 'values')
            if len(item_values) >= 3:
                grapheme = item_values[1]
                phonemes = self.dictionary[grapheme]
                # Apply transformations such as lowercase and removing accents if needed
                if self.lowercase_phonemes_var.get():
                    phonemes = [phoneme.lower() for phoneme in phonemes]
                if self.remove_numbered_accents_var.get():
                    phonemes = self.remove_numbered_accents(phonemes)
                escaped_phonemes = [escape_special_characters(phoneme) for phoneme in phonemes]
                formatted_phonemes = ", ".join(f'{phoneme}' for phoneme in escaped_phonemes)
                grapheme = escape_grapheme(grapheme)
                entry_text = f"  - grapheme: {grapheme}\n    phonemes: [{formatted_phonemes}]\n"
                new_entries_text.append(entry_text)

        # Append the entries tag and new entries
        existing_data_text.append('entries:\n')
        existing_data_text.extend(new_entries_text)

        # Prompt user for output file path using a file dialog if not chosen already
        if selected_template == "Current Template":
            output_file_path = template_path
        else:
            output_file_path = filedialog.asksaveasfilename(title="Save YAML File", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])

        # Save changes if the user has selected a file path
        if output_file_path:
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.writelines(existing_data_text)
            messagebox.showinfo("Success", f"Dictionary saved to {output_file_path}.")
        else:
            messagebox.showinfo("Cancelled", "Save operation cancelled.")

    def save_as_ds_yaml(self):
        selected_template = self.template_var.get()
        # If "Current Template" is selected, ask the user to select a file to load and save.
        if not self.dictionary:
            messagebox.showinfo("Warning", "No entries to save. Please add entries before saving.")
            return

        if selected_template == "Current Template":
            template_path = filedialog.askopenfilename(title="Using the current YAML file as a template", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
            if not template_path:
                return
        else:
            # Define the base directory for templates and construct the file path
            data_folder = self.Templates
            template_path = os.path.join(data_folder, selected_template)
        
        # Read existing data from the template as text, ignoring the entries section
        existing_data_text = []
        entries_start = False
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if 'entries:' in line.strip():
                        entries_start = True
                        break
                    existing_data_text.append(line)

        # Prepare new entries as formatted strings
        self.clear_entries()
        new_entries_text = []
        # Ensure the order of entries in the dictionary matches the order in the TreeView
        for item in self.viewer_tree.get_children():
            item_values = self.viewer_tree.item(item, 'values')
            if len(item_values) >= 3:
                grapheme = item_values[1]
                phonemes = self.dictionary[grapheme]
                # Apply transformations such as lowercase and removing accents if needed
                if self.lowercase_phonemes_var.get():
                    phonemes = [phoneme.lower() for phoneme in phonemes]
                if self.remove_numbered_accents_var.get():
                    phonemes = self.remove_numbered_accents(phonemes)
                escaped_phonemes = [escape_special_characters(phoneme) for phoneme in phonemes]
                formatted_phonemes = ", ".join(f'{phoneme}' for phoneme in escaped_phonemes)
                entry_text = f"  - {{grapheme: \"{grapheme}\", phonemes: [{formatted_phonemes}]}}\n"
                new_entries_text.append(entry_text)

        # Append the entries tag and new entries
        existing_data_text.append('entries:\n')
        existing_data_text.extend(new_entries_text)

        # Prompt user for output file path using a file dialog if not chosen already
        if selected_template == "Current Template":
            output_file_path = template_path
        else:
            output_file_path = filedialog.asksaveasfilename(title="Save YAML File", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])

        # Save changes if the user has selected a file path
        if output_file_path:
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.writelines(existing_data_text)
            messagebox.showinfo("Success", f"Dictionary saved to {output_file_path}.")
        else:
            messagebox.showinfo("Cancelled", "Save operation cancelled.")
    
    def export_cmudict(self):
        if not self.dictionary:
            messagebox.showinfo("Warning", "No entries to save. Please add entries before saving.")
            return
        # Prompt user for output file path using a file dialog
        output_file_path = filedialog.asksaveasfilename(title="Save CMUDict File", defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])

        if not output_file_path:
            messagebox.showinfo("Cancelled", "Save operation cancelled.")
            return
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

        # Write entries to the selected file
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.writelines(entries_text)
        messagebox.showinfo("Success", f"Dictionary saved to {output_file_path}.")

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
            # List all files in the specified directory
            files = os.listdir(TEMPLATES)
            # Filter out files to include only .yaml files
            yaml_files = [file for file in files if file.endswith('.yaml')]
            options = ["Current Template"] + yaml_files
            combobox['values'] = options
            # Set default selection to the first item
            self.template_var.set(options[0])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read the directory: {str(e)}")
    
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
    
    def create_widgets(self):
        # Main notebook to contain tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        self.notebook.grid_columnconfigure(0, weight=1)
        self.notebook.grid_rowconfigure(0, weight=1)
        
        # Create the first tab which will contain existing widgets
        self.options_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.options_tab, text='Entry Editor')
        self.localizable_widgets['tab1'] = self.notebook 
        self.options_tab.grid_columnconfigure(0, weight=1)
        self.options_tab.grid_rowconfigure(0, weight=1)

        # Create a second tab for future additions
        self.additional_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.additional_tab, text='Settings')
        self.localizable_widgets['tab2'] = self.additional_tab 
        self.additional_tab.grid_columnconfigure(0, weight=1)
        self.additional_tab.grid_rowconfigure(0, weight=1)

        self.main_editor_widgets()
        self.settings_widgets()
    
    def main_editor_widgets(self):
        # Options Frame setup
        options_frame = ttk.LabelFrame(self.options_tab, text="Entry options")
        options_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=2)
        self.localizable_widgets['entry_option'] = options_frame 

        # Populate the Options frame
        self.template_var = tk.StringVar()
        template_label = ttk.Label(options_frame, text="Select Template:")  # Default text
        template_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.localizable_widgets['select_template'] = template_label

        template_combobox = ttk.Combobox(options_frame, textvariable=self.template_var, state="readonly")
        template_combobox.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.update_template_combobox(template_combobox)

        # Add localizable Checkbuttons
        remove_accents_cb = ttk.Checkbutton(options_frame, text="Remove Number Accents", variable=self.remove_numbered_accents_var)
        remove_accents_cb.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['remove_accents'] = remove_accents_cb

        lowercase_phonemes_cb = ttk.Checkbutton(options_frame, text="Make Phonemes Lowercase", variable=self.lowercase_phonemes_var)
        lowercase_phonemes_cb.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.localizable_widgets['lowercase_phonemes'] = lowercase_phonemes_cb

        edit_symbols = ttk.Button(options_frame, text="Edit Symbols", style='Accent.TButton', command=self.open_symbol_editor)
        edit_symbols.grid(row=3, column=1, padx=10, pady=(5,10), sticky="ew")
        self.localizable_widgets['edit_sym'] = edit_symbols
       
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
        self.word_entry.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.phoneme_entry = ttk.Entry(manual_frame)
        self.phoneme_entry.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        add_entry_button = ttk.Button(manual_frame, text="Add Entry", style='Accent.TButton', command=self.add_manual_entry)
        add_entry_button.grid(row=2, column=1, columnspan=1, padx=5, pady=10)
        self.localizable_widgets['add_entry'] = add_entry_button

        delete_entry_button = ttk.Button(manual_frame, text="Delete Entry", style='Accent.TButton', command=self.delete_manual_entry)
        delete_entry_button.grid(row=2, column=0, columnspan=1, padx=5, pady=10)
        self.localizable_widgets['delete_entry'] = delete_entry_button

        # Create frames for each set of buttons
        convert_frame = ttk.Frame(self)
        convert_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        convert_frame.columnconfigure(0, weight=1)
        convert_frame.columnconfigure(1, weight=1)
        load_frame = ttk.Frame(self)
        load_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        load_frame.columnconfigure(0, weight=1)
        load_frame.columnconfigure(1, weight=1)
        save_frame = ttk.Frame(self)
        save_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        cad_frame = ttk.Frame(self)
        cad_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        label_font = tkFont.Font(size=10)
        label_color = "gray"

        # Add buttons to each frame
        self.cmu = ttk.Button(convert_frame, text="Import CMUDict", command=self.load_cmudict)
        self.cmu.grid(column=1, row=0, padx=5, sticky="ew")
        self.localizable_widgets['convert_cmudict'] = self.cmu
        cmux = ttk.Button(convert_frame, text="Export CMUDict", command=self.export_cmudict)
        cmux.grid(column=0, row=0, padx=5, sticky="ew")
        self.localizable_widgets['export_cmudict'] = cmux
        ap_yaml = ttk.Button(load_frame, text= "Append YAML File", command=self.merge_yaml_files)
        ap_yaml.grid(column=0, row=0, padx=5, pady=5, sticky="ew")
        self.localizable_widgets['append_yaml'] = ap_yaml
        open_yaml = ttk.Button(load_frame, text= "Open YAML File", command=self.load_yaml_file)
        open_yaml.grid(column=1, row=0, padx=5, sticky="ew")
        self.localizable_widgets['open_yaml'] = open_yaml
        
        # For saving, you might want distinct actions for each button, so specify them if they differ
        ou_save = ttk.Button(save_frame, text="Save OU Dictionary", style='Accent.TButton', command=self.save_as_yaml)
        ou_save.pack(side=tk.LEFT, expand=True, fill="x", padx=(5), pady=(0,5))
        self.localizable_widgets['save_ou'] = ou_save
        ds_save = ttk.Button(save_frame, text="Save DS Dictionary", style='Accent.TButton', command=self.save_as_ds_yaml)
        ds_save.pack(side=tk.LEFT, expand=True, fill="x", padx=(5), pady=(0,5))
        self.localizable_widgets['save_ds'] = ds_save
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
        update_frame.columnconfigure(0, weight=1)
        update_frame.columnconfigure(1, weight=1)
        update_frame.columnconfigure(2, weight=1)
        update_frame.rowconfigure(0, weight=1)
        update_frame.rowconfigure(1, weight=1)
        update_frame.rowconfigure(2, weight=1)

        # Button to check for updates
        update_button = ttk.Button(update_frame, text="Check for Updates", style='Accent.TButton', command=self.check_for_updates)
        update_button.grid(row=1, column=1, padx=10, pady=20, sticky="ew",)
        self.localizable_widgets['update_b'] = update_button
        # Make sure the frame expands with the window
        update_frame.columnconfigure(0, weight=1)

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
        theme_select = ttk.Label(self.theming, text="Select Theme:")
        theme_select.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['def_theme'] = theme_select
        theme_options = ["Amaranth", "Amethyst", "Burnt Sienna", "Dandelion", "Denim", "Electric Blue", 
                         "Fern", "Lemon Ginger", "Lightning Yellow", "Mint", "Orange", "Pear", "Persian Red", 
                         "Pink", "Salmon", "Sapphire", "Sea Green", "Seance"]  # Theme options
        theme_combobox = ttk.Combobox(self.theming, textvariable=self.accent_var, values=theme_options, state="readonly")
        theme_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        theme_combobox.bind("<<ComboboxSelected>>", self.toggle_theme)

        # Radio button for light theme
        light_theme_button = ttk.Radiobutton(theme_frame, text="Light", value="Light", variable=self.theme_var, command=self.toggle_theme)
        light_theme_button.grid(row=1, column=0, pady=(0, 10))

        # Radio button for dark theme
        dark_theme_button = ttk.Radiobutton(theme_frame, text="Dark", value="Dark", variable=self.theme_var, command=self.toggle_theme)
        dark_theme_button.grid(row=1, column=1, pady=(0, 10))

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

        local_select = ttk.Label(self.save_loc, text="Select Localization:")
        local_select.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.localizable_widgets['select_local'] = local_select
        localization_combobox = ttk.Combobox(self.save_loc, textvariable=self.localization_var, state="readonly")
        localization_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        localization_combobox.bind("<<ComboboxSelected>>", self.localization_selected)
        self.update_localization_combobox(localization_combobox)
    
    def is_connected(self):
        # Check internet connection by trying to reach Google lmao
        try:
            requests.get("http://www.google.com", timeout=3)
            return True
        except requests.RequestException:
            return False
    
    def check_for_updates(self):
        if not self.is_connected():
            messagebox.showerror("Internet Error", "No internet connection. Please check your connection and try again.")
            return
        try:
            self.response = requests.get("https://api.github.com/repos/Cadlaxa/OpenUtau-Dictionary-Editor/releases/latest", timeout=5)
            self.response.raise_for_status()
            self.latest_release = self.response.json()
            self.latest_version_tag = self.latest_release['tag_name']
            self.latest_asset = self.latest_release['assets'][0]  # first asset is the zip file
            if self.latest_version_tag > self.current_version:
                if messagebox.askyesno("Update Available", f"Version {self.latest_version_tag} is available. Do you want to update now?"):
                    self.download_and_install_update(self.latest_asset['browser_download_url'])
            else:
                messagebox.showinfo("No Updates", "You are up to date!")
        except requests.RequestException as e:
            messagebox.showerror("Update Error", f"Could not check for updates: {str(e)}")

    def download_and_install_update(self, download_url):
        downloads_path = str(P("./Downloads"))
        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)

        local_zip_path = os.path.join(downloads_path, f"OU Dict Editor {self.latest_version_tag}.zip")
        temp_extraction_path = os.path.join(downloads_path, "temp_extract")  # Temporary extraction directory
        
        try:
            # Download the file
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(local_zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # Extract ZIP file using Python
            with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extraction_path)

            # Move the contents of the first directory in the extracted folder
            first_directory = next(os.walk(temp_extraction_path))[1][0]
            source_path = os.path.join(temp_extraction_path, first_directory)
            target_path = str(P('./OU DICTIONARY EDITOR'))
            
            if not os.path.exists(target_path):
                os.makedirs(target_path)

            for item in os.listdir(source_path):
                s = os.path.join(source_path, item)
                d = os.path.join(target_path, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            
            # Offer to open the directory
            if messagebox.askyesno("Open Directory", "Do you want to open the update directory?"):
                if os.name == 'nt':
                    os.startfile(target_path)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.Popen([opener, target_path])

            # Inform user about the restart
            messagebox.showinfo("Application Close", "The application will now close. Please move the downloaded file manually.")

            # Delete the temporary files and folders
            os.remove(local_zip_path)
            shutil.rmtree(temp_extraction_path)

            # Close application
            self.close_application()

        except requests.RequestException as e:
            messagebox.showerror("Download Error", f"Could not download the update: {str(e)}")
        except zipfile.BadZipFile:
            messagebox.showerror("Unzip Error", "The downloaded file was not a valid zip file.")
        except Exception as e:
            messagebox.showerror("Update Error", f"An error occurred during the update process: {str(e)}")

    def close_application(self):
        # This should safely close the application
        sys.exit()

    def restart_application(self):
        # Restarting the application
        os.execl(sys.executable, sys.executable, *sys.argv)
    
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
        current_local = self.local_var.get()

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
                if current_local in language_dict:
                    combobox.set(current_local)
                else:
                    combobox.set(sorted_languages[0])
                self.language_file_map = language_dict
            else:
                messagebox.showinfo("No Localizations Found", "No valid YAML files found in 'Localizations' subfolder.")
        else:
            messagebox.showinfo("No Localizations Found", "No 'Localizations' subfolder found or it is empty.")

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
                messagebox.showerror("Localization Error", f"Failed to load localization file: {str(e)}")
                self.localization = {}
        else:
            messagebox.showinfo("No Localizations Found", "No 'Localizations' subfolder found or it is empty.")
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
            messagebox.showinfo("Localization Error", "Selected language configuration not found.")

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
        if not hasattr(self, '.\Templates\Localizations\en_US.yaml'):
            yaml = YAML()
            with open('.\Templates\Localizations\en_US.yaml', 'r') as file:
                self.default_localization = yaml.load(file)
                
        if hasattr(self, 'localizable_widgets'):
            for key, widget in self.localizable_widgets.items():
                # Retrieve text from current localization or fall back to default localization
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
    
if __name__ == "__main__":
    app = Dictionary()
    app.mainloop()