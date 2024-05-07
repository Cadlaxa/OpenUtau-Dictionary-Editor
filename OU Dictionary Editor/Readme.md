# Changelog
---
**`(5/7/24)`**
- Fix saving YAML bug
- Add `copy`, `cut`, and `paste` function via `Ctrl + c`/`Command + c` `Ctrl + x`/`Command + x` `Ctrl + v`/`Command + v`
- Treeview Selected can now handle multiple datas at once
- Multiple Selection of entries will be visible on the entrybox instead of only the last selected entry.
- Utau/OpenUtau plugin Feature
- Portable executables for `Windows`, for `MacOS` and `Linux` please use the `.pyw` script
- Fixes to `tcl` not able to locate the themes making the application fail to lunch


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
- Move Theming to Settings tab and data is store through **`settings.ini`**

**`(4/15/24)`**
- **V.01 released**
- **initial version released and features are all in the readme section**
