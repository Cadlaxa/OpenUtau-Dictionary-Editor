# OpenUtau-Dictionary-Editor
A python GUI toolkit for creating and editing Aesthetic YAML dictionaries for OpenUtau 🥰😍
![ou dictionary editor  6D4460C](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/7e28a808-cd52-4c85-a4d0-f2166e32d750)
- To use this GUI Toolkit, first open the **`[Install modules.bat]`** to install the neccessary python modules in order for the toolkit to work or just manually pip install them
  ```
  pip install tk sv-ttk ruamel.yaml
  ```
---
# Features
## Open/Append YAML Dictionaries
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/68d34381-0e09-4d10-8440-6806b784b9d8)
- By clicking the **`[Open YAML File]`**, you can open a premade Openutau YAML dictionary to edit them directly with this GUI toolkit. The **`[Append YAML File]`** button function is to merge multiple YAML files so that users can merge them together.
## Create a YAML Dictionary from scratch
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/46568b2b-b722-4e44-8c67-cdeae38d91f3)
- You can add the graphemes and phonemes onto the Manual Entry section. Pressing the **`[Add Entry]`** button will add them to the Entries viewer, using the **`[Delete Entry]`** button or delete button on your keyboard will delete the selected entry. By clicking the entries first then `shift` + `click` to other entries will highlight them so that users can batch delete the entries using the **`[Delete Entry]`** button or the delete keyboard button
## Using OpenUtau YAML Templates or Custom Template
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d364e70f-60c2-4735-ad74-5796a9a2c19d)
- Using the combobox picker, users can choose their OpenUtau YAML template to create their dictionary. Also you users can add their own templates by placing it to the **`[Templates]`** folder and so GUI toolkit will recognize the files and use them for dictionary creation.
## Converting CMUdict to OU YAMl dictionary
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/7932b90b-ca63-4901-bfd6-cc011abdbeb3)
- Function to convert the CMUdict.txt into a functional Openutau dictionary. Note that the CMUdict must have not a **`;;;`** or the GUI toolkit will thrown an error.
## Using the Entries Viewer
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/e2fb61f1-7f4e-46ba-a15b-06181a2ea160)
- On the Entries Viewer, users can interact with the entries by clicking, deleting, adding, arranging the entries
 - ### Clicking the Entries to edit
   - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/fd038fea-3b89-42d1-8130-af55e2294503)
   - Users can `Ctrl` + click and `Shift` + click to select multiple entries on the viewer.
 - ### Dragging the Entries to change their positions
   - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/f0a7637f-e3c1-4884-9e72-ea677684353d)
   - Users can drag and drop the entries to change their positions manually.
## Using the Regex Function
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/2e2af4b9-ff5f-4d96-bded-ac494babd569)
- Users can use the Regex search and replace to replace the grapheme or the phonemes.
## Saving the YAML Dictionary
![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/d8e24192-a3ad-4061-8ece-7131625f35c9)
- There are currently 2 saving buttons to save the YAML dictionary into these formats:
   - Normal OU YAML
   - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/fcf731ff-9d06-420e-8705-063314ceccc2)
   - Diffsinger Format
   - ![image](https://github.com/Cadlaxa/OpenUtau-Dictionary-Editor/assets/92255161/20a075ef-b8b3-4d4c-a228-2b3d39736a09)
---
- And other features of this GUI Toolkit such as automatic `' '` for the special characters for the grapheme and phonemes, Light mode and Dark mode theming, Entry sorting, Remove number accents, Make phonemes lowercase and more


