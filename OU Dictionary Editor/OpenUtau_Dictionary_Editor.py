import tkinter as tk
from tkinter import filedialog, messagebox, ttk, BOTH
import sv_ttk
import os
from ruamel.yaml import YAML, YAMLError
import re
import tkinter.font as tkFont

# Directory for the YAML Templates
Templates = "OU Dictionary Editor\Templates"

def escape_special_characters(text):
    # Convert non-string text to string
    if not isinstance(text, str):
        text = str(text)
    special_characters = r"[{}\@#\$%\^&\*\(\)\+=<>\|\[\\\];'\",\./\?]+"
    # Use regex to find sequences of special characters and wrap them in single quotes
    escaped_text = re.sub(special_characters, lambda match: "'" + match.group(0) + "'", text)
    return escaped_text

def escape_grapheme(grapheme):
        # Check if the first character is a special character that might require quoting
        if grapheme[0] in r"[{}\@#\$%\^&\*\(\)\+=<>\|\[\\\];'\",\./\?]+":
            return f'"{grapheme}"'  # Return the grapheme enclosed in double quotes
        return grapheme
 
class Dictionary(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Initialize the sv_ttk theme
        sv_ttk.set_theme("dark")

        # Set window title
        self.base_title = "OpenUTAU Dictionary Editor"
        self.title(self.base_title)
        self.current_filename = None
        self.file_modified = False

        # Dictionary to hold the data
        self.dictionary = {}
        self.template_var = tk.StringVar(value="Custom Template")
        self.entries_window = None
        self.text_widget = None
        self.replace_window = None
        self.drag_window = None
        self.remove_numbered_accents_var = tk.BooleanVar()
        self.remove_numbered_accents_var.set(False)  # Default is off
        self.lowercase_phonemes_var = tk.BooleanVar()
        self.lowercase_phonemes_var.set(False)  # Default is off
        self.current_order = [] # To store the manual order of keys
        self.create_widgets()

    def update_title(self):
        if self.current_filename:
            self.title(f"OU DE (editing {self.current_filename})")
        else:
            self.title(self.base_title)
    
    def toggle_theme(self):
        if self.theme_var.get() == 1:  # switched to dark mode
            sv_ttk.set_theme("dark")
        else:  # switched back to light mode
            sv_ttk.set_theme("light")

    def load_cmudict(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not filepath:
            return  # Exit if no file is selected
        # Handle file opening to update tittle
        if filepath:
            self.current_filename = filepath
            self.file_modified = False  # Reset modification status
            self.update_title()
            self.current_order = list(self.dictionary.keys())
        try:
            with open(filepath, 'r') as file:
                lines = file.readlines()
        except Exception as e:
            messagebox.showerror("Error", f"Error occurred while reading file: {e}")
            return
        new_dictionary = {}  # Create a new dictionary to store the data
        error_occurred = False
        for line in lines:
            try:
                parts = line.strip().split('  ')  # Assumes two spaces separate the key and values
                if len(parts) == 2:
                    grapheme, phonemes = parts[0], parts[1].split()
                    new_dictionary[grapheme] = phonemes
                else:
                    raise ValueError(f"Invalid format in line: {line.strip()}")
            except Exception as e:
                messagebox.showerror("Error", f"Error occurred while processing line '{line.strip()}': {e}")
                error_occurred = True
                break
        if not error_occurred:
            self.dictionary = new_dictionary  # Update the main dictionary only if no errors occurred
            self.update_entries_window()
            messagebox.showinfo("Success", "Dictionary loaded successfully.")

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

        from ruamel.yaml import YAML, YAMLError
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

        if not isinstance(data, dict) or 'entries' not in data:
            messagebox.showerror("Error", "Invalid YAML format: No 'entries' key found or file structure is incorrect.")
            return

        entries = data['entries']
        if not isinstance(entries, list):
            messagebox.showerror("Error", "The 'entries' key must be associated with a list.")
            return

        self.dictionary = {}
        self.data_list = []  # Initialize data_list

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
        merged_entries = []

        for filepath in filepaths:
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = yaml.load(file)
                    if data is None:
                        raise ValueError("The YAML file is empty or has an incorrect format.")

                    if not isinstance(data, dict) or 'entries' not in data:
                        messagebox.showerror("Error", "Invalid YAML format: No 'entries' key found or file structure is incorrect in file: " + filepath)
                        continue

                    entries = data['entries']
                    if not isinstance(entries, list):
                        messagebox.showerror("Error", "The 'entries' key must be associated with a list in file: " + filepath)
                        continue

                    for item in entries:
                        if not isinstance(item, dict):
                            messagebox.showerror("Error", "Entry format incorrect in file: " + filepath + ". Each entry must be a dictionary.")
                            continue
                        grapheme = item.get('grapheme')
                        phonemes = item.get('phonemes', [])
                        if grapheme is None or not isinstance(phonemes, list):
                            messagebox.showerror("Error", "Each entry must have a 'grapheme' key and a list of 'phonemes' in file: " + filepath)
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

    def add_manual_entry(self):
        global yaml_loaded
        yaml_loaded = False
        word = self.word_entry.get().strip()
        phonemes = self.phoneme_entry.get().strip()
        if word and phonemes:
            self.dictionary[word] = phonemes.split()
            self.word_entry.delete(0, tk.END)
            self.phoneme_entry.delete(0, tk.END)
            self.update_entries_window()
        else:
            messagebox.showinfo("Error", "Please provide both word and phonemes to the entry.")

    def delete_manual_entry(self):
        selected_items = self.viewer_tree.selection()
        for item_id in selected_items:
            item_data = self.viewer_tree.item(item_id, 'values')
            if item_data:
                grapheme = item_data[0]
                if grapheme in self.dictionary:
                    del self.dictionary[grapheme]  # Delete the entry from the dictionary
                    self.viewer_tree.delete(item_id)  # Remove the item from the treeview
                else:
                    messagebox.showinfo("Notice", f"Grapheme {grapheme} not found in dictionary.")
            else:
                messagebox.showinfo("Notice", f"No data found for item ID {item_id}.")
        self.update_entries_window()  # Refresh the

    def delete_all_entries(self):
        if not self.dictionary:
            messagebox.showinfo("Info", "No entries to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete all entries?"):
            self.dictionary.clear()
            self.viewer_tree.delete(*self.viewer_tree.get_children())
            self.update_entries_window()
    
    def update_entries_window(self):
        if self.entries_window is None or not self.entries_window.winfo_exists():
            self.entries_window = tk.Toplevel(self)
            self.entries_window.title("Entries Viewer")
            self.entries_window.protocol("WM_DELETE_WINDOW", self.close)

            # Create a Frame for the search bar
            search_frame = tk.Frame(self.entries_window)
            search_frame.pack(fill=tk.X)
            search_label = ttk.Label(search_frame, text="Search:")
            search_label.pack(side=tk.LEFT, padx=5, pady=5)
            self.search_var = tk.StringVar()
            self.search_var.trace("w", lambda name, index, mode, sv=self.search_var: self.filter_treeview())
            search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
            search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
            ttk.Button(search_frame, text="Replace", style='Accent.TButton', command=self.regex_replace_dialog).pack(side=tk.LEFT, padx=5, pady=10)

            # Create a Frame to hold the Treeview and the Scrollbar
            frame = tk.Frame(self.entries_window)
            frame.pack(fill=tk.BOTH, expand=True)

            # Create the Treeview
            self.viewer_tree = ttk.Treeview(frame, columns=('Grapheme', 'Phonemes'), show='headings')
            self.viewer_tree.heading('Grapheme', text='Grapheme')
            self.viewer_tree.heading('Phonemes', text='Phonemes')
            self.viewer_tree.column('Grapheme', width=120, anchor='w')
            self.viewer_tree.column('Phonemes', width=180, anchor='w')
            self.viewer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Create and pack the Scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.viewer_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.viewer_tree.configure(yscrollcommand=scrollbar.set)
            
            # Bind the selection and drag events
            self.viewer_tree.bind("<<TreeviewSelect>>", self.on_tree_selection)
            self.viewer_tree.bind("<ButtonPress-1>", self.start_drag)
            self.viewer_tree.bind("<B1-Motion>", self.on_drag)
            self.viewer_tree.bind("<ButtonRelease-1>", self.stop_drag)

            # Buttons for saving or discarding changes
            button_frame = tk.Frame(self.entries_window)
            button_frame.pack(fill=tk.X, expand=False)
            ttk.Button(button_frame, text="Clear all entries", style='Accent.TButton', command=self.delete_all_entries).pack(side=tk.RIGHT, padx=5, pady=10)
            ttk.Button(button_frame, text="Refresh", command=self.update_entries_window).pack(side=tk.RIGHT, padx=5, pady=10)
            ttk.Button(button_frame, text="Close", command=self.close).pack(side=tk.RIGHT, padx=5, pady=10)
        self.refresh_treeview()

    def start_drag(self, event):
        # Initialize the drag_window if it doesn't already exist
        if not hasattr(self, 'drag_window') or not self.drag_window:
            self.drag_window = tk.Toplevel(self)
            self.drag_window.overrideredirect(True)
            self.drag_window.attributes("-alpha", 0.8)

            # Styling the label
            bg_color = '#FFD700'
            text_color = '#000000'
            font_style = ("Helvetica", 7, "bold")

            # Create a label with improved styling
            label = tk.Label(self.drag_window, text="Aesthetic drag", bg=bg_color, fg=text_color, font=font_style, padx=5, pady=3)
            label.pack(ipadx=3, ipady=3, expand=True)

            # Configuring the window with rounded corners
            self.drag_window.config(borderwidth=1, relief="solid")
            self.drag_window.wm_attributes("-topmost", True)
            self.drag_window.wm_attributes("-toolwindow", True) 

            # Apply rounded corners to the window
            self.drag_window.config(borderwidth=2, relief="solid")
            try:
                self.drag_window.wm_attributes("-alpha", 0.95)  # Windows OS
                self.drag_window.config(bg=bg_color)
                label.config(bg=bg_color)
            except Exception:
                # Fallback for other OS, as "-alpha" might not work on all systems
                self.drag_window.config(bg=bg_color)
                label.config(bg=bg_color)

        self.dragged_item = self.viewer_tree.identify_row(event.y)
        self.drag_window.geometry(f"+{event.x_root}+{event.y_root}")

    def on_drag(self, event):
        # Update the position of the drag window during the drag
        if hasattr(self, 'drag_window') and self.drag_window:
            self.drag_window.geometry(f"+{event.x_root}+{event.y_root}")
            self.drag_window.update_idletasks()  # Force the GUI to update

        # Check mouse position and scroll accordingly
        self.autoscroll(event)

    def autoscroll(self, event):
        treeview_height = self.viewer_tree.winfo_height()
        y_relative = event.y_root - self.viewer_tree.winfo_rooty()
        scroll_zone_size = 20

        if y_relative < scroll_zone_size:
            # Calculate scroll speed based on distance to edge
            speed = 1 - (y_relative / scroll_zone_size)
            self.viewer_tree.yview_scroll(int(-1 * speed), "units")
        elif y_relative > (treeview_height - scroll_zone_size):
            speed = 1 - ((treeview_height - y_relative) / scroll_zone_size)
            self.viewer_tree.yview_scroll(int(1 * speed), "units")

    def stop_drag(self, event):
        if hasattr(self, 'dragged_item') and self.dragged_item:
            # Identify the target item
            target_item = self.viewer_tree.identify_row(event.y)

            if target_item and self.dragged_item != target_item:
                # Calculate positions in the Treeview
                dragged_index = self.viewer_tree.index(self.dragged_item)
                target_index = self.viewer_tree.index(target_item)
                # Move the dragged item in the Treeview to its new position
                self.viewer_tree.move(self.dragged_item, '', target_index)
                # Extract data from the dragged item
                dragged_data = self.viewer_tree.item(self.dragged_item, 'values')
                dragged_grapheme = dragged_data[0]
                # Adjust dictionary for dragged item
                if dragged_grapheme in self.dictionary:
                    dragged_entry = self.dictionary.pop(dragged_grapheme)
                    new_keys = list(self.dictionary.keys())
                    new_keys.insert(target_index, dragged_grapheme)
                    new_dict = {}
                    for key in new_keys:
                        if key == dragged_grapheme:
                            new_dict[key] = dragged_entry
                        else:
                            new_dict[key] = self.dictionary[key]
                    self.dictionary = new_dict
                else:
                    messagebox.showinfo("Error", f"Grapheme {dragged_grapheme} not found in dictionary.")
            if hasattr(self, 'drag_window') and self.drag_window:
                self.drag_window.destroy()
                self.drag_window = None
            self.viewer_tree.selection_set(self.dragged_item)
            self.update_entries_window()
                
    def regex_replace_dialog(self):
        if self.replace_window is None or not self.replace_window.winfo_exists():
            self.replace_window = tk.Toplevel(self.entries_window)
            self.replace_window.title("Regex Replace")

            # Make sure all visual updates are processed
            self.replace_window.update_idletasks()

            # Make the window modal
            self.replace_window.grab_set()
            self.replace_window.transient(self.entries_window)

            # Fields for entering regex pattern and replacement text
            ttk.Label(self.replace_window, text="Regex Pattern:").grid(row=0, column=0, padx=10, pady=5)
            regex_var = tk.StringVar()
            regex_entry = ttk.Entry(self.replace_window, textvariable=regex_var)
            regex_entry.grid(row=0, column=1, padx=10, pady=5)

            ttk.Label(self.replace_window, text="Replacement:").grid(row=1, column=0, padx=10, pady=5)
            replace_var = tk.StringVar()
            replace_entry = ttk.Entry(self.replace_window, textvariable=replace_var)
            replace_entry.grid(row=1, column=1, padx=10, pady=5)

            # Radio buttons to select target (graphemes or phonemes)
            target_var = tk.StringVar(value="Phonemes")
            ttk.Radiobutton(self.replace_window, text="Graphemes", variable=target_var, value="Graphemes").grid(row=2, column=0, padx=10, pady=5, sticky="w")
            ttk.Radiobutton(self.replace_window, text="Phonemes", variable=target_var, value="Phonemes").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        # Button to execute the replace operation
        def apply_replace():
            pattern = regex_var.get()
            replacement = replace_var.get()
            target = target_var.get()

            import re
            for key in list(self.dictionary):
                if target == "Graphemes":
                    new_key = re.sub(pattern, replacement, key)
                    if new_key != key:
                        self.dictionary[new_key] = self.dictionary.pop(key)
                elif target == "Phonemes":
                    phonemes = self.dictionary[key]
                    # Ensure phonemes are treated as strings, apply regex substitution, and then escape special characters
                    new_phonemes = [re.sub(pattern, replacement, str(phoneme)) for phoneme in phonemes]
                    self.dictionary[key] = new_phonemes

            self.refresh_treeview()
            self.update_entries_window()  # Ensure this is called as a method with parentheses
            self.replace_window.destroy()

        ttk.Button(self.replace_window, text="Apply", style='Accent.TButton', command=apply_replace).grid(row=4, column=1, padx=10, pady=10)

        # Keep the dialog window on top
        self.replace_window.transient(self.entries_window)
        self.replace_window.grab_set()

    
    def close(self):
        # Ensure the entries_window exists
        if hasattr(self, 'entries_window') and self.entries_window.winfo_exists():
            if not self.dictionary:
                self.entries_window.destroy()
                self.create_widgets()
            else:
                response = messagebox.askyesno("Notice", "There are entries in the viewer. Closing this window will clear them all. Are you sure you want to proceed?")
                if response:
                    self.title(self.base_title)
                    self.dictionary.clear()
                    self.viewer_tree.delete(*self.viewer_tree.get_children())
                    self.update_entries_window()
                    self.entries_window.destroy()
                    self.create_widgets()
                else:
                    return
        else:
            return

    def refresh_treeview(self):
        # Define fonts
        self.normal_font = tkFont.Font(family="Helvetica", size=10, weight="normal")
        self.bold_font = tkFont.Font(family="Helvetica", size=10, weight="bold")

        # Setup tag configurations for normal and bold fonts
        self.viewer_tree.tag_configure('normal', font=self.normal_font)
        self.viewer_tree.tag_configure('selected', font=self.bold_font)

        # Capture the grapheme of the currently selected item before clearing entries
        selected = self.viewer_tree.selection()
        selected_grapheme = None
        if selected:
            selected_item_id = selected[0]
            selected_item_values = self.viewer_tree.item(selected_item_id, "values")
            selected_grapheme = selected_item_values[0] if selected_item_values else None

        # Clear all current entries from the treeview
        self.viewer_tree.delete(*self.viewer_tree.get_children())
        
        # Insert new entries into the treeview
        new_selection_id = None
        for grapheme, phonemes in self.dictionary.items():
            if self.lowercase_phonemes_var.get():
                phonemes = [phoneme.lower() for phoneme in phonemes]
            if self.remove_numbered_accents_var.get():
                phonemes = self.remove_numbered_accents(phonemes)
            escaped_phonemes = ', '.join(escape_special_characters(str(phoneme)) for phoneme in phonemes)
            item_id = self.viewer_tree.insert('', 'end', values=(grapheme, escaped_phonemes), tags=('normal',))
            # Check if this was the previously selected grapheme
            if grapheme == selected_grapheme:
                new_selection_id = item_id

        # If there was a previously selected grapheme, reselect its new corresponding item ID
        if new_selection_id:
            self.viewer_tree.selection_set(new_selection_id)
            self.viewer_tree.item(new_selection_id, tags=('selected',))
            self.viewer_tree.see(new_selection_id)  # Ensure the item is visible in the viewport

    def filter_treeview(self):
        search_text = self.search_var.get().lower()
        self.refresh_treeview()
        if search_text:
            for item in self.viewer_tree.get_children():
                if not (search_text in self.viewer_tree.item(item, "values")[0].lower() or
                        search_text in self.viewer_tree.item(item, "values")[1].lower()):
                    self.viewer_tree.delete(item)

    def on_tree_selection(self, event):
        # Define fonts
        self.normal_font = tkFont.Font(family="Helvetica", size=10, weight="normal")
        self.bold_font = tkFont.Font(family="Helvetica", size=10, weight="bold")
        
        for item in self.viewer_tree.get_children():
            self.viewer_tree.item(item, tags=('normal',))
        self.viewer_tree.tag_configure('normal', font=self.normal_font)

        # Apply bold font to selected items
        selected_items = self.viewer_tree.selection()
        for item in selected_items:
            self.viewer_tree.item(item, tags=('selected',))
        self.viewer_tree.tag_configure('selected', font=self.bold_font)
        
        selected_items = self.viewer_tree.selection()
        if selected_items:
            selected_item_id = selected_items[0]
            # Fetch the item data using the item ID, ensuring the tree structure corresponds to dictionary keys
            item_data = self.viewer_tree.item(selected_item_id, 'values')
            if item_data:
                grapheme = item_data[0]
                phonemes = self.dictionary.get(grapheme, [])
                # Update the entries in the respective widgets
                self.word_entry.delete(0, tk.END)
                self.word_entry.insert(0, grapheme)

                self.phoneme_entry.delete(0, tk.END)
                phoneme_text = ' '.join(str(phoneme) for phoneme in phonemes)
                self.phoneme_entry.insert(0, phoneme_text)
            else:
                messagebox.showinfo("Error", "No data found for selected item.")

    def save_as_yaml(self):
        selected_template = self.template_var.get()
        # If "Current Template" is selected, ask the user to select a file to load and save.
        if not self.dictionary:
            messagebox.showinfo("Warning", "No entries to save. Please add entries before saving.")
            return
        if selected_template == "Current Template":
            template_path = filedialog.askopenfilename(title="Using the current YAML file as a template", filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")])
            if not template_path:
                return  # Return if the user cancels the file selection
        else:
            # Define the base directory for templates and construct the file path
            data_folder = Templates
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
        new_entries_text = []
        for grapheme, phonemes in self.dictionary.items():
            if self.lowercase_phonemes_var.get():
                # Convert all phonemes to lowercase if the checkbox is checked
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
                return  # Return if the user cancels the file selection
        else:
            # Define the base directory for templates and construct the file path
            data_folder = Templates
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
        new_entries_text = []
        for grapheme, phonemes in self.dictionary.items():
            if self.lowercase_phonemes_var.get():
                # Convert all phonemes to lowercase if the checkbox is checked
                phonemes = [phoneme.lower() for phoneme in phonemes]
            if self.remove_numbered_accents_var.get():
                phonemes = self.remove_numbered_accents(phonemes)
            escaped_phonemes = [escape_special_characters(phoneme) for phoneme in phonemes]
            formatted_phonemes = ", ".join(f'{phoneme}' for phoneme in escaped_phonemes)
            #grapheme = escape_grapheme(grapheme)
            entry_text = f"- {{grapheme: \"{grapheme}\", phonemes: [{formatted_phonemes}]}}\n"
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

    def load_template(self, selection):
        # Build the full path to the template file
        file_path = os.path.join(Templates, selection)
        yaml = YAML(typ='safe')
        try:
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
            # Assuming the structure of the YAML file includes a dictionary key or similar
            self.dictionary.update(data.get('dictionary', {}))
            print(f"Loaded dictionary from {file_path}")
        except Exception as e:
            print(f"Failed to load file: {e}")
    
    def update_template_combobox(self, combobox, directory):
        try:
            # List all files in the specified directory
            files = os.listdir(directory)
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
            sorted_items = sorted(self.dictionary.items(), key=lambda item: item[0])
        elif sort_by == 'Z-A Sorting':
            sorted_items = sorted(self.dictionary.items(), key=lambda item: item[0], reverse=True)
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
        # Frame for Options
        options_frame = ttk.LabelFrame(self, text="Options")
        options_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Configure the grid layout inside the options_frame to adjust dynamically
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=2)

        # Variable to hold the selected template option
        self.template_var = tk.StringVar()

        # Widgets within the options frame
        ttk.Label(options_frame, text="Select Template:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        # Creating and setting up the combobox
        template_combobox = ttk.Combobox(options_frame, textvariable=self.template_var, state="readonly")
        template_combobox.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Path to the Data folder
        data_folder_path = Templates
        self.update_template_combobox(template_combobox, data_folder_path)
        
        ttk.Checkbutton(options_frame, text="Remove Number Accents", variable=self.remove_numbered_accents_var).grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        ttk.Checkbutton(options_frame, text="Make Phonemes Lowercase", variable=self.lowercase_phonemes_var).grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        # Combobox for sorting options
        self.sort_options_var = tk.StringVar()
        self.sort_combobox = ttk.Combobox(options_frame, textvariable=self.sort_options_var, state="readonly")
        self.sort_combobox['values'] = ('Default Sorting', 'A-Z Sorting', 'Z-A Sorting')
        self.sort_combobox.set('Default Sorting')
        self.sort_combobox.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.sort_combobox.bind("<<ComboboxSelected>>", self.sort_entries)

        # Theme switch styled as a Switch
        self.theme_var = tk.IntVar(value=1)  # 0 for light, 1 for dark
        ttk.Checkbutton(options_frame, text="🌓︎", variable=self.theme_var, style='Switch.TCheckbutton', command=self.toggle_theme).grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Frame for Manual Entry
        manual_frame = ttk.LabelFrame(self, text="Manual Entry")
        manual_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Configure the grid layout inside the manual_frame to adjust dynamically
        manual_frame.grid_columnconfigure(0, weight=1)
        manual_frame.grid_columnconfigure(1, weight=1)

        # Create the word entry on the left
        self.word_entry = ttk.Entry(manual_frame)
        self.word_entry.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Create the phoneme entry on the right
        self.phoneme_entry = ttk.Entry(manual_frame)
        self.phoneme_entry.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Place the buttons so they do not overlap and are centered
        ttk.Button(manual_frame, text="Add Entry", style='Accent.TButton', command=self.add_manual_entry).grid(row=1, column=1, columnspan=1, padx=5, pady=10)
        ttk.Button(manual_frame, text="Delete Entry", style='Accent.TButton', command=self.delete_manual_entry).grid(row=1, column=0, columnspan=1, padx=5, pady=10)
        
        # Create frames for each set of buttons
        convert_frame = ttk.Frame(self)
        convert_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        load_frame = ttk.Frame(self)
        load_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        save_frame = ttk.Frame(self)
        save_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        cad_frame = ttk.Frame(self)
        cad_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        label_font = tkFont.Font(size=10)
        label_color = "gray"

        # Add buttons to each frame
        ttk.Button(convert_frame, text="Convert CMUDict to YAML", command=self.load_cmudict).pack(fill=tk.X)
        ttk.Button(load_frame, text="Append YAML File", command=self.merge_yaml_files).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5), pady=(5))
        ttk.Button(load_frame, text=" Open YAML File ", command=self.load_yaml_file).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5,0), pady=(5))
        
        # For saving, you might want distinct actions for each button, so specify them if they differ
        ttk.Button(save_frame, text="Save OU Dictionary", style='Accent.TButton', command=self.save_as_yaml).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5), pady=(0,5))
        ttk.Button(save_frame, text="Save DS Dictionary", style='Accent.TButton', command=self.save_as_ds_yaml).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5,0), pady=(0,5))
        label = ttk.Label(cad_frame, text="© Cadlaxa | OU Dictionary Editor v0.1", font=label_font, foreground=label_color)
        label.grid(row=0, column=1, sticky="ew", pady=(0,10))
        cad_frame.columnconfigure(0, weight=1)
        cad_frame.columnconfigure(1, weight=0)
        cad_frame.columnconfigure(2, weight=1)
        
        # Configure grid weight for overall flexibility
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=2)
        self.grid_columnconfigure(0, weight=1)

if __name__ == "__main__":
    app = Dictionary()
    app.mainloop()