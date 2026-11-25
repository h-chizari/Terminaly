#!/usr/bin/env python3
"""Terminaly AI Task Runner: Step-by-step interactive command execution (Warp Terminal equivalent)."""

import difflib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure core is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.theme import get_active_theme

def get_shell_context() -> Dict[str, Any]:
    """Gathers local terminal context to inform AI task breakdown."""
    cwd = os.getcwd()
    git_info = {"is_git": False, "branch": "", "status": ""}
    try:
        if subprocess.call(["git", "rev-parse", "--is-inside-work-tree"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            git_info["is_git"] = True
            git_info["branch"] = subprocess.check_output(
                ["git", "branch", "--show-current"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            git_info["status"] = subprocess.check_output(
                ["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL
            ).strip()
    except Exception:
        pass

    return {
        "cwd": cwd,
        "os": "macOS",
        "shell": os.environ.get("SHELL", "/bin/zsh"),
        "git": git_info,
        "files_sample": [f.name for f in list(Path(cwd).iterdir())[:10] if not f.name.startswith(".")]
    }

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "up", "about",
    "into", "over", "after", "how", "what", "which", "who", "where", "why",
    "when", "can", "could", "would", "should", "do", "does", "did", "you",
    "we", "i", "me", "my", "our", "your", "it", "its", "here", "there", "this", "that"
}

def has_fuzzy_match(words: List[str], target_keywords: List[str], cutoff: float = 0.78) -> bool:
    """Checks if any word in the user's prompt matches a keyword, even with typos."""
    for w in words:
        clean_w = w.lower().strip(".,!?\"'`:;()")
        if not clean_w or clean_w in STOP_WORDS:
            continue
        if clean_w in target_keywords:
            return True
        # Only fuzzy match words of reasonable length (>= 4) and close length difference
        if len(clean_w) < 4:
            continue
        for target in target_keywords:
            if abs(len(clean_w) - len(target)) > 2:
                continue
            ratio = difflib.SequenceMatcher(None, clean_w, target).ratio()
            if ratio >= cutoff:
                return True
    return False

def decompose_task(prompt: str, context: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    """
    Decomposes a user task or question into a title and an ordered list of executable steps.
    Supports natural language queries, questions, and typo-tolerant intent recognition.
    """
    p_clean = prompt.strip()
    words = p_clean.split()
    p_lower = p_clean.lower()

    # 1. Largest / Biggest / File Size queries (handles "largets", "biggest", "heavy", etc.)
    if has_fuzzy_match(words, ["largest", "biggest", "large", "heaviest", "size"]) and ("file" in p_lower or "folder" in p_lower or "dir" in p_lower or "here" in p_lower):
        goal_title = "Find the largest files in current directory and subfolders"
        steps = [
            {
                "title": "List files in current folder sorted by size (largest first)",
                "command": "ls -lhS | grep -v '^total' | head -n 6",
                "explain": "Lists files in the current directory with human-readable sizes (GB/MB/KB) ordered from largest to smallest.",
                "safety": "SAFE"
            },
            {
                "title": "Find the top 5 largest files recursively across all subfolders",
                "command": "find . -type f -not -path '*/.*' -exec ls -lh {} + 2>/dev/null | sort -k5,5 -hr | head -n 5",
                "explain": "Recursively searches all non-hidden directories to locate the largest files on disk.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    # 2. Smallest / Empty files
    if has_fuzzy_match(words, ["smallest", "tiny"]) and "file" in p_lower:
        goal_title = "Find smallest files in current directory"
        steps = [
            {
                "title": "List files sorted by size (smallest first)",
                "command": "ls -lhrS | grep -v '^total' | head -n 6",
                "explain": "Lists files in ascending size order.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    if has_fuzzy_match(words, ["empty", "blank"]) and ("file" in p_lower or "folder" in p_lower or "dir" in p_lower):
        goal_title = "Find empty files and directories"
        steps = [
            {
                "title": "Locate 0-byte empty files in current directory",
                "command": "find . -maxdepth 2 -type f -empty -not -path '*/.*'",
                "explain": "Searches for empty files that contain 0 bytes.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    # 3. Newest / Latest / Recent files
    if has_fuzzy_match(words, ["newest", "latest", "recent", "modified"]) and ("file" in p_lower or "changes" in p_lower or "here" in p_lower):
        goal_title = "Find most recently modified files"
        steps = [
            {
                "title": "List newest modified files in current directory",
                "command": "ls -lht | head -n 8",
                "explain": "Displays files sorted by modification time with newest items at the top.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    # 4. Count / How many files
    if has_fuzzy_match(words, ["count", "number"]) or ("how" in p_lower and "many" in p_lower):
        goal_title = "Count files and directories"
        steps = [
            {
                "title": "Count total files and folders",
                "command": 'echo "Files: $(find . -maxdepth 1 -type f -not -name ".*" | wc -l | tr -d " ") | Subdirs: $(find . -maxdepth 1 -type d -not -name ".*" | wc -l | tr -d " ")"',
                "explain": "Calculates the count of files and subdirectories in the current directory.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    # 5. Git Workflows
    if has_fuzzy_match(words, ["branch", "branches"]) and has_fuzzy_match(words, ["clean", "delete", "cleanup", "prune", "merged"]):
        goal_title = "Clean up merged local Git branches"
        steps = [
            {
                "title": "Check merged local branches",
                "command": "git branch --merged",
                "explain": "Lists local branches that have already been integrated into current branch.",
                "safety": "SAFE"
            },
            {
                "title": "Prune stale remote branch trackers",
                "command": "git fetch --prune",
                "explain": "Synchronizes local git reference table with deleted remote branches.",
                "safety": "SAFE"
            },
            {
                "title": "Delete merged branches (protecting master/main/dev)",
                "command": 'git branch --merged | grep -Ev "(^\\*|master|main|dev)" | xargs -n 1 git branch -d 2>/dev/null || echo "No merged branches to remove"',
                "explain": "Safely removes merged branches without touching protected branches.",
                "safety": "CAUTION"
            }
        ]
        return goal_title, steps

    if has_fuzzy_match(words, ["commit", "push"]) and has_fuzzy_match(words, ["all", "changes", "save", "sync"]):
        goal_title = "Stage, commit, and push pending changes"
        msg = "chore: update work"
        m_match = re.search(r'["\']([^"\']+)["\']', prompt)
        if m_match:
            msg = m_match.group(1)
        steps = [
            {
                "title": "Review pending modifications",
                "command": "git status -s",
                "explain": "Displays staged and unstaged file modifications.",
                "safety": "SAFE"
            },
            {
                "title": "Stage modified tracked files",
                "command": "git add -u",
                "explain": "Stages changes in tracked files without accidentally adding untracked build artifacts.",
                "safety": "MODIFY"
            },
            {
                "title": "Commit changes",
                "command": f'git commit -m "{msg}"',
                "explain": f"Creates commit with message '{msg}'.",
                "safety": "MODIFY"
            }
        ]
        return goal_title, steps

    if has_fuzzy_match(words, ["diff", "changes", "modified"]) and ("git" in p_lower or context["git"]["is_git"]):
        goal_title = "Inspect uncommitted Git diffs"
        steps = [
            {
                "title": "Display summary of changed lines and files",
                "command": "git diff --stat",
                "explain": "Summarizes insertion and deletion counts for all modified files.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    # 6. Ports & Network
    if has_fuzzy_match(words, ["port", "ports", "listen", "listening"]):
        m_port = re.search(r'(\d{2,5})', prompt)
        if m_port:
            target_port = m_port.group(1)
            goal_title = f"Find and inspect process listening on port {target_port}"
            steps = [
                {
                    "title": f"Identify process holding port {target_port}",
                    "command": f"lsof -i :{target_port}",
                    "explain": f"Displays the PID and application name listening on TCP/UDP port {target_port}.",
                    "safety": "SAFE"
                }
            ]
        else:
            goal_title = "List all active TCP listening ports and services"
            steps = [
                {
                    "title": "List all active listening TCP ports",
                    "command": "lsof -iTCP -sTCP:LISTEN -P -n | head -n 25",
                    "explain": "Lists applications and daemons currently listening for incoming TCP network connections.",
                    "safety": "SAFE"
                }
            ]
        return goal_title, steps

    if has_fuzzy_match(words, ["ip", "address", "network", "wifi"]) and ("my" in p_lower or "what" in p_lower or "local" in p_lower):
        goal_title = "Inspect local and public network IP addresses"
        steps = [
            {
                "title": "Display local LAN IP address",
                "command": "echo 'Local IP: '$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo 'Unknown')",
                "explain": "Queries the macOS network interface for current Wi-Fi/Ethernet IP address.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    # 7. Processes & System Stats
    if has_fuzzy_match(words, ["process", "processes", "top", "cpu", "ram", "memory", "heavy"]):
        goal_title = "Inspect top resource-consuming processes"
        steps = [
            {
                "title": "List top 5 processes by CPU utilization",
                "command": "ps -Ao pid,%cpu,%mem,comm | sort -k2,2 -nr | head -n 6",
                "explain": "Lists active processes sorted by CPU percentage.",
                "safety": "SAFE"
            },
            {
                "title": "List top 5 processes by Memory consumption",
                "command": "ps -Ao pid,%cpu,%mem,comm | sort -k3,3 -nr | head -n 6",
                "explain": "Lists active processes sorted by RAM percentage.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    # 8. File Searching by Name
    if has_fuzzy_match(words, ["where", "locate", "find"]) and not ("large" in p_lower or "biggest" in p_lower):
        # Extract target search term
        cleaned_tokens = [w.strip(".,!?\"'") for w in words if w.lower() not in ("where", "is", "the", "find", "locate", "file", "folder", "here", "in", "a")]
        search_target = cleaned_tokens[0] if cleaned_tokens else "*"
        goal_title = f"Locate files matching '{search_target}'"
        steps = [
            {
                "title": f"Search current directory for files matching '{search_target}'",
                "command": f'find . -iname "*{search_target}*" -not -path "*/.*" | head -n 15',
                "explain": f"Case-insensitive search for files or folders with names containing '{search_target}'.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    # 9. Text Content Search (grep)
    if has_fuzzy_match(words, ["grep", "search", "contains", "mention"]):
        cleaned_tokens = [w.strip(".,!?\"'") for w in words if w.lower() not in ("search", "grep", "for", "text", "contains", "in", "files", "code")]
        pattern = cleaned_tokens[0] if cleaned_tokens else "TODO"
        goal_title = f"Search file contents for '{pattern}'"
        steps = [
            {
                "title": f"Grep for pattern '{pattern}'",
                "command": f"grep -rn --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='__pycache__' '{pattern}' . | head -n 20",
                "explain": f"Recursively scans files for occurrences of '{pattern}' with line numbers.",
                "safety": "SAFE"
            }
        ]
        return goal_title, steps

    # 10. General Intelligent Fallback: Dynamic Synthesizer
    # Extract query intent words and create targeted exploration
    goal_title = f"Task: {p_clean}"
    
    # Check if target is a file in directory
    matched_file = None
    for f in context.get("files_sample", []):
        if f.lower() in p_lower:
            matched_file = f
            break

    if matched_file:
        steps = [
            {
                "title": f"Inspect details of '{matched_file}'",
                "command": f"ls -lh '{matched_file}' && head -n 20 '{matched_file}'",
                "explain": f"Displays file metadata and preview for {matched_file}.",
                "safety": "SAFE"
            }
        ]
    else:
        steps = [
            {
                "title": f"Inspect relevant items in current directory",
                "command": "tls -l",
                "explain": "Lists directory entries with permissions, sizes, and git status.",
                "safety": "SAFE"
            }
        ]

    return goal_title, steps

def run_interactive_workflow(prompt: str):
    """Interactive Warp-style step-by-step terminal executor."""
    theme = get_active_theme()
    ansi = theme.get("ansi", {})
    p = ansi.get("primary", "\033[36m")
    s = ansi.get("secondary", "\033[34m")
    suc = ansi.get("success", "\033[32m")
    warn = ansi.get("warning", "\033[33m")
    dang = ansi.get("danger", "\033[31m")
    acc = ansi.get("accent", "\033[35m")
    b = "\033[1m"
    dim = "\033[2m"
    rst = "\033[0m"

    context = get_shell_context()
    title, steps = decompose_task(prompt, context)

    print(f"\n{b}{p}========================================================================{rst}")
    print(f"{b}{p}  Terminaly AI Workflow: {title}{rst}")
    print(f"{b}{p}========================================================================{rst}")
    print(f"  {dim}Target: {context['cwd']} │ Steps: {len(steps)}{rst}\n")

    run_all = False
    step_idx = 0

    while step_idx < len(steps):
        step = steps[step_idx]
        num = step_idx + 1
        total = len(steps)

        # Safety badge styling
        safety = step.get("safety", "SAFE").upper()
        if safety == "SAFE":
            safety_badge = f"{suc}[SAFE: Read-Only]{rst}"
        elif safety == "MODIFY":
            safety_badge = f"{warn}[MODIFY: Creates/Edits]{rst}"
        else:
            safety_badge = f"{dang}[CAUTION: Permanent Change]{rst}"

        print(f"{b}{acc}┌─ Step {num}/{total}: {step['title']} ─────────────────────────────────{rst}")
        print(f"{b}{acc}│{rst} {b}Command:{rst}  {p}{step['command']}{rst}")
        print(f"{b}{acc}│{rst} {b}Purpose:{rst}  {step['explain']}")
        print(f"{b}{acc}│{rst} {b}Safety:{rst}   {safety_badge}")
        print(f"{b}{acc}└────────────────────────────────────────────────────────────────────────{rst}")

        current_cmd = step['command']

        if not run_all:
            print(f"  {b}Actions:{rst} [r/Enter] Run  [e] Edit  [s] Skip  [a] Run All  [q/Ctrl+C] Quit")
            try:
                choice = input(f"  {p}❯{rst} ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{warn}Workflow cancelled.{rst}")
                return

            if choice in ("q", "quit", "exit"):
                print(f"{warn}Aborted workflow.{rst}\n")
                return
            elif choice in ("s", "skip"):
                print(f"{dim}Skipped Step {num}.{rst}\n")
                step_idx += 1
                continue
            elif choice in ("a", "all"):
                run_all = True
            elif choice in ("e", "edit"):
                try:
                    import readline
                    readline.set_startup_hook(lambda: readline.insert_text(current_cmd))
                    current_cmd = input(f"  {b}Edit Command:{rst} ").strip()
                except Exception:
                    current_cmd = input(f"  {b}New Command:{rst} ").strip()
                finally:
                    try:
                        readline.set_startup_hook(None)
                    except Exception:
                        pass
                if not current_cmd:
                    print(f"{dim}Cancelled edit, skipping.{rst}\n")
                    step_idx += 1
                    continue

        # Execute Command
        print(f"\n{b}{suc}▶ Executing:{rst} {current_cmd}\n")
        start_time = time.time()
        shell_bin = os.environ.get("SHELL", "/bin/zsh")
        proc = subprocess.run([shell_bin, "-c", current_cmd], cwd=context["cwd"])
        elapsed = time.time() - start_time
        exit_code = proc.returncode

        if exit_code == 0:
            print(f"\n{b}{suc}✓ Step {num} completed successfully ({elapsed:.2f}s){rst}\n")
            step_idx += 1
        else:
            print(f"\n{b}{dang}✗ Step {num} failed with exit code {exit_code} ({elapsed:.2f}s){rst}")
            run_all = False
            print(f"  {b}Options:{rst} [r] Retry  [e] Edit  [s] Skip  [q] Abort")
            try:
                err_choice = input(f"  {dang}❯{rst} ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{warn}Workflow aborted.{rst}")
                return
            if err_choice in ("r", "retry", ""):
                continue
            elif err_choice in ("s", "skip"):
                step_idx += 1
                continue
            elif err_choice in ("e", "edit"):
                try:
                    import readline
                    readline.set_startup_hook(lambda: readline.insert_text(current_cmd))
                    steps[step_idx]["command"] = input(f"  {b}Edit Command:{rst} ").strip()
                except Exception:
                    steps[step_idx]["command"] = input(f"  {b}New Command:{rst} ").strip()
                finally:
                    try:
                        readline.set_startup_hook(None)
                    except Exception:
                        pass
                continue
            else:
                print(f"{warn}Aborted workflow.{rst}\n")
                return

    print(f"{b}{suc}========================================================================{rst}")
    print(f"{b}{suc}  ✓ Workflow complete! All steps executed.{rst}")
    print(f"{b}{suc}========================================================================{rst}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ai_task.py '<task or question>'")
        sys.exit(1)
    prompt_arg = " ".join(sys.argv[1:])
    run_interactive_workflow(prompt_arg)
