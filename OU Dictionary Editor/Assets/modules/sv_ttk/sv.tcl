package require Tk 8.6

# Source theme files in a loop for efficiency and maintainability
set themes [list light dark amaranth_dark amaranth_light amethyst_dark amethyst_light burnt-sienna_dark burnt-sienna_light dandelion_dark dandelion_light denim_dark denim_light fern_dark fern_light lemon-ginger_dark lemon-ginger_light lightning-yellow_dark lightning-yellow_light mint_dark mint_light orange_dark orange_light pear_dark pear_light persian-red_dark persian-red_light pink_dark pink_light salmon_dark salmon_light sapphire_dark sapphire_light sea-green_dark sea-green_light seance_dark seance_light sunny-yellow_light sunny-yellow_dark yellow-green_light yellow-green_dark payne's-gray_light payne's-gray_dark sky-magenta_light sky-magenta_dark l-see-green_light l-see-green_dark]
foreach theme $themes {
    source [file join [file dirname [info script]] theme $theme.tcl]
}

if {[tk windowingsystem] == "win32"} {
  set static ""
} elseif {[tk windowingsystem] == "x11"} {
  set static "static"
} else {
  set static ""  # macOS and other systems
}

font create SunValleyCaptionFont -family "Arial Bold" -size -12
font create SunValleyBodyFont -family "Arial Bold" -size -14
font create SunValleyBodyStrongFont -family "Arial Bold" -weight bold -size -14
font create SunValleyBodyLargeFont -family "Arial Bold" -size -18
font create SunValleySubtitleFont -family "Arial Bold" -weight bold -size -20
font create SunValleyTitleFont -family "Arial Bold" -weight bold -size -28
font create SunValleyTitleLargeFont -family "Arial Bold" -weight bold -size -40
font create SunValleyDisplayFont -family "Arial Bold" -weight bold -size -68


proc config_entry_font {w} {
  set font_config [$w config -font]
  if {[lindex $font_config 3] != [lindex $font_config 4]} {
    return
  }
  if {[ttk::style theme use] in {"sun-valley-dark", "sun-valley-light", "sun-valley-light", "amaranth_light", "amethyst_light", "burnt-sienna_light", "dandelion_light", "denim_light", "fern_light", "lemon-ginger_light", "lightning-yellow_light", "mint_light", "orange_light", "pear_light", "persian-red_light", "pink_light", "salmon_light", "sapphire_light", "sea-green_light", "seance_light", "sun-valley-dark", "amaranth_dark", "amethyst_dark", "burnt-sienna_dark", "dandelion_dark", , "denim_dark", "fern_dark", "lemon-ginger_dark", "darkning-yellow_dark", "mint_dark", "orange_dark", "pear_dark", "persian-red_dark", "pink_dark", "salmon_dark", "sapphire_dark", "sea-green_dark", "seance_dark", "sunny-yellow_light", "sunny-yellow_dark", "yellow-green_light", "yellow-green_dark", "payne's-gray_dark", "payne's-gray_light", "sky-magenta_dark", "sky-magenta_light", "l-see-green_dark", "l-see-green_light"}} {
    $w configure -font SunValleyBodyFont
  }
}


proc config_menus {w} {
  if {[tk windowingsystem] == "aqua" || [tk windowingsystem] == "win32"} {
    return
  }

  set theme [ttk::style theme use]
  if {$theme == "sun-valley-dark" || $theme == "amaranth_dark" || $theme == "amethyst_dark" || $theme == "burnt-sienna_dark" || $theme == "dandelion_dark"  || $theme == "denim_dark" || $theme == "fern_dark" || $theme == "lemon-ginger_dark" || $theme == "lightning-yellow_dark" || $theme == "mint_dark" || $theme == "orange_dark" || $theme == "pear_dark" || $theme == "persian-red_dark" || $theme == "pink_dark" || $theme == "salmon_dark" || $theme == "sapphire_dark" || $theme == "sea-green_dark" || $theme == "seance_dark" || $theme == "sunny-yellow_dark" || $theme == "yellow-green_dark" || $theme == "payne's-gray_dark" || $theme == "sky-magenta_dark" || $theme == "l-see-green_dark"} {
    $w configure \
      -relief solid \
      -borderwidth 1 \
      -activeborderwidth 0 \
      -background "#292929" \
      -activebackground $ttk::theme::sv_dark::colors(-selbg) \
      -activeforeground $ttk::theme::sv_dark::colors(-selfg) \
      -selectcolor $ttk::theme::sv_dark::colors(-selfg)
  } elseif {$theme == "sun-valley-light" || $theme == "amaranth_light" || $theme == "amethyst_light" || $theme == "burnt-sienna_light" || $theme == "dandelion_light"  || $theme == "denim_light" || $theme == "fern_light" || $theme == "lemon-ginger_light" || $theme == "lightning-yellow_light" || $theme == "mint_light" || $theme == "orange_light" || $theme == "pear_light" || $theme == "persian-red_light" || $theme == "pink_light" || $theme == "salmon_light" || $theme == "sapphire_light" || $theme == "sea-green_light" || $theme == "seance_light" || $theme == "sunny-yellow_light" || $theme == "yellow-green_light" || $theme == "payne's-gray_light" || $theme == "sky-magenta_light" || $theme == "l-see-green_light"} {
    $w configure \
      -relief solid \
      -borderwidth 1 \
      -activeborderwidth 0 \
      -background "#e7e7e7" \
      -activebackground $ttk::theme::sv_dark::colors(-selbg) \
      -activeforeground $ttk::theme::sv_dark::colors(-selfg) \
      -selectcolor $ttk::theme::sv_dark::colors(-selfg)
  }

  if {[[winfo toplevel $w] cget -menu] != $w} {
    if {$theme == "sun-valley-dark" || $theme == "amaranth_dark" || $theme == "amethyst_dark" || $theme == "burnt-sienna_dark" || $theme == "dandelion_dark"  || $theme == "denim_dark" || $theme == "fern_dark" || $theme == "lemon-ginger_dark" || $theme == "lightning-yellow_dark" || $theme == "mint_dark" || $theme == "orange_dark" || $theme == "pear_dark" || $theme == "persian-red_dark" || $theme == "pink_dark" || $theme == "salmon_dark" || $theme == "sapphire_dark" || $theme == "sea-green_dark" || $theme == "seance_dark" || $theme == "sunny-yellow_dark" || $theme == "yellow-green_dark" || $theme == "payne's-gray_dark" || $theme == "sky-magenta_dark" || $theme == "l-see-green_dark"} {
      $w configure -borderwidth 0 -background $ttk::theme::sv_dark::colors(-bg)
    } elseif {$theme == "sun-valley-light" || $theme == "amaranth_light" || $theme == "amethyst_light" || $theme == "burnt-sienna_light" || $theme == "dandelion_light"  || $theme == "denim_light" || $theme == "fern_light" || $theme == "lemon-ginger_light" || $theme == "lightning-yellow_light" || $theme == "mint_light" || $theme == "orange_light" || $theme == "pear_light" || $theme == "persian-red_light" || $theme == "pink_light" || $theme == "salmon_light" || $theme == "sapphire_light" || $theme == "sea-green_light" || $theme == "seance_light" || $theme == "sunny-yellow_light" || $theme == "yellow-green_light" || $theme == "payne's-gray_light" || $theme == "sky-magenta_light" || $theme == "l-see-green_light"} {
      $w configure -borderwidth 0 -background $ttk::theme::sv_light::colors(-bg)
    }
  }
}


proc configure_colors {} {
  set theme [ttk::style theme use]
  if {$theme == "sun-valley-dark" || $theme == "amaranth_dark" || $theme == "amethyst_dark" || $theme == "burnt-sienna_dark" || $theme == "dandelion_dark"  || $theme == "denim_dark" || $theme == "fern_dark" || $theme == "lemon-ginger_dark" || $theme == "lightning-yellow_dark" || $theme == "mint_dark" || $theme == "orange_dark" || $theme == "pear_dark" || $theme == "persian-red_dark" || $theme == "pink_dark" || $theme == "salmon_dark" || $theme == "sapphire_dark" || $theme == "sea-green_dark" || $theme == "seance_dark" || $theme == "sunny-yellow_dark" || $theme == "yellow-green_dark" || $theme == "payne's-gray_dark" || $theme == "sky-magenta_dark" || $theme == "l-see-green_dark"} {
    ttk::style configure . \
      -background $ttk::theme::sv_dark::colors(-bg) \
      -foreground $ttk::theme::sv_dark::colors(-fg) \
      -troughcolor $ttk::theme::sv_dark::colors(-bg) \
      -focuscolor $ttk::theme::sv_dark::colors(-selbg) \
      -selectbackground $ttk::theme::sv_dark::colors(-selbg) \
      -selectforeground $ttk::theme::sv_dark::colors(-selfg) \
      -insertwidth 1 \
      -insertcolor $ttk::theme::sv_dark::colors(-fg) \
      -fieldbackground $ttk::theme::sv_dark::colors(-bg) \
      -font SunValleyBodyFont \
      -borderwidth 0 \
      -relief flat

    tk_setPalette \
      background $ttk::theme::sv_dark::colors(-bg) \
      foreground $ttk::theme::sv_dark::colors(-fg) \
      highlightColor $ttk::theme::sv_dark::colors(-selbg) \
      selectBackground $ttk::theme::sv_dark::colors(-selbg) \
      selectForeground $ttk::theme::sv_dark::colors(-selfg) \
      activeBackground $ttk::theme::sv_dark::colors(-selbg) \
      activeForeground $ttk::theme::sv_dark::colors(-selfg)

    ttk::style map . -foreground [list disabled $ttk::theme::sv_dark::colors(-disfg)]
  } elseif {$theme == "sun-valley-light" || $theme == "amaranth_light" || $theme == "amethyst_light" || $theme == "burnt-sienna_light" || $theme == "dandelion_light"  || $theme == "denim_light" || $theme == "fern_light" || $theme == "lemon-ginger_light" || $theme == "lightning-yellow_light" || $theme == "mint_light" || $theme == "orange_light" || $theme == "pear_light" || $theme == "persian-red_light" || $theme == "pink_light" || $theme == "salmon_light" || $theme == "sapphire_light" || $theme == "sea-green_light" || $theme == "seance_light" || $theme == "sunny-yellow_light" || $theme == "yellow-green_light" || $theme == "payne's-gray_light" || $theme == "sky-magenta_light" || $theme == "l-see-green_light"} {
    ttk::style configure . \
      -background $ttk::theme::sv_light::colors(-bg) \
      -foreground $ttk::theme::sv_light::colors(-fg) \
      -troughcolor $ttk::theme::sv_light::colors(-bg) \
      -focuscolor $ttk::theme::sv_light::colors(-selbg) \
      -selectbackground $ttk::theme::sv_light::colors(-selbg) \
      -selectforeground $ttk::theme::sv_light::colors(-selfg) \
      -insertwidth 1 \
      -insertcolor $ttk::theme::sv_light::colors(-fg) \
      -fieldbackground $ttk::theme::sv_light::colors(-bg) \
      -font SunValleyBodyFont \
      -borderwidth 0 \
      -relief flat

    tk_setPalette \
      background $ttk::theme::sv_light::colors(-bg) \
      foreground $ttk::theme::sv_light::colors(-fg) \
      highlightColor $ttk::theme::sv_light::colors(-selbg) \
      selectBackground $ttk::theme::sv_light::colors(-selbg) \
      selectForeground $ttk::theme::sv_light::colors(-selfg) \
      activeBackground $ttk::theme::sv_light::colors(-selbg) \
      activeForeground $ttk::theme::sv_light::colors(-selfg)

    ttk::style map . -foreground [list disabled $ttk::theme::sv_light::colors(-disfg)]
  }
}


bind [winfo class .] <<ThemeChanged>> {+configure_colors}
bind TEntry <<ThemeChanged>> {+config_entry_font %W}
bind TCombobox <<ThemeChanged>> {+config_entry_font %W}
bind TSpinbox <<ThemeChanged>> {+config_entry_font %W}
bind Menu <<ThemeChanged>> {+config_menus %W}
