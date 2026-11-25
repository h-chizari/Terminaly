#!/usr/bin/env python3
"""Terminaly Curses UI Library: Reusable pure-Python curses components for pickers, tables, and dialogs."""

import curses
import os
import sys
from typing import List, Tuple, Optional, Callable, Dict, Any

from core.theme import apply_curses_theme

class TerminalColors:
    PAIR_DEFAULT = 1
    PAIR_HEADER = 2
    PAIR_HIGHLIGHT = 3
    PAIR_MUTED = 4
    PAIR_SUCCESS = 5
    PAIR_WARNING = 6
    PAIR_DANGER = 7
    PAIR_ACCENT = 8

    @classmethod
    def init_colors(cls):
        apply_curses_theme()

def safe_addstr(win, y: int, x: int, text: str, attr: int = 0):
    max_y, max_x = win.getmaxyx()
    if 0 <= y < max_y and 0 <= x < max_x:
        avail = max_x - x
        # Avoid writing to the bottom-right corner cell (max_y - 1, max_x - 1)
        # because ncurses returns ERR when advancing cursor past the bottom-right corner.
        if y == max_y - 1:
            avail = max(0, avail - 1)
        if avail > 0:
            try:
                win.addstr(y, x, text[:avail], attr)
            except curses.error:
                pass

def draw_box(win, y: int, x: int, h: int, w: int, title: str = "", attr: int = 0):
    for i in range(h):
        for j in range(w):
            char = " "
            if i == 0 or i == h - 1:
                char = "─"
            elif j == 0 or j == w - 1:
                char = "│"
            if i == 0 and j == 0:
                char = "┌"
            elif i == 0 and j == w - 1:
                char = "┐"
            elif i == h - 1 and j == 0:
                char = "└"
            elif i == h - 1 and j == w - 1:
                char = "┘"
            safe_addstr(win, y + i, x + j, char, attr)
    if title:
        header = f" {title} "
        safe_addstr(win, y, x + 2, header[:max(0, w - 4)], attr | curses.A_BOLD)

class InteractivePicker:
    """A high-performance curses-based interactive fuzzy picker with optional split preview."""
    
    def __init__(self, title: str, items: List[Tuple[str, Any]],
                 preview_fn: Optional[Callable[[Any], List[str]]] = None,
                 placeholder: str = "Type to filter..."):
        self.title = title
        self.all_items = items  # List of (display_text, data_payload)
        self.preview_fn = preview_fn
        self.placeholder = placeholder
        self.query = ""
        self.selected_idx = 0
        self.scroll_offset = 0

    def _filter_items(self) -> List[Tuple[str, Any]]:
        if not self.query:
            return self.all_items
        q = self.query.lower()
        tokens = q.split()
        results = []
        for text, data in self.all_items:
            t_lower = text.lower()
            if all(tok in t_lower for tok in tokens):
                results.append((text, data))
        return results

    def run(self) -> Optional[Any]:
        return curses.wrapper(self._main)

    def _main(self, stdscr) -> Optional[Any]:
        TerminalColors.init_colors()
        curses.curs_set(1)
        stdscr.timeout(100)
        
        while True:
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()
            if max_y < 10 or max_x < 30:
                safe_addstr(stdscr, 0, 0, "Terminal window too small!")
                stdscr.refresh()
                key = stdscr.getch()
                if key in (27, ord('q')):
                    return None
                continue

            filtered = self._filter_items()
            if self.selected_idx >= len(filtered):
                self.selected_idx = max(0, len(filtered) - 1)

            # Determine split widths
            has_preview = (self.preview_fn is not None) and (max_x >= 80)
            list_w = int(max_x * 0.5) if has_preview else max_x
            preview_w = max_x - list_w if has_preview else 0

            # Draw Search / Header box
            draw_box(stdscr, 0, 0, 3, max_x, title=self.title, attr=curses.color_pair(TerminalColors.PAIR_HEADER))
            query_display = self.query if self.query else f"({self.placeholder})"
            query_attr = curses.A_BOLD if self.query else curses.color_pair(TerminalColors.PAIR_MUTED)
            safe_addstr(stdscr, 1, 2, f"Search: {query_display}", query_attr)

            # Draw List Box
            list_h = max_y - 4
            draw_box(stdscr, 3, 0, list_h, list_w,
                     title=f"Results ({len(filtered)})",
                     attr=curses.color_pair(TerminalColors.PAIR_DEFAULT))

            visible_count = list_h - 2
            if self.selected_idx < self.scroll_offset:
                self.scroll_offset = self.selected_idx
            elif self.selected_idx >= self.scroll_offset + visible_count:
                self.scroll_offset = self.selected_idx - visible_count + 1

            for i in range(visible_count):
                item_idx = self.scroll_offset + i
                if item_idx < len(filtered):
                    text, _ = filtered[item_idx]
                    y = 4 + i
                    if item_idx == self.selected_idx:
                        safe_addstr(stdscr, y, 1, f"❯ {text}".ljust(list_w - 2),
                                    curses.color_pair(TerminalColors.PAIR_HIGHLIGHT) | curses.A_BOLD)
                    else:
                        safe_addstr(stdscr, y, 1, f"  {text}".ljust(list_w - 2),
                                    curses.color_pair(TerminalColors.PAIR_DEFAULT))

            # Draw Preview Box
            if has_preview:
                draw_box(stdscr, 3, list_w, list_h, preview_w,
                         title="Preview",
                         attr=curses.color_pair(TerminalColors.PAIR_DEFAULT))
                if filtered:
                    _, curr_data = filtered[self.selected_idx]
                    try:
                        preview_lines = self.preview_fn(curr_data)
                    except Exception as e:
                        preview_lines = [f"Error loading preview: {e}"]
                    for i, p_line in enumerate(preview_lines[:list_h - 2]):
                        safe_addstr(stdscr, 4 + i, list_w + 2, p_line[:preview_w - 4],
                                    curses.color_pair(TerminalColors.PAIR_DEFAULT))

            # Bottom Status Bar
            status_text = " [Enter] Select  [Esc/Ctrl+C] Cancel  [↑/↓] Navigate "
            safe_addstr(stdscr, max_y - 1, 0, status_text.ljust(max(0, max_x - 1)),
                        curses.color_pair(TerminalColors.PAIR_HEADER) | curses.A_REVERSE)

            # Position Cursor
            cursor_x = min(max_x - 2, 10 + len(self.query))
            stdscr.move(1, cursor_x)
            stdscr.refresh()

            # Handle Keys
            key = stdscr.getch()
            if key == -1:
                continue
            if key in (27, 3, 7):  # ESC, Ctrl+C, or Ctrl+G
                return None
            elif key in (curses.KEY_ENTER, 10, 13):
                if filtered and 0 <= self.selected_idx < len(filtered):
                    return filtered[self.selected_idx][1]
                return None
            elif key in (curses.KEY_UP, 16):  # Up or Ctrl+P
                if self.selected_idx > 0:
                    self.selected_idx -= 1
            elif key in (curses.KEY_DOWN, 14):  # Down or Ctrl+N
                if self.selected_idx < len(filtered) - 1:
                    self.selected_idx += 1
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if self.query:
                    self.query = self.query[:-1]
                    self.selected_idx = 0
            elif 32 <= key <= 126:
                self.query += chr(key)
                self.selected_idx = 0
