import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES

class YourApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Drag and Drop File")
        
        # Create the frame
        self.options_frame = ttk.LabelFrame(self, text="Drop files here")
        self.options_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.options_frame.columnconfigure(0, weight=1)
        self.options_frame.columnconfigure(1, weight=2)

        # Register the frame as a drop target
        self.options_frame.drop_target_register(DND_FILES)
        self.options_frame.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        # Get the file paths from the event
        files = self.tk.splitlist(event.data)
        
        # Assuming you only want to open the first dropped file
        if files:
            filepath = self.dnd_path_to_native_path(files[0])
            print("Dropped file:", filepath)

            # Perform actions with the dropped file, e.g., open it
            self.open_file(filepath)
    
    def open_file(self, filepath):
        # Perform actions to open the file, e.g., display its content
        with open(filepath, 'r') as file:
            content = file.read()
            print("File content:", content)

    def dnd_path_to_native_path(self, dnd_path):
        # Handle URI schemes if needed (specific to Windows)
        if dnd_path.startswith("{"):
            dnd_path = dnd_path[1:-1]
        return dnd_path.replace('/', '\\') if '\\' in dnd_path else dnd_path

if __name__ == "__main__":
    app = YourApp()
    app.mainloop()
