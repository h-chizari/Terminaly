# Terminaly: Main Zsh Environment Initializer
# Zero external downloads. 100% native macOS.

export TERMINALY_HOME="${0:A:h:h}"
export PATH="$TERMINALY_HOME/bin:$PATH"

# Source modular components
source "$TERMINALY_HOME/zsh/prompt.zsh"
source "$TERMINALY_HOME/zsh/jump.zsh"
source "$TERMINALY_HOME/zsh/history.zsh"
source "$TERMINALY_HOME/zsh/env_manager.zsh"
source "$TERMINALY_HOME/zsh/keybindings.zsh"

# Record initial shell launch directory
if whence -w _terminaly_chpwd_record >/dev/null 2>&1; then
    _terminaly_chpwd_record
fi
