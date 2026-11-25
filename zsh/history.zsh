# Terminaly Persistent SQLite Command History (Atuin equivalent)

autoload -Uz add-zsh-hook
zmodload zsh/datetime 2>/dev/null

typeset -g _T_HIST_CMD=""
typeset -g _T_HIST_START=0
typeset -g _T_SESSION_ID="sess_$$"

function _terminaly_hist_preexec() {
    _T_HIST_CMD="$1"
    _T_HIST_START=$EPOCHREALTIME
}

function _terminaly_hist_precmd() {
    local last_exit=$?
    if [[ -n "$_T_HIST_CMD" ]]; then
        local dur=0.0
        if (( _T_HIST_START > 0 )); then
            dur=$(( EPOCHREALTIME - _T_HIST_START ))
        fi
        
        # Asynchronously record to SQLite
        ("$TERMINALY_HOME/bin/thist" record "$_T_HIST_CMD" "$PWD" "$last_exit" "$dur" "$_T_SESSION_ID" >/dev/null 2>&1 &)
        _T_HIST_CMD=""
        _T_HIST_START=0
    fi
}

add-zsh-hook preexec _terminaly_hist_preexec
add-zsh-hook precmd _terminaly_hist_precmd

# Ctrl+R Widget replacing standard incremental search
function _terminaly_history_widget() {
    local selected
    selected=$("$TERMINALY_HOME/bin/thist" tui "$LBUFFER" 2>/dev/tty)
    if [[ -n "$selected" ]]; then
        LBUFFER="$selected"
    fi
    zle reset-prompt
}

zle -N _terminaly_history_widget
bindkey '^R' _terminaly_history_widget
