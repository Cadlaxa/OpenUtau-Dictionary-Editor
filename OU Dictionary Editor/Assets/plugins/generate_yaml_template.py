from ruamel.yaml import YAML
import os, chardet
from tkinter import messagebox, filedialog
from collections import defaultdict, OrderedDict

# Dictionary to hold the data
dictionary = {}
comments = {}
localization = {}
symbols = defaultdict(tuple)
symbols_list = []
plugin_file = None

def read_symbol_types_from_yaml(folder_path):
    yaml = YAML()
    symbol_types = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".yaml"):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, 'r') as file:
                data = yaml.load(file)
            if 'symbols' in data and isinstance(data['symbols'], list):  # Ensure 'symbols' is in data and is a list
                for item in data['symbols']:
                    if isinstance(item, dict) and 'symbol' in item and 'type' in item:
                        symbol_types[item['symbol']] = item['type']
                    else:
                        print(f"Unexpected item format in {filename}: {item}")
            else:
                print(f"Unexpected data format in {filename}: {data}")
    return symbol_types

def generate_yaml_template_from_reclist():
    # Open a file dialog to select the reclist file
    filepath = filedialog.askopenfilename(
        title="Select Reclist File",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not filepath:
        # If no file is selected, show an info message and return
        messagebox.showinfo("No File Selected", "No file was selected.")
        return None, None

    # Detect file encoding
    with open(filepath, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']

    # Read the reclist file with the detected encoding
    try:
        with open(filepath, 'r', encoding=encoding) as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        messagebox.showerror("Encoding Error", f"Failed to decode the file using detected encoding '{encoding}'.")
        return None, None
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None, None

    # Initialize set to store unique phonemes
    phoneme_set = set()

    # Define vowels
    vowels = {
        'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U', 
        '{', 'V', '3', 'aI', 'eI', 'OI', 'aU', 'oU', 
        'e@', 'e@n', 'e@m', 'eN', 'IN', 'Ar', 'Qr', 
        'Er', 'Ir', 'Or', 'Ur', 'ir', 'ur', 'aIr', 
        'aUr', 'A@', 'Q@', 'E@', 'I@', 'O@', 'U@', 
        'i@', 'u@', 'aI@', 'aU@', 'Q', '1', 'Ol', 
        'aUn', '@r', '@l', '@m', '@n', '@N', '@', 
        'y', 'I\'', 'M', 'U\'', 'Y', '@\'', '@`', 
        '3`', 'A`', 'Q`', 'E`', 'I`', 'O`', 
        'U`', 'i`', 'u`', 'aI`', 'aU`', '}', 
        '2', '3\'', '6', '7', '8', '9', '&', 
        '{~', 'I~', 'aU~', 'VI', 'VU', '@U', 
        'i:', 'u:', 'O:', 'e@0', 'ai', 'ei', 
        'Oi', 'au', 'ou', 'Ou', '@u', 'E~', 
        'e~', '3r', 'ar', 'or', '{l', 'Al', 
        'al', 'El', 'Il', 'ul', 'Ul', 'mm', 
        'nn', 'll', 'NN'
    }
    arpabet_vowels = {
        "aa", "ax", "ae", "ah", "ao", "aw", "ay", "eh", "er", "ey", "ih", "iy", "ow", "oy", "uh", "uw", "a", "e", "i", "o", "u", "ai", "ei", "oi", "au", "ou", "ix", "ux",
        "aar", "ar", "axr", "aer", "ahr", "aor", "or", "awr", "aur", "ayr", "air", "ehr", "eyr", "eir", "ihr", "iyr", "ir", "owr", "our", "oyr", "oir", "uhr", "uwr", "ur",
        "aal", "al", "axl", "ael", "ahl", "aol", "ol", "awl", "aul", "ayl", "ail", "ehl", "el", "eyl", "eil", "ihl", "iyl", "il", "owl", "oul", "oyl", "oil", "uhl", "uwl", "ul",
        "aan", "an", "axn", "aen", "ahn", "aon", "on", "awn", "aun", "ayn", "ain", "ehn", "en", "eyn", "ein", "ihn", "iyn", "in", "own", "oun", "oyn", "oin", "uhn", "uwn", "un",
        "aang", "ang", "axng", "aeng", "ahng", "aong", "ong", "awng", "aung", "ayng", "aing", "ehng", "eng", "eyng", "eing", "ihng", "iyng", "ing", "owng", "oung", "oyng", "oing", "uhng", "uwng", "ung",
        "aam", "am", "axm", "aem", "ahm", "aom", "om", "awm", "aum", "aym", "aim", "ehm", "em", "eym", "eim", "ihm", "iym", "im", "owm", "oum", "oym", "oim", "uhm", "uwm", "um", "oh",
        "eu", "oe", "yw", "yx", "wx", "ox", "ex", "ea", "ia", "oa", "ua"
    }

    # Process each line and extract phonemes
    for line in lines:
        phoneme_groups = line.strip().replace('-', '_').replace('・', '_').replace(' ', '_').split('_')
        for phoneme in phoneme_groups:
            # If the phoneme is in ARPAbet vowels, add it directly
            if phoneme in arpabet_vowels:
                phoneme_set.add(phoneme)
            else:
                # Split CV sequences into consonants and vowels
                consonant = ''
                vowel = ''
                for i, char in enumerate(phoneme):
                    if char in vowels:
                        vowel = char
                        if i > 0:
                            consonant = phoneme[:i]
                            phoneme_set.add(consonant)
                        phoneme_set.add(vowel)
                        break  # Exit after the first vowel to handle only CV pairs
                else:
                    # If no vowels found, add the whole phoneme
                    phoneme_set.add(phoneme)

    # Sort phonemes alphabetically
    sorted_phonemes = sorted(phoneme_set)

    # Read the reference YAML files to get symbol types
    template_folder = 'Templates'
    symbol_types_reference = read_symbol_types_from_yaml(template_folder)

    # Create the symbols section of the YAML data
    symbols = {}
    for phoneme in sorted_phonemes:
        if phoneme:  # Skip empty strings
            # Determine type of the phoneme from reference or default to 'unknown'
            symbol_type = symbol_types_reference.get(phoneme, 'unknown')
            symbols[phoneme] = symbol_type

    return filepath, symbols
