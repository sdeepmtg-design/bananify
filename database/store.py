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


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


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
                last_prompt TEXT,
                credits INTEGER NOT NULL DEFAULT 0,
                free_used INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        for column, ddl in [
            ("credits", "ALTER TABLE users ADD COLUMN credits INTEGER NOT NULL DEFAULT 0"),
            ("free_used", "ALTER TABLE users ADD COLUMN free_used INTEGER NOT NULL DEFAULT 0"),
        ]:
            if not _column_exists(conn, "users", column):
                conn.execute(ddl)

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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                package_id TEXT NOT NULL,
                credits INTEGER NOT NULL,
                stars INTEGER NOT NULL,
                telegram_payment_charge_id TEXT,
                provider_payment_charge_id TEXT,
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


def user_balance_text(user_id: int) -> str:
    user = get_user_settings(user_id)
    free_status = "использована" if int(user.get("free_used") or 0) else "доступна"
    return (
        "👤 Профиль\n\n"
        f"🎁 Бесплатная генерация: {free_status}\n"
        f"💎 Платных изображений осталось: {int(user.get('credits') or 0)}\n"
        f"📐 Формат: {user['aspect_ratio']}\n"
        f"🔢 Количество: {user['image_count']}"
    )


def add_credits(user_id: int, credits: int) -> None:
    touch_user(user_id)
    with connect() as conn:
        conn.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (int(credits), user_id))


def consume_generation_credits(user_id: int, image_count: int) -> tuple[bool, str, str]:
    """Returns (ok, charge_type, message). charge_type: paid, free, none."""
    touch_user(user_id)
    image_count = max(1, int(image_count))
    with connect() as conn:
        row = conn.execute("SELECT credits, free_used FROM users WHERE user_id = ?", (user_id,)).fetchone()
        credits = int(row["credits"] or 0)
        free_used = int(row["free_used"] or 0)

        if credits >= image_count:
            conn.execute("UPDATE users SET credits = credits - ? WHERE user_id = ?", (image_count, user_id))
            return True, "paid", ""

        if not free_used and image_count == 1:
            conn.execute("UPDATE users SET free_used = 1 WHERE user_id = ?", (user_id,))
            return True, "free", ""

    if not free_used and image_count > 1:
        return (
            False,
            "none",
            "🎁 У тебя доступна 1 бесплатная генерация.\n\n"
            "Выбери количество 1 или купи пакет изображений, чтобы генерировать сразу несколько.",
        )

    return (
        False,
        "none",
        "💳 На балансе недостаточно изображений.\n\n"
        "Купи пакет, чтобы продолжить генерацию.",
    )


def refund_generation_credits(user_id: int, image_count: int, charge_type: str) -> None:
    if charge_type == "paid":
        add_credits(user_id, image_count)
    elif charge_type == "free":
        with connect() as conn:
            conn.execute("UPDATE users SET free_used = 0 WHERE user_id = ?", (user_id,))


def record_payment(
    user_id: int,
    package_id: str,
    credits: int,
    stars: int,
    telegram_payment_charge_id: str | None = None,
    provider_payment_charge_id: str | None = None,
) -> None:
    touch_user(user_id)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO payments
            (user_id, package_id, credits, stars, telegram_payment_charge_id, provider_payment_charge_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                package_id,
                int(credits),
                int(stars),
                telegram_payment_charge_id,
                provider_payment_charge_id,
                int(time.time()),
            ),
        )
        conn.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (int(credits), user_id))


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
        free_used = conn.execute("SELECT COUNT(*) AS c FROM users WHERE free_used = 1").fetchone()["c"]
        total_paid_credits = conn.execute("SELECT COALESCE(SUM(credits), 0) AS c FROM payments").fetchone()["c"]
        total_stars = conn.execute("SELECT COALESCE(SUM(stars), 0) AS c FROM payments").fetchone()["c"]
        buyers = conn.execute("SELECT COUNT(DISTINCT user_id) AS c FROM payments").fetchone()["c"]
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
        "free_used": int(free_used or 0),
        "total_paid_credits": int(total_paid_credits or 0),
        "total_stars": int(total_stars or 0),
        "buyers": int(buyers or 0),
        "recent_errors": [(row["error_code"], row["c"]) for row in recent_errors],
    }
