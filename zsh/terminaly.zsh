# Terminaly: Main Zsh Environment Initializer
# Zero external downloads. 100% native macOS.

setopt NO_BG_NICE 2>/dev/null

export TERMINALY_HOME="${0:A:h:h}"
export PATH="$TERMINALY_HOME/bin:$PATH"

# Source modular components
source "$TERMINALY_HOME/zsh/prompt.zsh"
source "$TERMINALY_HOME/zsh/jump.zsh"
source "$TERMINALY_HOME/zsh/history.zsh"
source "$TERMINALY_HOME/zsh/env_manager.zsh"
source "$TERMINALY_HOME/zsh/keybindings.zsh"

# Apply active terminal theme colors (OSC 10/11)
python3 -c "
import sys
sys.path.insert(0, '$TERMINALY_HOME')
try:
    from core.theme import apply_terminal_theme
    apply_terminal_theme()
except Exception:
    pass
" 2>/dev/null

# Command reference & help shortcut
function help() {
    "$TERMINALY_HOME/bin/terminaly" help
}

# tfm shell wrapper: lands on the folder visited inside tfm upon exit
function tfm() {
    "$TERMINALY_HOME/bin/tfm" "$@"

    local target=""
    if [[ -f "$HOME/.terminaly/lastdir" ]]; then
        target=$(cat "$HOME/.terminaly/lastdir" 2>/dev/null)
        rm -f "$HOME/.terminaly/lastdir"
    elif [[ -f "$TERMINALY_HOME/.terminaly_data/lastdir" ]]; then
        target=$(cat "$TERMINALY_HOME/.terminaly_data/lastdir" 2>/dev/null)
        rm -f "$TERMINALY_HOME/.terminaly_data/lastdir"
    fi

    if [[ -n "$target" && -d "$target" && "$target" != "$PWD" ]]; then
        cd "$target"
    fi
}
# Alias to handle typo 'tmf'
alias tmf="tfm"

# AI Task & Workflow runner (Warp Terminal style)
function task() {
    "$TERMINALY_HOME/bin/terminaly" task "$@"
}
alias ask="task"

# Record initial shell launch directory
if whence -w _terminaly_chpwd_record >/dev/null 2>&1; then
    _terminaly_chpwd_record
fi
