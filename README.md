# Terminaly: Offline macOS Native & Antigravity Terminal Suite

**Terminaly** is a high-speed, modular terminal enhancement suite designed specifically for macOS native tools (`Terminal.app`, `/bin/zsh`, `/usr/bin/vim`, `/usr/bin/sqlite3`, Python 3 stdlib) and **Google Antigravity (`agy`)**.

It provides a complete, modern command-line productivity environment built entirely with native macOS tools and **zero external downloads** (`brew`, `pip`, `npm`, and `cargo` are NOT required).

---

## 15 Features at a Glance

| # | Capability | Benchmark Stack | Terminaly Native Offline Equivalent |
|---|---|---|---|
| **1** | GPU-Accelerated Terminal Emulation | Ghostty | **`profiles/Terminaly.terminal`**: Metal GPU rendering, 24-bit TrueColor, font ligatures, and Option-as-Meta key navigation. |
| **2** | Multiplexing & Window Management | tmux + TUIOS | **`terminaly mux`**: Pure-Python PTY multiplexer with real-time macOS telemetry top bar (CPU, RAM, Battery, Time). |
| **3** | Fuzzy Session Switching & Presets | SessionX + Sesh | **`terminaly session`**: Fuzzy session switcher indexing active git repos, worktrees, and workspaces with live previews. |
| **4** | Floating Popup Panes | Floax | **`terminaly scratch`** (`Ctrl+\`): Floating overlay Terminal scratchpad window via AppleScript & Vim popup terminal. |
| **5** | Git Worktree Lifecycle Management | Worktrunk | **`twt`**: High-speed worktree manager (`twt list`, `twt add`, `twt remove`, `twt prune`) with automated `.env` sync. |
| **6** | Parallel AI Agent & Worktree Dashboard | Workmux | **`tboard`**: Curses dashboard monitoring worktrees, live git diffs, and running Antigravity (`agy`) agent transcripts. |
| **7** | POSIX Shell & Structured Data Queries | Zsh + eza + Nushell | **`tls` & `tq`**: `tls` provides formatted directory trees and git status; `tq` executes SQL queries over JSON, CSV, and SQLite tables. |
| **8** | Dynamic Context-Aware Prompt | Starship | **`zsh/prompt.zsh`**: Sub-15ms Zsh prompt displaying git branch, dirty flag, venv, command execution timer (>2s), and exit code badge. |
| **9** | Terminal-Native AI Coding Agent | Pi + ASD-STE100 | **`tai`**: Antigravity CLI (`agy`) bridge with ASD-STE100 prompting rules, session transcript export, and slash commands. |
| **10** | Smart Directory Jumping | Zoxide | **`z <query>`**: SQLite frecency engine (`frecency.db`) with decay scoring and interactive fuzzy fallback. |
| **11** | Persistent, AI-Searchable History | Atuin | **`thist`** (`Ctrl+R`): SQLite-backed history tracking command, cwd, duration, and exit code with interactive search TUI. |
| **12** | Universal Fuzzy Search & Channels | fzf + Television | **`tfzf`**: Universal fuzzy finder with live split preview and structured channels (`files`, `dirs`, `git`, `proc`, `history`, `env`). |
| **13** | In-Terminal IDE | Neovim / LazyVim | **`vim/vimrc`**: Configured native `/usr/bin/vim` 9.1 with Netrw drawer (`Ctrl+E`), `:terminal` splits, and Antigravity AI review (`<leader>ai`). |
| **14** | Visual TUI File Explorer | Superfile | **`tfm`**: Dual-pane visual file explorer with syntax-highlighted previews, bookmarks, and clipboard operations (`c`, `x`, `v`, `d`). |
| **15** | Automatic Per-Project Environments | Mise + Nix | **`zsh/env_manager.zsh`**: Directory-scoped environment auto-loader for `.env` / `.terminaly-env` with SHA256 security verification. |

---

## Quick Start & Installation

Run the self-contained installer:
```zsh
./install.sh
```

To activate immediately in your current terminal:
```zsh
source ~/.zshrc
```

Verify your environment:
```zsh
terminaly doctor
```

---

## Keyboard Shortcuts

| Shortcut | Action | Tool |
|---|---|---|
| `Ctrl+R` | Interactive Persistent History Search (Atuin style) | `thist` |
| `Ctrl+T` | Fuzzy File Finder & Insertion | `tfzf` |
| `Alt+C` (or `Esc+C`) | Fuzzy Directory Jump | `tfzf` |
| `Ctrl+\` | Toggle Floating Scratchpad Terminal | `terminaly scratch` |
| `Ctrl+E` (inside Vim) | Toggle Netrw File Drawer | `vim` |
| `<leader>t` (inside Vim) | Open Bottom Terminal Drawer | `vim` |
| `<leader>ai` (inside Vim) | Send selection/file to Antigravity AI Agent | `tai` |

---

## CLI Tools Reference

- **Directory Tree & Modern Listing**:
  ```zsh
  tls -t            # Render visual directory tree
  tls -l            # Detailed listing with human sizes and git badges
  ```
- **Query Structured Data**:
  ```zsh
  cat users.json | tq "SELECT name, email FROM data WHERE age > 25"
  tq -f report.csv "SELECT department, SUM(sales) FROM data GROUP BY department"
  ```
- **Universal Fuzzy Finder**:
  ```zsh
  tfzf --channel=files    # Search files with preview
  tfzf --channel=proc     # Search processes and inspect CPU/RAM
  tfzf --channel=git      # Browse git commits with diff preview
  ```
- **Git Worktrees**:
  ```zsh
  twt list                # List all parallel worktrees
  twt add feature-auth    # Create worktree under .worktrees/feature-auth
  twt remove feature-auth # Remove worktree safely
  ```
- **Interactive Dashboards & File Manager**:
  ```zsh
  tboard                  # Launch Worktree & Antigravity Agent dashboard
  tfm                     # Launch dual-pane visual file manager with bottom command prompt
  ```
  Inside `tfm`:
  - Press `:` or `!` to activate the **Integrated Shell Command Prompt**.
  - Type any command (`git status`, `mkdir`, `touch`, `python script.py`, or `cd <dir>`).
  - Use `%f` to insert the selected file's path, or `%n` for its filename.
  - Press `Tab` for filename auto-completion, `↑`/`↓` for command history, `Enter` to run, `Esc` to cancel.
- **Interactive AI Step-by-Step Workflows (Warp Terminal style)**:
  ```zsh
  task "clean up merged git branches"
  ask "find files larger than 100MB and inspect disk usage"
  task "find what process is using port 3000 and stop it"
  ```
  Decomposes your goal into structured steps with safety ratings (`SAFE`, `MODIFY`, `CAUTION`).
  - Press `[r]` or `[Enter]` to run the step.
  - Press `[e]` to tweak/edit the command before execution.
  - Press `[s]` to skip to the next step.
  - Press `[a]` to run all remaining steps automatically.
- **Antigravity AI Bridge**:
  ```zsh
  tai ask "Refactor this function to improve performance" -f main.py
  tai sessions            # List recent Antigravity conversation sessions
  tai export <session_id> # Export transcript to markdown
  ```

---

## Author & Open Source License

* **Author:** Hassan Chizari
* **License:** Open Source under the MIT License — free to use, modify, and distribute.
