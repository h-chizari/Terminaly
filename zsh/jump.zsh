# Terminaly Smart Directory Jumping (Zoxide equivalent)
# Automatically records visited directories into SQLite frecency database

autoload -Uz add-zsh-hook

function _terminaly_chpwd_record() {
    python3 -c "
import sys, os
sys.path.insert(0, '$TERMINALY_HOME')
try:
    from core.db import record_visit
    record_visit(os.getcwd())
except Exception:
    pass
" 2>/dev/null &!
}

add-zsh-hook chpwd _terminaly_chpwd_record

# Interactive or direct jump command 'z'
function z() {
    if [[ $# -eq 0 ]]; then
        cd ~
        return
    fi

    local query="$*"
    # Query highest frecency match
    local target
    target=$(python3 -c "
import sys
sys.path.insert(0, '$TERMINALY_HOME')
from core.db import query_frecency
res = query_frecency('$query', limit=5)
if res:
    print(res[0][0])
" 2>/dev/null)

    if [[ -n "$target" && -d "$target" ]]; then
        cd "$target"
    else
        # Fall back to interactive fuzzy picker
        local pick
        pick=$(python3 -c "
import sys
sys.path.insert(0, '$TERMINALY_HOME')
from core.db import query_frecency
rows = query_frecency(limit=100)
for r in rows:
    print(r[0])
" 2>/dev/null | "$TERMINALY_HOME/bin/tfzf" --title="Directory Jump (z)" --filter="$query")
        if [[ -n "$pick" && -d "$pick" ]]; then
            cd "$pick"
        else
            echo "z: no matching directory for '$query'" >&2
            return 1
        fi
    fi
}
