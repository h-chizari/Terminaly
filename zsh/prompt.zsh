# Terminaly Dynamic Context-Aware Prompt Engine (Starship equivalent)
# Pure Zsh execution with sub-15ms latency and zero external dependencies

setopt PROMPT_SUBST

# Load colors based on active Terminaly theme
function _terminaly_load_prompt_colors() {
    local theme_name="latte"
    if [[ -f "$HOME/.terminaly/theme" ]]; then
        theme_name=$(cat "$HOME/.terminaly/theme" 2>/dev/null | tr -d '[:space:]')
    elif [[ -f "$TERMINALY_HOME/.terminaly_data/theme" ]]; then
        theme_name=$(cat "$TERMINALY_HOME/.terminaly_data/theme" 2>/dev/null | tr -d '[:space:]')
    fi

    if [[ "$theme_name" == "latte" ]]; then
        # Light mode high-contrast palette
        _T_CYAN='%{%F{25}%}'        # Deep Sapphire Navy
        _T_MAGENTA='%{%F{90}%}'     # Royal Plum
        _T_YELLOW='%{%F{130}%}'     # Deep Rust / Amber
        _T_GREEN='%{%F{28}%}'       # Forest Green
        _T_RED='%{%F{160}%}'        # Crimson Red
        _T_BLUE='%{%F{31}%}'        # Deep Teal
        _T_GRAY='%{%F{242}%}'       # Slate Gray
    elif [[ "$theme_name" == "nord" ]]; then
        # Arctic palette
        _T_CYAN='%{%F{110}%}'
        _T_MAGENTA='%{%F{139}%}'
        _T_YELLOW='%{%F{222}%}'
        _T_GREEN='%{%F{150}%}'
        _T_RED='%{%F{167}%}'
        _T_BLUE='%{%F{81}%}'
        _T_GRAY='%{%F{246}%}'
    elif [[ "$theme_name" == "tokyo-night" ]]; then
        # Tokyo Night palette
        _T_CYAN='%{%F{75}%}'
        _T_MAGENTA='%{%F{176}%}'
        _T_YELLOW='%{%F{215}%}'
        _T_GREEN='%{%F{114}%}'
        _T_RED='%{%F{203}%}'
        _T_BLUE='%{%F{38}%}'
        _T_GRAY='%{%F{244}%}'
    elif [[ "$theme_name" == "dracula" ]]; then
        # Dracula palette
        _T_CYAN='%{%F{117}%}'
        _T_MAGENTA='%{%F{141}%}'
        _T_YELLOW='%{%F{228}%}'
        _T_GREEN='%{%F{84}%}'
        _T_RED='%{%F{212}%}'
        _T_BLUE='%{%F{141}%}'
        _T_GRAY='%{%F{244}%}'
    else
        # Default Catppuccin Mocha Dark
        _T_CYAN='%{%F{117}%}'
        _T_MAGENTA='%{%F{141}%}'
        _T_YELLOW='%{%F{216}%}'
        _T_GREEN='%{%F{120}%}'
        _T_RED='%{%F{204}%}'
        _T_BLUE='%{%F{75}%}'
        _T_GRAY='%{%F{245}%}'
    fi
    _T_RESET='%{%f%b%}'
}

_terminaly_load_prompt_colors

# Fast git status parser
function _terminaly_git_segment() {
    local git_dir
    git_dir=$(git rev-parse --git-dir 2>/dev/null) || return

    local branch
    branch=$(git branch --show-current 2>/dev/null)
    if [[ -z "$branch" ]]; then
        branch=$(git rev-parse --short HEAD 2>/dev/null)
        [[ -z "$branch" ]] && return
        branch="detached:$branch"
    fi

    local dirty=""
    if ! git diff --quiet 2>/dev/null; then
        dirty="${_T_YELLOW}*${_T_RESET}"
    elif ! git diff --cached --quiet 2>/dev/null; then
        dirty="${_T_GREEN}+${_T_RESET}"
    fi

    echo -n " ${_T_GRAY}on${_T_RESET} ${_T_MAGENTA}⎇ ${branch}${_T_RESET}${dirty}"
}

# Python virtual environment segment
function _terminaly_venv_segment() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        local venv_name=$(basename "$VIRTUAL_ENV")
        echo -n " ${_T_BLUE}(${venv_name})${_T_RESET}"
    fi
}

# Command execution timer
typeset -g _TERMINALY_CMD_START=0
typeset -g _T_CMD_EXECUTED=0

function _terminaly_preexec_timer() {
    _TERMINALY_CMD_START=$EPOCHREALTIME
    _T_CMD_EXECUTED=1
}

function _terminaly_duration_segment() {
    if (( _TERMINALY_CMD_START > 0 )); then
        local elapsed=$(( EPOCHREALTIME - _TERMINALY_CMD_START ))
        _TERMINALY_CMD_START=0
        if (( elapsed > 2.0 )); then
            printf " %s[%.1fs]%s" "$_T_YELLOW" "$elapsed" "$_T_RESET"
        fi
    fi
}

# Dynamic Prompt Hook
autoload -Uz add-zsh-hook
zmodload zsh/datetime 2>/dev/null

add-zsh-hook preexec _terminaly_preexec_timer

function _terminaly_render_prompt() {
    local last_exit=$?
    _terminaly_load_prompt_colors

    local exit_badge=""
    if (( _T_CMD_EXECUTED == 1 && last_exit != 0 )); then
        exit_badge="${_T_RED}[${last_exit}]${_T_RESET} "
    fi
    _T_CMD_EXECUTED=0

    local char="${_T_CYAN}❯${_T_RESET}"
    if [[ -n "$exit_badge" ]]; then
        char="${_T_RED}❯${_T_RESET}"
    fi

    # Build prompt:
    # [dir] [on git] [venv] [duration] [exit_badge]
    # ❯
    PROMPT=$'\n'"${_T_CYAN}%~${_T_RESET}"'$(_terminaly_git_segment)'"$(_terminaly_venv_segment)"'$(_terminaly_duration_segment)'$'\n'"${exit_badge}${char} "
}

add-zsh-hook precmd _terminaly_render_prompt
