**English** *[華語](./README-zh.md)*
# OpenUtau-Dictionary-Editor
A python GUI toolkit for creating and editing Aesthetic YAML dictionaries for OpenUtau 🥰😍
![ou dictionary editor  6D4460C](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/7e28a808-cd52-4c85-a4d0-f2166e32d750)
- To use this GUI Toolkit, for **`Windows`** I recommend using the portable **`.exe`** file and for **`MacOs`** and **`Linux`** I recommend using the **`.pyw`** file and use **`python version 3.10 and above`** **`3.9 and below`** is untested and it may not work properly.
- installing the modules for **`MacOs`** and **`Linux`**:
  ```
  pip install -r requirements.txt
  ```
- pip is not on the path yet do `python get-pip.py` then pip install:
  ```
  python get-pip.py
  ```
---
## 📍 Download the latest version here:
[![Download Latest Release](https://img.shields.io/github/v/release/Cadlaxa/OpenUtau-Dictionary-Editor?style=for-the-badge&label=Download&kill_cache=1)](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/releases)
## 📍 language support
- OpenUtau Dictionary Editor uses a preformated yaml file for GUI translation. All users are welcome to translate the text found in `Templates/Localizations/en_US.yaml` to other languages and submit a pull request.
---
# Features
## Open/Append YAML Dictionaries
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/a0bf596e-01a9-4ec6-bbe2-0d2503972122)
- By clicking the **`[Open YAML File]`** button, you can open a premade OpenUTAU YAML dictionary to edit them directly with this GUI toolkit. The **`[Append YAML File]`** button's function is to merge multiple YAML files so that users can merge them together.
## Create a YAML Dictionary from Scratch
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/4d4b6537-2622-4c2c-b13e-a9838037ee95)
- You can add the graphemes and phonemes onto the Manual Entry section. Pressing the **`[Add Entry]`** button will add them to the Entries viewer. Using the **`[Delete Entry]`** button or the delete button on your keyboard will delete the selected entry. By clicking the entries first then `shift` + `click` to other entries will highlight them so that users can batch delete the entries using the **`[Delete Entry]`** button or the delete keyboard button.
- `Note: If creating a dictionary from scratch, choose a yaml template from the combobox picker`
## Using G2P for Faster Dictionary Editing/Creation
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d4f2a6e7-2df5-4736-884d-073bd8a2f8e6)
- You can turn on `G2P Suggestions` on the `Others` tab and it will generate phonemes automatically when you type the words on the word entry
- Currently the G2p models are the same with [Openutau](https://github.com/stakira/OpenUtau) + Millefeuille French G2p model by [UFR](https://utaufrance.com/)
## Using OpenUtau YAML Templates or Custom Template
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/7079a076-8933-44e2-8428-939c52da749a)
- Using the combobox picker, users can choose their OpenUtau YAML template to create their dictionary. Also, users can add their own templates by placing them in the **`[Templates]`** folder so the GUI toolkit will recognize the files via the templates.ini and use them for dictionary creation.
- `Tip: if you're creating a custom dict from scratch, add your template from the templates folder so that you can use it on the picker and add your entries, if you have already made a custom dict, just import them to the editor then use 'Current Template' so that it add the entries to the current imported yaml file and still preserve the custom symbols`
## Sorting the Entries
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/532b16b8-eebf-423a-b974-9460e577831e)
- Users can sort their entries alphabetically either **`A-Z`** or **`Z-A`**
## Converting CMUdict to OU YAML dictionary
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/2ecf2317-435b-427a-8535-c53dc83150cd)
- Function to convert the CMUdict.txt into a functional OpenUTAU dictionary. Note that the CMUdict mustn't have a **`;;;`** or the GUI toolkit will throw an error.
## Editing the Symbols and saving them as a Template
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/6cde7d0b-1ad2-457d-9170-ae9d3ca2aa96)
- Users can edit the symbols of the yaml dictionary by clicking the **`Edit symbols`**, add or delete the symbols (phonemes and phoneme type) and saving them for future use.
## Using the Entries Viewer
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/6f37b8d4-dff0-4408-9a20-954a245eeeea)
- In the Entries Viewer, users can interact with the entries by clicking, deleting, adding, and arranging the entries.
- ### Clicking the Entries to Edit
  ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/2b85b200-d856-479f-840c-239ed4e2ecd5)
 - Users can `Ctrl` + click and `Shift` + click to select multiple entries in the viewer.
- ## Double Clicking the Cell for Direct Entry Edit
  ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/ee821fe7-19cf-4967-8d3d-087915805b74)
  - By double clicking the selected entry or `right-click > edit`, users can directly edit the entry.
- ### Dragging the Entries to Change Their Positions
  ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d131a01c-e4e7-489d-aa57-37aaa6d406c9)
 - Users can drag and drop the entries to change their positions manually.
## Using the Regex Function
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/8623971c-fcd2-42ff-83a7-5cce092e9123)
- Users can use the Regex search and replace to replace the grapheme or the phonemes.
## Saving and Importing the Dictionary
- There are currently 3 formats for saving the created/edited dictionary:
  - **`OpenUtau YAML Format`**
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/a5259363-fd50-4dc1-ad5b-446fb2faba4a)
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d90fe642-791d-4507-884b-dd6761631814)
  - **`CMUDICT Format`**
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d50030be-793f-488a-9327-0e5933b05d0c)
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/f7720ada-6693-4c8d-a19f-0193d75f9711)
  - **`Synthv Format`**
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d06fc7cf-3206-47e9-9c1d-c135d39d6663)
  - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/5396f87c-4481-46d2-b115-d77c066fb311)
## Changing Themes and Color Accents
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/54450466-81e2-4e2f-9cc2-135d97602121)
- Users change the theme and color accents of the GUI toolkit as they please. Currently there are **`23`** color accents to choose from corresponding with their **`Light`** and **`dark`** theme.
---
- And other features of this GUI Toolkit such as automatic `' '` for the special characters for the grapheme and phonemes, Light mode and Dark mode theming, Entry sorting, Remove number accents, Make phonemes lowercase and more.
