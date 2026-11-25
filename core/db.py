#!/usr/bin/env python3
"""Terminaly Database Layer: SQLite persistence for history, frecency, and project environments."""

import os
import sqlite3
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

TERMINALY_DEFAULT_DIR = Path.home() / ".terminaly"
FALLBACK_DIR = Path(__file__).resolve().parent.parent / ".terminaly_data"

def get_terminaly_dir() -> Path:
    env_dir = os.environ.get("TERMINALY_DIR")
    if env_dir:
        return Path(env_dir)
    return TERMINALY_DEFAULT_DIR

def ensure_terminaly_dir() -> Path:
    target = get_terminaly_dir()
    try:
        target.mkdir(parents=True, exist_ok=True)
        return target
    except (PermissionError, OSError):
        FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        return FALLBACK_DIR

def get_db_path(filename: str) -> Path:
    return ensure_terminaly_dir() / filename

def get_db_connection(db_filename: str) -> sqlite3.Connection:
    db_path = get_db_path(db_filename)
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

# ==================== FRECENCY DB ====================

def init_frecency_db() -> None:
    with get_db_connection("frecency.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS directories (
                path TEXT PRIMARY KEY,
                score REAL DEFAULT 1.0,
                count INTEGER DEFAULT 1,
                last_accessed REAL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_frecency_score ON directories(score DESC);")

def record_visit(dir_path: str) -> None:
    abs_path = os.path.abspath(os.path.expanduser(dir_path))
    if not os.path.isdir(abs_path):
        return
    init_frecency_db()
    now = time.time()
    with get_db_connection("frecency.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT score, count, last_accessed FROM directories WHERE path = ?", (abs_path,))
        row = cursor.fetchone()
        if row:
            old_score, count, last_acc = row
            time_delta = max(0.0, now - last_acc)
            decay = 1.0 / (1.0 + (time_delta / 86400.0))
            new_score = (old_score * decay) + 10.0
            new_count = count + 1
            cursor.execute(
                "UPDATE directories SET score = ?, count = ?, last_accessed = ? WHERE path = ?",
                (new_score, new_count, now, abs_path)
            )
        else:
            cursor.execute(
                "INSERT INTO directories (path, score, count, last_accessed) VALUES (?, 10.0, 1, ?)",
                (abs_path, now)
            )
        conn.commit()

def query_frecency(pattern: Optional[str] = None, limit: int = 50) -> List[Tuple[str, float]]:
    init_frecency_db()
    with get_db_connection("frecency.db") as conn:
        cursor = conn.cursor()
        if not pattern:
            cursor.execute("SELECT path, score FROM directories ORDER BY score DESC LIMIT ?", (limit,))
        else:
            tokens = pattern.strip().split()
            where_clauses = ["path LIKE ?" for _ in tokens]
            params: List[Any] = [f"%{tok}%" for tok in tokens]
            params.append(limit)
            query = f"SELECT path, score FROM directories WHERE {' AND '.join(where_clauses)} ORDER BY score DESC LIMIT ?"
            cursor.execute(query, params)
        rows = cursor.fetchall()
        return [(r[0], r[1]) for r in rows if os.path.isdir(r[0])]

# ==================== PERSISTENT HISTORY DB ====================

def init_history_db() -> None:
    with get_db_connection("history.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                directory TEXT NOT NULL,
                timestamp REAL NOT NULL,
                exit_code INTEGER DEFAULT 0,
                duration REAL DEFAULT 0.0,
                session_id TEXT DEFAULT ''
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cmd_timestamp ON commands(timestamp DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cmd_dir ON commands(directory);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cmd_text ON commands(command);")

def record_command(command: str, directory: str, timestamp: float,
                   exit_code: int = 0, duration: float = 0.0,
                   session_id: str = "") -> None:
    cmd_clean = command.strip()
    if not cmd_clean:
        return
    init_history_db()
    with get_db_connection("history.db") as conn:
        conn.execute(
            """INSERT INTO commands (command, directory, timestamp, exit_code, duration, session_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cmd_clean, directory, timestamp, exit_code, duration, session_id)
        )
        conn.commit()

def search_history(query: Optional[str] = None, directory: Optional[str] = None,
                   limit: int = 200) -> List[Dict[str, Any]]:
    init_history_db()
    with get_db_connection("history.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        clauses = []
        params: List[Any] = []
        
        if query:
            for tok in query.strip().split():
                clauses.append("command LIKE ?")
                params.append(f"%{tok}%")
                
        if directory:
            clauses.append("directory = ?")
            params.append(directory)
            
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT id, command, directory, timestamp, exit_code, duration, session_id FROM commands {where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_history_stats() -> Dict[str, Any]:
    init_history_db()
    with get_db_connection("history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT command) FROM commands")
        total_runs, unique_cmds = cursor.fetchone()
        cursor.execute("SELECT command, COUNT(*) as c FROM commands GROUP BY command ORDER BY c DESC LIMIT 10")
        top_cmds = cursor.fetchall()
        return {
            "total_commands": total_runs or 0,
            "unique_commands": unique_cmds or 0,
            "top_commands": top_cmds or []
        }
