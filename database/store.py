import sqlite3
import time
from contextlib import contextmanager
from typing import Any

from core.config import settings


@contextmanager
def connect():
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_seen INTEGER NOT NULL,
                last_seen INTEGER NOT NULL,
                aspect_ratio TEXT NOT NULL DEFAULT '1:1',
                image_count INTEGER NOT NULL DEFAULT 1,
                last_prompt TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                aspect_ratio TEXT NOT NULL,
                image_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                cost REAL DEFAULT 0,
                duration_ms INTEGER DEFAULT 0,
                error_code TEXT,
                created_at INTEGER NOT NULL
            )
            """
        )


def touch_user(user_id: int) -> None:
    now = int(time.time())
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, first_seen, last_seen)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET last_seen = excluded.last_seen
            """,
            (user_id, now, now),
        )


def get_user_settings(user_id: int) -> dict[str, Any]:
    touch_user(user_id)
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row)


def set_aspect_ratio(user_id: int, aspect_ratio: str) -> None:
    touch_user(user_id)
    with connect() as conn:
        conn.execute("UPDATE users SET aspect_ratio = ? WHERE user_id = ?", (aspect_ratio, user_id))


def set_image_count(user_id: int, image_count: int) -> None:
    touch_user(user_id)
    with connect() as conn:
        conn.execute("UPDATE users SET image_count = ? WHERE user_id = ?", (image_count, user_id))


def set_last_prompt(user_id: int, prompt: str) -> None:
    touch_user(user_id)
    with connect() as conn:
        conn.execute("UPDATE users SET last_prompt = ? WHERE user_id = ?", (prompt, user_id))


def log_generation(
    user_id: int,
    prompt: str,
    aspect_ratio: str,
    image_count: int,
    status: str,
    cost: float = 0.0,
    duration_ms: int = 0,
    error_code: str | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO generations
            (user_id, prompt, aspect_ratio, image_count, status, cost, duration_ms, error_code, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, prompt[:2000], aspect_ratio, image_count, status, float(cost or 0), duration_ms, error_code, int(time.time())),
        )


def admin_stats() -> dict[str, Any]:
    with connect() as conn:
        total_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        total_generations = conn.execute("SELECT COUNT(*) AS c FROM generations WHERE status = 'success'").fetchone()["c"]
        failed_generations = conn.execute("SELECT COUNT(*) AS c FROM generations WHERE status != 'success'").fetchone()["c"]
        total_cost = conn.execute("SELECT COALESCE(SUM(cost), 0) AS c FROM generations").fetchone()["c"]
        today_start = int(time.time()) - 86400
        today_generations = conn.execute(
            "SELECT COUNT(*) AS c FROM generations WHERE status = 'success' AND created_at >= ?",
            (today_start,),
        ).fetchone()["c"]
        avg_ms = conn.execute(
            "SELECT COALESCE(AVG(duration_ms), 0) AS c FROM generations WHERE status = 'success' AND duration_ms > 0"
        ).fetchone()["c"]
        recent_errors = conn.execute(
            """
            SELECT error_code, COUNT(*) AS c
            FROM generations
            WHERE status != 'success' AND error_code IS NOT NULL
            GROUP BY error_code
            ORDER BY c DESC
            LIMIT 5
            """
        ).fetchall()
    return {
        "total_users": total_users,
        "total_generations": total_generations,
        "failed_generations": failed_generations,
        "today_generations": today_generations,
        "total_cost": float(total_cost or 0),
        "avg_ms": int(avg_ms or 0),
        "recent_errors": [(row["error_code"], row["c"]) for row in recent_errors],
    }
