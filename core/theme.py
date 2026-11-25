#!/usr/bin/env python3
"""Terminaly Theme Engine: Beautiful palettes for light and dark terminals."""

import curses
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

TERMINALY_DIR = Path.home() / ".terminaly"
THEME_FILE = TERMINALY_DIR / "theme"

THEMES = {
    "latte": {
        "name": "Catppuccin Latte (Light)",
        "type": "light",
        "desc": "Crisp, warm contrast optimized for light, beige, or white terminal backgrounds",
        # 256-color codes: (fg, bg)
        "curses": {
            "default": (-1, -1),
            "header": (25, -1),        # Deep Sapphire Navy
            "highlight": (234, 153),   # Dark Charcoal text on Soft Sky Blue bar
            "muted": (242, -1),        # Slate Gray (readable on light)
            "success": (28, -1),       # Forest Green
            "warning": (130, -1),      # Warm Amber / Cinnamon
            "danger": (160, -1),       # Ruby Crimson
            "accent": (90, -1),        # Deep Plum / Mauve
        },
        "ansi": {
            "primary": "\033[38;5;25m",
            "secondary": "\033[38;5;31m",
            "highlight": "\033[38;5;234m\033[48;5;153m",
            "muted": "\033[38;5;242m",
            "success": "\033[38;5;28m",
            "warning": "\033[38;5;130m",
            "danger": "\033[38;5;160m",
            "accent": "\033[38;5;90m",
            "text": "\033[38;5;235m",
        }
    },
    "catppuccin": {
        "name": "Catppuccin Mocha (Dark)",
        "type": "dark",
        "desc": "Modern soothing pastel palette on deep slate dark background",
        "curses": {
            "default": (-1, -1),
            "header": (117, -1),       # Sky Blue
            "highlight": (232, 117),   # Charcoal on Sky Blue
            "muted": (245, -1),        # Warm Gray
            "success": (120, -1),      # Mint Green
            "warning": (216, -1),      # Peach
            "danger": (204, -1),       # Flamingo Red
            "accent": (141, -1),       # Mauve Lavender
        },
        "ansi": {
            "primary": "\033[38;5;117m",
            "secondary": "\033[38;5;75m",
            "highlight": "\033[38;5;232m\033[48;5;117m",
            "muted": "\033[38;5;245m",
            "success": "\033[38;5;120m",
            "warning": "\033[38;5;216m",
            "danger": "\033[38;5;204m",
            "accent": "\033[38;5;141m",
            "text": "\033[38;5;253m",
        }
    },
    "tokyo-night": {
        "name": "Tokyo Night (Dark)",
        "type": "dark",
        "desc": "Vibrant neon accents on a sleek deep blue-black night background",
        "curses": {
            "default": (-1, -1),
            "header": (75, -1),        # Neon Cyan/Blue
            "highlight": (234, 75),    # Dark on Neon Blue
            "muted": (244, -1),        # Steel Gray
            "success": (114, -1),      # Spring Green
            "warning": (215, -1),      # Warm Orange
            "danger": (203, -1),       # Coral Red
            "accent": (176, -1),       # Neon Magenta
        },
        "ansi": {
            "primary": "\033[38;5;75m",
            "secondary": "\033[38;5;38m",
            "highlight": "\033[38;5;234m\033[48;5;75m",
            "muted": "\033[38;5;244m",
            "success": "\033[38;5;114m",
            "warning": "\033[38;5;215m",
            "danger": "\033[38;5;203m",
            "accent": "\033[38;5;176m",
            "text": "\033[38;5;252m",
        }
    },
    "nord": {
        "name": "Nord Arctic (Dark)",
        "type": "dark",
        "desc": "Calm, cold arctic ice blue and frost palette",
        "curses": {
            "default": (-1, -1),
            "header": (110, -1),       # Frost Blue
            "highlight": (236, 110),   # Polar Night on Frost Blue
            "muted": (246, -1),        # Arctic Gray
            "success": (150, -1),      # Aurora Green
            "warning": (222, -1),      # Aurora Yellow
            "danger": (167, -1),       # Aurora Red
            "accent": (139, -1),       # Aurora Purple
        },
        "ansi": {
            "primary": "\033[38;5;110m",
            "secondary": "\033[38;5;81m",
            "highlight": "\033[38;5;236m\033[48;5;110m",
            "muted": "\033[38;5;246m",
            "success": "\033[38;5;150m",
            "warning": "\033[38;5;222m",
            "danger": "\033[38;5;167m",
            "accent": "\033[38;5;139m",
            "text": "\033[38;5;254m",
        }
    },
    "dracula": {
        "name": "Dracula (Dark)",
        "type": "dark",
        "desc": "High contrast gothic dark theme with vivid purple and pink highlights",
        "curses": {
            "default": (-1, -1),
            "header": (141, -1),       # Dracula Purple
            "highlight": (234, 141),   # Dark on Purple
            "muted": (244, -1),        # Muted Gray
            "success": (84, -1),       # Bright Green
            "warning": (228, -1),      # Bright Yellow
            "danger": (212, -1),       # Hot Pink / Red
            "accent": (117, -1),       # Cyan
        },
        "ansi": {
            "primary": "\033[38;5;141m",
            "secondary": "\033[38;5;117m",
            "highlight": "\033[38;5;234m\033[48;5;141m",
            "muted": "\033[38;5;244m",
            "success": "\033[38;5;84m",
            "warning": "\033[38;5;228m",
            "danger": "\033[38;5;212m",
            "accent": "\033[38;5;117m",
            "text": "\033[38;5;255m",
        }
    }
}

def get_theme_name() -> str:
    env_theme = os.environ.get("TERMINALY_THEME")
    if env_theme and env_theme in THEMES:
        return env_theme
    if THEME_FILE.exists():
        try:
            val = THEME_FILE.read_text(encoding="utf-8").strip().lower()
            if val in THEMES:
                return val
        except Exception:
            pass
    # Default to 'latte' (light) since user's terminal has light background, or catppuccin
    return "latte"

def set_theme_name(theme_name: str) -> bool:
    if theme_name not in THEMES:
        return False
    try:
        THEME_FILE.parent.mkdir(parents=True, exist_ok=True)
        THEME_FILE.write_text(theme_name, encoding="utf-8")
        return True
    except Exception:
        # Fallback to local data dir
        fallback = Path(__file__).resolve().parent.parent / ".terminaly_data" / "theme"
        fallback.parent.mkdir(parents=True, exist_ok=True)
        fallback.write_text(theme_name, encoding="utf-8")
        return True

def get_active_theme() -> Dict[str, Any]:
    name = get_theme_name()
    return THEMES.get(name, THEMES["latte"])

def apply_curses_theme(theme_name: Optional[str] = None):
    t = THEMES.get(theme_name or get_theme_name(), THEMES["latte"])
    curses.start_color()
    curses.use_default_colors()

    c = t["curses"]
    has_256 = curses.COLORS >= 256

    if has_256:
        curses.init_pair(1, c["default"][0], c["default"][1])
        curses.init_pair(2, c["header"][0], c["header"][1])
        curses.init_pair(3, c["highlight"][0], c["highlight"][1])
        curses.init_pair(4, c["muted"][0], c["muted"][1])
        curses.init_pair(5, c["success"][0], c["success"][1])
        curses.init_pair(6, c["warning"][0], c["warning"][1])
        curses.init_pair(7, c["danger"][0], c["danger"][1])
        curses.init_pair(8, c["accent"][0], c["accent"][1])
    else:
        # Standard 8-color fallback
        if t["type"] == "light":
            curses.init_pair(1, -1, -1)
            curses.init_pair(2, curses.COLOR_BLUE, -1)
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(4, curses.COLOR_BLACK, -1)
            curses.init_pair(5, curses.COLOR_GREEN, -1)
            curses.init_pair(6, curses.COLOR_RED, -1)
            curses.init_pair(7, curses.COLOR_RED, -1)
            curses.init_pair(8, curses.COLOR_MAGENTA, -1)
        else:
            curses.init_pair(1, -1, -1)
            curses.init_pair(2, curses.COLOR_CYAN, -1)
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(4, curses.COLOR_WHITE, -1)
            curses.init_pair(5, curses.COLOR_GREEN, -1)
            curses.init_pair(6, curses.COLOR_YELLOW, -1)
            curses.init_pair(7, curses.COLOR_RED, -1)
            curses.init_pair(8, curses.COLOR_MAGENTA, -1)
