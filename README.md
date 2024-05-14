**English** *[Chinese](./README-zh.md)*
# OpenUtau-Dictionary-Editor
A python GUI toolkit for creating and editing Aesthetic YAML dictionaries for OpenUtau 🥰😍
![ou dictionary editor  6D4460C](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/7e28a808-cd52-4c85-a4d0-f2166e32d750)
- To use this GUI Toolkit, for **`Windows`** I recommend using the portable **`.exe`** file and for **`MacOs`** and **`Linux`** I recommend using the **`.pyw`** file and use **`python version 3.10 and above`** **`3.9 and below`** is untested and it may not work properly.
- installing the modules for **`MacOs`** and **`Linux`**:
  ```
  pip install ruamel.yaml tk requests
  ```
---
## 📍 Download the latest version here:
[![Download Latest Release](https://img.shields.io/github/v/release/Cadlaxa/OpenUtau-Dictionary-Editor?style=for-the-badge&label=Download&kill_cache=1)](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/releases)
---
# Features
## Open/Append YAML Dictionaries
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/a0bf596e-01a9-4ec6-bbe2-0d2503972122)
- By clicking the **`[Open YAML File]`** button, you can open a premade OpenUTAU YAML dictionary to edit them directly with this GUI toolkit. The **`[Append YAML File]`** button's function is to merge multiple YAML files so that users can merge them together.
## Create a YAML Dictionary from Scratch
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/4d4b6537-2622-4c2c-b13e-a9838037ee95)
- You can add the graphemes and phonemes onto the Manual Entry section. Pressing the **`[Add Entry]`** button will add them to the Entries viewer. Using the **`[Delete Entry]`** button or the delete button on your keyboard will delete the selected entry. By clicking the entries first then `shift` + `click` to other entries will highlight them so that users can batch delete the entries using the **`[Delete Entry]`** button or the delete keyboard button.
- `Note: If creating a dictionary from scratch, choose a yaml template from the combobox picker`
## Using OpenUtau YAML Templates or Custom Template
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/7079a076-8933-44e2-8428-939c52da749a)
- Using the combobox picker, users can choose their OpenUtau YAML template to create their dictionary. Also, users can add their own templates by placing them in the **`[Templates]`** folder so the GUI toolkit will recognize the files via the templates.ini and use them for dictionary creation.
- `Tip: if you're creating a custom dict from scratch, add your template from the templates folder so that you can use it on the picker and add your entries, if you have already made a custom dict, just import them to the editor then use 'Current Template' so that it add the entries to the current imported yaml file and still preserve the custom symbols`
## Sorting the Entries
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/86e65879-9af1-4cda-af37-70b8c1cc40a6)
- Users can sort their entries alphabetically either **`A-Z`** or **`Z-A`**
## Converting CMUdict to OU YAML dictionary
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/2ecf2317-435b-427a-8535-c53dc83150cd)
- Function to convert the CMUdict.txt into a functional OpenUTAU dictionary. Note that the CMUdict mustn't have a **`;;;`** or the GUI toolkit will throw an error.
## Using the Entries Viewer
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/6f37b8d4-dff0-4408-9a20-954a245eeeea)
- In the Entries Viewer, users can interact with the entries by clicking, deleting, adding, and arranging the entries.
- ### Clicking the Entries to Edit
- ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/2b85b200-d856-479f-840c-239ed4e2ecd5)
 - Users can `Ctrl` + click and `Shift` + click to select multiple entries in the viewer.
- ### Dragging the Entries to Change Their Positions
- ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/470c74b9-aa64-4048-8ed2-6d29086ab50f)
 - Users can drag and drop the entries to change their positions manually.
## Using the Regex Function
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/65e78088-d2fe-4d32-9663-f1b0dc42d083)
- Users can use the Regex search and replace to replace the grapheme or the phonemes.
## Saving the YAML Dictionary
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/aed1949e-caa1-4eba-9633-5dcfdbf50d94)
- There are currently 2 saving buttons to save the YAML dictionary into these formats:
 - Normal OU YAML
 - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/fcf731ff-9d06-420e-8705-063314ceccc2)
 - Diffsinger Format
 - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/20a075ef-b8b3-4d4c-a228-2b3d39736a09)
## Changing Themes and Color Accents
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/54450466-81e2-4e2f-9cc2-135d97602121)
- Users change the theme and color accents of the GUI toolkit as they please. Currently there are **`18`** color accents to choose from corresponding with their **`Light`** and **`dark`** theme.
---
- And other features of this GUI Toolkit such as automatic `' '` for the special characters for the grapheme and phonemes, Light mode and Dark mode theming, Entry sorting, Remove number accents, Make phonemes lowercase and more.
