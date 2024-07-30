# Changelog
---
**`(7/--/24)`**
- Add file drag and drop file support to open them directly
- Adds `open with` function to edit the dictionary files without opening the application first
- Get lyrics from the track and add them to the treeview with the predicted phonemes from the selected G2p model
- Import voicebank yaml dictionary (Can be used only when the GUI is used as an OpenUtau Plugin)
- Fix paste function for quoted graphemes
- Added Regenate YAML template from reclist function
- Separate `Plugins` tab
- Added Phonetic System replace (Users can add other phonetic systems by editing the `phoneme systems.csv` on the `Templates` folder)
- Revamp Regex dialog
- Changed default G2p state to true
- Update Localizations and fixes to the code

**`(7/24/24)`**
- Regex find and replace now directly iterates and edits the self.dictionary (the data that holds the graphemes and phonemes) instead of the treeview
- [JA Monophone G2P] Add missing phonemes @lottev1991
- Fixes to JA Monophone G2P splitting graphemes to phonemes
- Fixes to fonts on treeview

**`(7/21/24)`**
- Fixed download speed
- Minor UI changes
- Follow System theme option via `System` RadioButton via `darkdetect` module
- `What's New` window for displaying the `Readme.md` file (`tkhtmlview` and `markdown2` modules are used)
- Update Localizations

**`(7/13/24)`**
- Fixed Cmudict error message to show the errored line instead of the word only
- Update Localizations
- Revamp `Light Mode` color accents to certain ui elements
- Fix Treeview selection color on `Light Mode`
- Performance Fixes

**`(7/09/24)`**
- Directly edit the entry with double click or `enter` button
- Button for G2P suggestions on direct entry edit
- Update Localizations (@zout)
- Copy entry function can now copy the data through the system's clipboard
- Paste function can now paste the datas on the system's clipboard (only yaml and cmudict format is accepted)
- Fixes to G2p combobox, updates also the phoneme entry automatically when changing the models
- Improved Treeview performance especially on bigger dictionary files
- Revamp drag message UI
- New keyboard shortcut: [`Enter` = adding new entry/symbol, `Ctrl/Command + f` = search, `Ctrl/Command + h` = Replace window, `Esc` = close the windows]
- New 5 themes: (`Sunny Yellow`, `Yellow Green`, `Payne's Gray`, `Sky Magenta`, `Light See Green`)
- Update Localizations + New Localizations (`French`, `Russian`)
- Add localizations for messageboxes
- Show Context Menu on `Right-Click` (Only available on Entry Editor)
- Fixed Blank combobox on the G2p suggestions
- G2p Suggestion switch is now also saved on `settings.ini`
- Set default theme and accent to `Mint Dark`
- Closing the `Main GUI` with an open `Entry Viewer` instance will prompt a message instead of closing the GUI immediately
- Code fixes and cleanup

**`(6/30/24)`**
- Added G2p Suggestions
    - Arpabet-plus G2p (@Cadlaxa)
    - French G2p
    - Germern G2p (@LotteV)
    - Italian G2p
    - Japanese Monophone G2p (@LotteV)
    - Millefeuille G2p (@UFR)
    - Portuguese G2p
    - Russian G2p
    - Spanish G2p (@LotteV)
- Fixed word and entry bug when typing with a g2p suggestions
- Fixed batch loading performance of Entry window
- Update Localizations
- Preparing 11 New themes: (`Sunny Yellow`, `Moonstone`, `Beaver`, `Dark Red`, `Liver`, `Yellow Green`, `Payne's Gray`, `Hunter Green`, `Sky Magenta`, `Light See Green`, `Middle Green Yellow`)
- Fix keyboard bindings to not overlap with other systems
- Revamp search function to select the closest value instead if filtering them, clicking the `search` button will iterates the closest search value

**`(6/21/24)`**
- Fixes to fonts for different languages
- Added download progress bar
- Fixed to system exit after propting the user to manually move the files after download
- Code Fixes and Updates

**`(6/6/24)`**
- Fixed security issue with the executable file

**`(5/24/24)`**
- Use compressed cache for loading dictionary files for better performance (startup will be slow on big files cuz of loading the file itself + creating the cache for the first time)
- Update cache files when saving the dictionary files
- Improved treeviewer performance (somewhat)...
- Fixed opening `YAML` files throwing no `grapheme` entry error when there's a blank line
- Fixed `ruamel.yaml` yaml width to prevent line breaks on long entries
- Performance fixes
- Added loading message when loading files

**`(5/20/24)`**
- Reworked YAML saving function to use `Ruamel.yaml` yaml.dump
- Merged 2 YAML saving buttons into 1 main button (standard banks and diffsinger banks both supports the `yaml.org,2002:map` yaml map formats)
- Add YAML validation when saving symbols as a template
- preparation for saving/loading message window when saving files
- Code optimizations and fixes
- Update to Localizations
- Fix saving bug

**`(5/17/24)`**
- Fixed phonemes with special characters not adding quotes with the entire string.
- Added Synthv Import and Export `json` dictionary files
- Automatically add extension filenames when saving
- Update `View Symbols` to `Edit Symbols` (functions limited to: add/delete symbols, select/deselect, search the symbols, and save symbols to template)
- Added `save symbols to template` yaml file and update templates combobox reads the `Templates` folder when new file is saved through `save symbols to template`
- Update to all Localizations + `Cebuano`, `Spanish (Latin America)` localizations
- Added `Find next` and `Find previous` entries on regex dialog
- Split `Replace` button to `Replace` and `Replace All`

**`(5/13/24)`**
- Fixed regex dialog, copy, cut, paste, delete, search broken on `v0.6.1`
- changes to keybinds so that `windows` and `macos` doesn't overlap

**`(5/12/24)`**
- Remove ask file dialog to find the `templates` folder and replace to automatically use the `templates` folder.
- Fixed to TopLevel Window on Regex Dialog
- Fixes to Icon did not apply to TopLevel Windows
- Fixed delete entries also clears the entry box
- Fixed loading YAML after loaded a CMUDict file causes `list indices must be integers or slices, not str` error
- Add select all function via `Ctrl + a` or `Command + a`
- fixed export CMUDict didn't export removed phoneme accents and lower-cased phonemes
- Improved cut and delete entry performance
- Fixed Localization combobox to update on the current local of the GUI and use a human readable option instead of the filename.
- Added `Japanese` Localization (made with DeepL)
- Added index header on treeview

**`(5/7/24)`**
- Fix saving YAML bug
- Add `copy`, `cut`, and `paste` function via `Ctrl + c`/`Command + c` `Ctrl + x`/`Command + x` `Ctrl + v`/`Command + v`
- Treeview Selected can now handle multiple datas at once
- Multiple Selection of entries will be visible on the entrybox instead of only the last selected entry.
- Utau/OpenUtau plugin Feature
- Portable executables for `Windows`, for `MacOS` and `Linux` please use the `.pyw` script
- Fixes to `tcl` not able to locate the themes making the application fail to lunch
- Revamp Regex dialog
- Fix save function on searched entries, only the search entries are saved but the rest is gone
- Option to open file directory after download
- Update `Chinese Simplified`,  `Chinese Traditional`, and `Cantonese` localizations (thanks to @Zout141)


**`(5/4/24)`**
- Update `Chinese Simplified`,  `Chinese Traditional`, and `Cantonese` localizations (thanks to @Zout141)
- Fixed `Lemon Ginger` theme font color on accented buttons for better contrast
- Add entries function now adds the entry below the selected entry instead on the end of the treeview, if no selected entry, it will add to the end of the treeview instead.
- Add entry deselection function via **`Right-Click`**
- Fixed drag label getting stuck when dragging into something else than the entries
- Add feature to export CMUdict text files
- Fixed Update button failed to check update if the internet is temporary disconnected and reconnects again
- Search function now ignores `,` from the search, from `hh, eh, l, ow` to `hh eh l ow` same with the regex find and replace function.
- Add `undo` and `redo` function via `Ctrl + z`/`Command + z` `Ctrl + y`/`Command + y`
- More Fixes

**`(4/24/24)`**
- Added more themes and color accents `["Amaranth", "Amethyst", "Burnt Sienna", "Dandelion", "Denim", "Electric Blue", "Fern", "Lemon Ginger", "Lightning Yellow", "Mint", "Orange", "Pear", "Persian Red", "Pink", "Salmon", "Sapphire", "Sea Green", "Seance"]`
- Autoscroll speed adjusted from `10` to `20`
- Added font rescaling feature on Tree Viewer
- Added `Chinese Simplified`,  `Chinese Traditional`, and `Cantonese` localization (thanks to @Zout141)
- Added  standard python gitignore (thanks to @oxygen-dioxide)
- Added an automatic updater feature
- Added Symbols viewer (kinda buggy and cannot edit the symbols yet)
- Changed windows font from `Segoe UI` to `Arial Rounded MT Bold`
- Fixes to UI elements
- More Fixes

**`(4/19/24)`**
- Tabs
- Localizations via YAML file
- UI changes
- **`templates.ini`** is now deprecated and changed to **`settings.ini`**, users can now delete **`templates.ini`**
- Fixes to Treeview
- Move Theming to Settings tab and data is stored through **`settings.ini`**

**`(4/15/24)`**
- **V.01 released**
- **initial version released and features are all in the readme section**
