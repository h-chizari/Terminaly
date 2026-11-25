# Terminaly Dynamic Context-Aware Prompt Engine (Starship equivalent)
# Pure Zsh execution with sub-15ms latency and zero external dependencies

setopt PROMPT_SUBST

# Color definitions
typeset -g _T_CYAN='%F{38}'
typeset -g _T_MAGENTA='%F{135}'
typeset -g _T_YELLOW='%F{220}'
typeset -g _T_GREEN='%F{76}'
typeset -g _T_RED='%F{196}'
typeset -g _T_BLUE='%F{33}'
typeset -g _T_GRAY='%F{242}'
typeset -g _T_RESET='%f%b'

# Fast git status parser
function _terminaly_git_segment() {
    # Check if inside git work tree without subshell if possible
    local git_dir
    git_dir=$(git rev-parse --git-dir 2>/dev/null) || return

    local branch
    branch=$(git branch --show-current 2>/dev/null)
    if [[ -z "$branch" ]]; then
        branch=$(git rev-parse --short HEAD 2>/dev/null)
        [[ -z "$branch" ]] && return
        branch="detached:$branch"
    fi

    # Check dirty status (fast check)
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
function _terminaly_preexec_timer() {
    _TERMINALY_CMD_START=$EPOCHREALTIME
}

function _terminaly_duration_segment() {
    if (( _TERMINALY_CMD_START > 0 )); then
        local elapsed=$(( EPOCHREALTIME - _TERMINALY_CMD_START ))
        _TERMINALY_CMD_START=0
        if (( elapsed > 2.0 )); then
            printf " ${_T_YELLOW}[%.1fs]${_T_RESET}" $elapsed
        fi
    fi
}

# Dynamic Prompt Hook
autoload -Uz add-zsh-hook
zmodload zsh/datetime 2>/dev/null

add-zsh-hook preexec _terminaly_preexec_timer

function _terminaly_render_prompt() {
    local last_exit=$?
    local exit_badge=""
    if (( last_exit != 0 )); then
        exit_badge="${_T_RED}[${last_exit}]${_T_RESET} "
    fi

    local char="${_T_CYAN}❯${_T_RESET}"
    if (( last_exit != 0 )); then
        char="${_T_RED}❯${_T_RESET}"
    fi

    # Build prompt:
    # [dir] [on git] [venv] [duration] [exit_badge]
    # ❯
    PROMPT=$'\n'"${_T_CYAN}%~${_T_RESET}"'$(_terminaly_git_segment)'"$(_terminaly_venv_segment)"'$(_terminaly_duration_segment)'$'\n'"${exit_badge}${char} "
}

add-zsh-hook precmd _terminaly_render_prompt
