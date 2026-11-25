#!/usr/bin/env zsh
# Terminaly Installer & Health Check Script
# 100% Offline, Zero Downloads.

set -e

SCRIPT_DIR="$(cd "$(dirname "${(%):-%N}")" && pwd)"
echo "\033[1m\033[36m====================================================\033[0m"
echo "\033[1m\033[36m     Terminaly: macOS Native Terminal Suite         \033[0m"
echo "\033[1m\033[36m====================================================\033[0m"
echo "Root directory: $SCRIPT_DIR"

# 1. Check prerequisites
echo "\nChecking system requirements..."
python3 -c "import curses, sqlite3, pty, termios; print('✓ Python 3 stdlib modules: curses, sqlite3, pty, termios OK')"
git --version | awk '{print "✓ Git version: " $0}'
/bin/zsh --version | awk '{print "✓ Zsh version: " $0}'
/usr/bin/vim --version | head -n 1 | awk '{print "✓ Native Vim:  " $0}'

# 2. Make binaries executable
chmod +x "$SCRIPT_DIR/bin/"*

# 3. Initialize ~/.terminaly
if mkdir -p "$HOME/.terminaly" 2>/dev/null; then
    echo "✓ Initialized configuration directory: $HOME/.terminaly"
else
    mkdir -p "$SCRIPT_DIR/.terminaly_data"
    export TERMINALY_DIR="$SCRIPT_DIR/.terminaly_data"
    echo "✓ Initialized fallback database directory: $SCRIPT_DIR/.terminaly_data"
fi

python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from core.db import init_frecency_db, init_history_db
init_frecency_db()
init_history_db()
print('✓ Initialized SQLite databases: frecency.db & history.db')
"

# 4. Configure Vim
if [[ ! -f "$HOME/.vimrc" ]] && touch "$HOME/.vimrc" 2>/dev/null; then
    rm -f "$HOME/.vimrc"
    ln -s "$SCRIPT_DIR/vim/vimrc" "$HOME/.vimrc"
    echo "✓ Linked $SCRIPT_DIR/vim/vimrc -> ~/.vimrc"
else
    echo "✓ Found existing ~/.vimrc (or sandboxed). You can load Terminaly vim with: vim -u $SCRIPT_DIR/vim/vimrc"
fi

# 5. Non-destructive integration with ~/.zshrc
ZSHRC="$HOME/.zshrc"
SOURCE_LINE="source \"$SCRIPT_DIR/zsh/terminaly.zsh\""

if [[ -f "$ZSHRC" ]] && grep -Fq "$SOURCE_LINE" "$ZSHRC" 2>/dev/null; then
    echo "✓ Terminaly is already configured in $ZSHRC"
elif touch "$ZSHRC" 2>/dev/null; then
    echo "\n# Terminaly Native Suite\n$SOURCE_LINE" >> "$ZSHRC"
    echo "✓ Added Terminaly hook to $ZSHRC"
else
    echo "✓ Sandboxed environment: To activate in your host shell, add to your ~/.zshrc:"
    echo "    $SOURCE_LINE"
fi

echo "\n\033[32mInstallation complete!\033[0m"
echo "To activate immediately in your current terminal session, run:"
echo "  \033[1msource ~/.zshrc\033[0m"
echo ""
echo "To inspect all features:"
echo "  \033[1mterminaly doctor\033[0m"
echo "  \033[1mtls -t\033[0m              # Tree listing"
echo "  \033[1mtq -h\033[0m               # Query structured data"
echo "  \033[1mtboard\033[0m              # Parallel AI agent & worktree dashboard"
echo "  \033[1mtfm\033[0m                 # Dual-pane file manager"
echo "  \033[1mtwt list\033[0m            # Git worktree lifecycle"
echo "  \033[1mtai ask \"<prompt>\"\033[0m  # Antigravity AI coding bridge"
echo ""
