#!/usr/bin/env python3
"""Terminaly System Telemetry: Extract native macOS metrics using built-in system tools."""

import os
import re
import shutil
import subprocess
import time
from typing import Dict, Any, Optional

def get_cpu_load() -> float:
    """Returns the 1-minute load average normalized to CPU count percentage."""
    try:
        out = subprocess.check_output(["sysctl", "-n", "vm.loadavg"], text=True, stderr=subprocess.DEVNULL)
        match = re.search(r"\{\s*([\d\.]+)", out)
        if match:
            load = float(match.group(1))
            cpu_count = os.cpu_count() or 1
            return min(100.0, round((load / cpu_count) * 100, 1))
    except Exception:
        pass
    return 0.0

def get_memory_info() -> Dict[str, Any]:
    """Returns memory usage metrics using native macOS vm_stat and sysctl."""
    info = {"used_gb": 0.0, "total_gb": 0.0, "percent": 0.0}
    try:
        total_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True, stderr=subprocess.DEVNULL).strip())
        info["total_gb"] = round(total_bytes / (1024**3), 1)
        
        vm_out = subprocess.check_output(["vm_stat"], text=True, stderr=subprocess.DEVNULL)
        page_size = 4096
        m_page = re.search(r"page size of (\d+) bytes", vm_out)
        if m_page:
            page_size = int(m_page.group(1))
            
        free_pages = 0
        speculative_pages = 0
        for line in vm_out.splitlines():
            if "Pages free:" in line:
                free_pages = int(line.split(":")[1].strip().rstrip("."))
            elif "Pages speculative:" in line:
                speculative_pages = int(line.split(":")[1].strip().rstrip("."))
                
        free_bytes = (free_pages + speculative_pages) * page_size
        used_bytes = max(0, total_bytes - free_bytes)
        info["used_gb"] = round(used_bytes / (1024**3), 1)
        info["percent"] = round((used_bytes / total_bytes) * 100, 1)
    except Exception:
        pass
    return info

def get_battery_info() -> Dict[str, Any]:
    """Returns battery percentage and charging state via pmset."""
    batt = {"percent": 100, "state": "AC", "has_battery": False}
    try:
        out = subprocess.check_output(["pmset", "-g", "batt"], text=True, stderr=subprocess.DEVNULL)
        if "InternalBattery" in out:
            batt["has_battery"] = True
            m_pct = re.search(r"(\d+)%", out)
            if m_pct:
                batt["percent"] = int(m_pct.group(1))
            if "discharging" in out.lower():
                batt["state"] = "Discharging"
            elif "charging" in out.lower():
                batt["state"] = "Charging"
            else:
                batt["state"] = "Charged"
    except Exception:
        pass
    return batt

def get_disk_info(path: str = "/") -> Dict[str, Any]:
    """Returns disk metrics using shutil.disk_usage."""
    try:
        usage = shutil.disk_usage(path)
        total_gb = round(usage.total / (1024**3), 1)
        used_gb = round(usage.used / (1024**3), 1)
        percent = round((usage.used / usage.total) * 100, 1)
        return {"total_gb": total_gb, "used_gb": used_gb, "percent": percent}
    except Exception:
        return {"total_gb": 0.0, "used_gb": 0.0, "percent": 0.0}

def get_git_info(cwd: Optional[str] = None) -> Dict[str, Any]:
    """Inspects git status of a directory without external packages."""
    git_info = {"is_repo": False, "branch": "", "dirty": False, "ahead": 0, "behind": 0, "staged": 0, "untracked": 0}
    target = cwd or os.getcwd()
    try:
        # Check if inside git work tree
        subprocess.check_call(["git", "-C", target, "rev-parse", "--is-inside-work-tree"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        git_info["is_repo"] = True
        
        # Get current branch or commit
        branch = subprocess.check_output(
            ["git", "-C", target, "branch", "--show-current"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        if not branch:
            branch = subprocess.check_output(
                ["git", "-C", target, "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        git_info["branch"] = branch
        
        # Check dirty and porcelain status
        status = subprocess.check_output(
            ["git", "-C", target, "status", "--porcelain", "-b"], text=True, stderr=subprocess.DEVNULL
        ).splitlines()
        
        if status:
            first_line = status[0]
            if "ahead" in first_line:
                m_ah = re.search(r"ahead (\d+)", first_line)
                if m_ah:
                    git_info["ahead"] = int(m_ah.group(1))
            if "behind" in first_line:
                m_bh = re.search(r"behind (\d+)", first_line)
                if m_bh:
                    git_info["behind"] = int(m_bh.group(1))
                    
            for line in status[1:]:
                if line.startswith("??"):
                    git_info["untracked"] += 1
                elif line[0] in "MADRC":
                    git_info["staged"] += 1
                elif line[1] in "MD":
                    git_info["dirty"] = True
                    
            if len(status) > 1:
                git_info["dirty"] = True
    except Exception:
        pass
    return git_info

def get_system_summary() -> str:
    """Returns a single-line status bar summary of system metrics."""
    cpu = get_cpu_load()
    mem = get_memory_info()
    batt = get_battery_info()
    disk = get_disk_info()
    
    parts = [f"CPU: {cpu}%", f"RAM: {mem['percent']}% ({mem['used_gb']}G/{mem['total_gb']}G)", f"Disk: {disk['percent']}%"]
    if batt["has_battery"]:
        icon = "⚡" if batt["state"] == "Charging" else "🔋"
        parts.append(f"{icon} {batt['percent']}%")
    return " | ".join(parts)

if __name__ == "__main__":
    print(get_system_summary())
