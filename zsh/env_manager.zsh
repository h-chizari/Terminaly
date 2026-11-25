# Terminaly Per-Project Environment Auto-Loader (Mise equivalent)
# Safely loads project variables on entry and unloads on exit with SHA256 verification

typeset -ga _TERMINALY_LOADED_ENV_VARS=()
typeset -g _TERMINALY_TRUSTED_ENV_FILE="$HOME/.terminaly/trusted_envs"

function _terminaly_unload_prev_env() {
    if (( ${#_TERMINALY_LOADED_ENV_VARS} > 0 )); then
        for var in "${_TERMINALY_LOADED_ENV_VARS[@]}"; do
            unset "$var"
        done
        _TERMINALY_LOADED_ENV_VARS=()
    fi
}

function _terminaly_chpwd_env() {
    _terminaly_unload_prev_env

    local env_file=""
    if [[ -f ".terminaly-env" ]]; then
        env_file=".terminaly-env"
    elif [[ -f ".env" ]]; then
        env_file=".env"
    fi

    [[ -z "$env_file" ]] && return

    local full_path="$PWD/$env_file"
    mkdir -p "$HOME/.terminaly"
    touch "$_TERMINALY_TRUSTED_ENV_FILE"

    # Compute SHA256 hash
    local hash
    hash=$(shasum -a 256 "$full_path" 2>/dev/null | awk '{print $1}')
    local entry="$full_path:$hash"

    if ! grep -Fxq "$entry" "$_TERMINALY_TRUSTED_ENV_FILE" 2>/dev/null; then
        echo -n "\033[1m\033[33mTerminaly:\033[0m Untrusted or modified env file detected ($env_file). Load environment? [y/N] "
        read -q response
        echo
        if [[ "$response" == "y" || "$response" == "Y" ]]; then
            echo "$entry" >> "$_TERMINALY_TRUSTED_ENV_FILE"
        else
            echo "\033[31mSkipped loading $env_file.\033[0m"
            return
        fi
    fi

    # Load environment variables safely
    while IFS='=' read -r key val || [[ -n "$key" ]]; do
        # Ignore comments and empty lines
        [[ "$key" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue
        
        # Clean key and val
        key=$(echo "$key" | tr -d '[:space:]')
        val=$(echo "$val" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'"'"']//' -e 's/["'"'"']$//')
        
        if [[ -n "$key" && "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
            export "$key=$val"
            _TERMINALY_LOADED_ENV_VARS+=("$key")
        fi
    done < "$env_file"

    echo "\033[32m✓ Terminaly: Loaded ${#_TERMINALY_LOADED_ENV_VARS} environment variables from $env_file\033[0m"
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd _terminaly_chpwd_env
