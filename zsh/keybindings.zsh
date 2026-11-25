# Terminaly Keybindings and Ergonomic Shell Shortcuts

# Ctrl+T: Fuzzy file insertion
function _terminaly_fzf_file_widget() {
    local selected
    selected=$("$TERMINALY_HOME/bin/tfzf" --channel=files 2>/dev/tty)
    if [[ -n "$selected" ]]; then
        LBUFFER="${LBUFFER}${selected} "
    fi
    zle reset-prompt
}
zle -N _terminaly_fzf_file_widget
bindkey '^T' _terminaly_fzf_file_widget

# Alt+C / Esc-C: Fuzzy directory cd
function _terminaly_fzf_cd_widget() {
    local selected
    selected=$("$TERMINALY_HOME/bin/tfzf" --channel=dirs 2>/dev/tty)
    if [[ -n "$selected" && -d "$selected" ]]; then
        cd "$selected"
    fi
    zle reset-prompt
}
zle -N _terminaly_fzf_cd_widget
bindkey '\ec' _terminaly_fzf_cd_widget

# Ctrl+\: Toggle Floating Scratchpad
function _terminaly_scratch_widget() {
    "$TERMINALY_HOME/bin/terminaly" scratch
    zle reset-prompt
}
zle -N _terminaly_scratch_widget
bindkey '^\\' _terminaly_scratch_widget

# Ergonomic command aliases
alias ll="$TERMINALY_HOME/bin/tls -l"
alias lt="$TERMINALY_HOME/bin/tls -t"
alias tree="$TERMINALY_HOME/bin/tls -t"
alias gwt="$TERMINALY_HOME/bin/twt"
