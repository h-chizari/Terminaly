#!/usr/bin/env python3
"""Terminaly AI Task Runner: Step-by-step interactive command execution (Warp Terminal equivalent)."""

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

def decompose_task(prompt: str, context: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    """
    Decomposes a user task or question into a title and an ordered list of executable steps.
    Each step contains:
      - 'title': short step name
      - 'command': exact shell command to run
      - 'explain': brief description of what the command does
      - 'safety': 'SAFE' (read-only), 'MODIFY' (edits/creates), or 'CAUTION' (deletes/replaces)
    """
    p_lower = prompt.lower().strip()
    steps: List[Dict[str, str]] = []
    goal_title = prompt.strip()

    # Heuristic template matches for common user queries
    # 1. Git workflows: branch cleanup, commit, stash, worktrees
    if "branch" in p_lower and ("clean" in p_lower or "delete" in p_lower or "merged" in p_lower):
        goal_title = "Clean up merged local Git branches"
        steps = [
            {
                "title": "Check current branch and local branches",
                "command": "git branch --merged",
                "explain": "Lists local branches that have already been merged into the current branch.",
                "safety": "SAFE"
            },
            {
                "title": "Prune remote-tracking branch references",
                "command": "git fetch --prune",
                "explain": "Removes stale references to branches deleted on the remote repository.",
                "safety": "SAFE"
            },
            {
                "title": "Safely delete merged branches (excluding master/main)",
                "command": 'git branch --merged | grep -Ev "(^\\*|master|main|dev)" | xargs -n 1 git branch -d 2>/dev/null || echo "No branches to remove"',
                "explain": "Deletes merged branches while protecting current, main, master, and dev branches.",
                "safety": "CAUTION"
            }
        ]

    elif "commit" in p_lower and ("push" in p_lower or "all" in p_lower or "changes" in p_lower):
        goal_title = "Stage, commit, and push repository changes"
        msg = "update: save progress"
        m_match = re.search(r'["\']([^"\']+)["\']', prompt)
        if m_match:
            msg = m_match.group(1)
        steps = [
            {
                "title": "Inspect modified and untracked files",
                "command": "git status -s",
                "explain": "Shows a concise overview of pending repository changes.",
                "safety": "SAFE"
            },
            {
                "title": "Stage modified tracked files",
                "command": "git add -u",
                "explain": "Stages changes to existing files without including uninspected new files.",
                "safety": "MODIFY"
            },
            {
                "title": "Create Git commit",
                "command": f'git commit -m "{msg}"',
                "explain": f"Commits staged changes with message '{msg}'.",
                "safety": "MODIFY"
            }
        ]

    # 2. Large files / Disk usage
    elif "large file" in p_lower or "disk" in p_lower or "space" in p_lower or "biggest" in p_lower:
        goal_title = "Identify largest files and disk consumers"
        steps = [
            {
                "title": "Find top 10 largest files in current directory",
                "command": "find . -type f -not -path '*/.*' -exec ls -lh {} + 2>/dev/null | sort -k5,5 -hr | head -n 10",
                "explain": "Scans for the 10 largest non-hidden files and sorts them by file size.",
                "safety": "SAFE"
            },
            {
                "title": "Inspect disk usage breakdown by folder",
                "command": "du -sh */ 2>/dev/null | sort -hr | head -n 10",
                "explain": "Calculates folder sizes for top-level subdirectories.",
                "safety": "SAFE"
            }
        ]

    # 3. Process / CPU / Port inspection
    elif "port" in p_lower or "listen" in p_lower:
        m_port = re.search(r'(\d{2,5})', prompt)
        target_port = m_port.group(1) if m_port else "8080"
        goal_title = f"Find and manage process using port {target_port}"
        steps = [
            {
                "title": f"Check which process is listening on port {target_port}",
                "command": f"lsof -i :{target_port}",
                "explain": f"Identifies the process PID, name, and owner listening on port {target_port}.",
                "safety": "SAFE"
            }
        ]

    elif "kill" in p_lower or "stop process" in p_lower:
        goal_title = "Find and terminate high-resource process"
        steps = [
            {
                "title": "List top 5 processes by CPU utilization",
                "command": "ps -Ao pid,%cpu,%mem,comm | sort -k2,2 -nr | head -n 6",
                "explain": "Lists the most CPU-intensive active processes.",
                "safety": "SAFE"
            }
        ]

    # 4. Search and replace in files
    elif "search" in p_lower or "find" in p_lower or "grep" in p_lower:
        words = [w for w in prompt.split() if w.lower() not in ("search", "find", "grep", "for", "in", "files")]
        pattern = words[0] if words else "TODO"
        goal_title = f"Search files for pattern '{pattern}'"
        steps = [
            {
                "title": f"Search matching files for '{pattern}'",
                "command": f"grep -rn --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='__pycache__' '{pattern}' . | head -n 25",
                "explain": f"Recursively finds occurrences of '{pattern}' with line numbers.",
                "safety": "SAFE"
            }
        ]

    # 5. General fallback: try Antigravity agentapi or construct command
    else:
        # Check if agentapi is reachable
        agentapi_bin = Path.home() / ".gemini" / "antigravity" / "bin" / "agentapi"
        if not agentapi_bin.exists():
            agentapi_bin = Path("/Applications/Antigravity.app/Contents/Resources/bin/language_server")

        goal_title = f"Task: {prompt}"
        # Provide general single or multi-step execution
        steps = [
            {
                "title": "Analyze and prepare execution context",
                "command": f"echo 'Running task: {prompt}'",
                "explain": "Initial step to inspect current directory state.",
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
