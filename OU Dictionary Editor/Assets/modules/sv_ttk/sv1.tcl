package require Tk 8.6

# Source theme files in a loop for efficiency and maintainability
set themes [list sunny-yellow_light sunny-yellow_dark moonstone_light moonstone_dark dark-red_light dark-red_dark liver_light liver_dark yellow-green_light yellow-green_dark payne's-gray_light payne's-gray_dark hunter-green_light hunter-green_dark sky-magenta_light sky-magenta_dark l-see-green_light l-see-green_dark]
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

font create SVCaptionFont -family "Arial Rounded MT Bold" -size -12
font create SVBodyFont -family "Arial Rounded MT Bold" -size -14
font create SVBodyStrongFont -family "Arial Rounded MT Bold" -weight bold -size -14
font create SVBodyLargeFont -family "Arial Rounded MT Bold" -size -18
font create SVSubtitleFont -family "Arial Rounded MT Bold" -weight bold -size -20
font create SVTitleFont -family "Arial Rounded MT Bold" -weight bold -size -28
font create SVTitleLargeFont -family "Arial Rounded MT Bold" -weight bold -size -40
font create SVDisplayFont -family "Arial Rounded MT Bold" -weight bold -size -68


proc config_entry_font {w} {
  set font_config [$w config -font]
  if {[lindex $font_config 3] != [lindex $font_config 4]} {
    return
  }
  if {[ttk::style theme use] in {"sunny-yellow_dark", "moonstone_dark", "dark-red_dark", "beaver_dark", "liver_dark", "yellow-green_dark", "payne's-gray_dark", "hunter-green_dark", "sky-magenta_dark", "l-see-green_dark", "middle-gy_dark",
  "sunny-yellow_light", "moonstone_light", "dark-red_light", "beaver_light", "liver_light", "yellow-green_light", "payne's-gray_light", "hunter-green_light", "sky-magenta_light", "l-see-green_light", "middle-gy_light"}} {
    $w configure -font SVBodyFont
  }
}


proc config_menus {w} {
  if {[tk windowingsystem] == "aqua" || [tk windowingsystem] == "win32"} {
    return
  }

  set theme [ttk::style theme use]
  if {$theme == "sunny-yellow_dark" || $theme == "moonstone_dark" || $theme == "dark-red_dark" || $theme == "beaver_dark" || $theme == "liver_dark" || $theme == "yellow-green_dark" || $theme == "payne's-gray_dark" || $theme == "hunter-green_dark" || $theme == "sky-magenta_dark" || $theme == "l-see-green_dark" || $theme == "middle-gy_dark"} {
    $w configure \
      -relief solid \
      -borderwidth 1 \
      -activeborderwidth 0 \
      -background "#292929" \
      -activebackground $ttk::theme::sv_dark::colors(-selbg) \
      -activeforeground $ttk::theme::sv_dark::colors(-selfg) \
      -selectcolor $ttk::theme::sv_dark::colors(-selfg)
  } elseif {$theme == "sunny-yellow_light" || $theme == "moonstone_light" || $theme == "dark-red_light" || $theme == "beaver_light" || $theme == "liver_light" || $theme == "yellow-green_light" || $theme == "payne's-gray_light" || $theme == "hunter-green_light" || $theme == "sky-magenta_light" || $theme == "l-see-green_light" || $theme == "middle-gy_light"} {
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
    if {$theme == "sunny-yellow_dark" || $theme == "moonstone_dark" || $theme == "dark-red_dark" || $theme == "beaver_dark" || $theme == "liver_dark" || $theme == "yellow-green_dark" || $theme == "payne's-gray_dark" || $theme == "hunter-green_dark" || $theme == "sky-magenta_dark" || $theme == "l-see-green_dark" || $theme == "middle-gy_dark"} {
      $w configure -borderwidth 0 -background $ttk::theme::sv_dark::colors(-bg)
    } elseif {$theme == "sunny-yellow_light" || $theme == "moonstone_light" || $theme == "dark-red_light" || $theme == "beaver_light" || $theme == "liver_light" || $theme == "yellow-green_light" || $theme == "payne's-gray_light" || $theme == "hunter-green_light" || $theme == "sky-magenta_light" || $theme == "l-see-green_light" || $theme == "middle-gy_light"} {
      $w configure -borderwidth 0 -background $ttk::theme::sv_light::colors(-bg)
    }
  }
}


proc configure_colors {} {
  set theme [ttk::style theme use]
  if {$theme == "sunny-yellow_dark" || $theme == "moonstone_dark" || $theme == "dark-red_dark" || $theme == "beaver_dark" || $theme == "liver_dark" || $theme == "yellow-green_dark" || $theme == "payne's-gray_dark" || $theme == "hunter-green_dark" || $theme == "sky-magenta_dark" || $theme == "l-see-green_dark" || $theme == "middle-gy_dark"} {
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
      -font SVBodyFont \
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
  } elseif {$theme == "sunny-yellow_light" || $theme == "moonstone_light" || $theme == "dark-red_light" || $theme == "beaver_light" || $theme == "liver_light" || $theme == "yellow-green_light" || $theme == "payne's-gray_light" || $theme == "hunter-green_light" || $theme == "sky-magenta_light" || $theme == "l-see-green_light" || $theme == "middle-gy_light"} {
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
      -font SVBodyFont \
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
