from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from pathlib import Path


WINDOW_SECONDS = 3600


def _db_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "views.sqlite3"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS page_view_counts (
                slug TEXT NOT NULL,
                lang TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (slug, lang)
            );

            CREATE TABLE IF NOT EXISTS page_view_visitors (
                slug TEXT NOT NULL,
                lang TEXT NOT NULL,
                visitor_hash TEXT NOT NULL,
                last_seen_at INTEGER NOT NULL,
                PRIMARY KEY (slug, lang, visitor_hash)
            );

            CREATE INDEX IF NOT EXISTS idx_page_view_visitors_last_seen
            ON page_view_visitors(last_seen_at);
            """
        )


def _normalize_slug(slug: str) -> str:
    value = (slug or "").strip().lower()
    value = re.sub(r"[^a-z0-9\\-_/]", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-/")
    return value[:160] or "unknown"


def _normalize_lang(lang: str) -> str:
    value = (lang or "").strip().lower()
    value = re.sub(r"[^a-z0-9\\-]", "", value)
    return value[:12] or "ko"


def make_visitor_hash(ip: str, user_agent: str, accept_language: str = "") -> str:
    raw = "|".join(
        [
            (ip or "").strip(),
            (user_agent or "").strip()[:300],
            (accept_language or "").strip()[:120],
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_count(slug: str, lang: str) -> int:
    norm_slug = _normalize_slug(slug)
    norm_lang = _normalize_lang(lang)
    with _connect() as conn:
        row = conn.execute(
            "SELECT count FROM page_view_counts WHERE slug = ? AND lang = ?",
            (norm_slug, norm_lang),
        ).fetchone()
        return int(row["count"]) if row else 0


def register_view(slug: str, lang: str, visitor_hash: str) -> dict:
    norm_slug = _normalize_slug(slug)
    norm_lang = _normalize_lang(lang)
    now = int(time.time())
    cutoff = now - WINDOW_SECONDS
    counted = False

    with _connect() as conn:
        conn.execute(
            "DELETE FROM page_view_visitors WHERE last_seen_at < ?",
            (cutoff,),
        )

        row = conn.execute(
            """
            SELECT last_seen_at
            FROM page_view_visitors
            WHERE slug = ? AND lang = ? AND visitor_hash = ?
            """,
            (norm_slug, norm_lang, visitor_hash),
        ).fetchone()

        if row and int(row["last_seen_at"]) >= cutoff:
            conn.execute(
                """
                UPDATE page_view_visitors
                SET last_seen_at = ?
                WHERE slug = ? AND lang = ? AND visitor_hash = ?
                """,
                (now, norm_slug, norm_lang, visitor_hash),
            )
        else:
            counted = True
            conn.execute(
                """
                INSERT INTO page_view_visitors(slug, lang, visitor_hash, last_seen_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(slug, lang, visitor_hash)
                DO UPDATE SET last_seen_at = excluded.last_seen_at
                """,
                (norm_slug, norm_lang, visitor_hash, now),
            )
            conn.execute(
                """
                INSERT INTO page_view_counts(slug, lang, count, updated_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(slug, lang)
                DO UPDATE SET count = count + 1, updated_at = excluded.updated_at
                """,
                (norm_slug, norm_lang, now),
            )

        row = conn.execute(
            "SELECT count FROM page_view_counts WHERE slug = ? AND lang = ?",
            (norm_slug, norm_lang),
        ).fetchone()
        count = int(row["count"]) if row else 0

    return {
        "slug": norm_slug,
        "lang": norm_lang,
        "count": count,
        "counted": counted,
        "window_seconds": WINDOW_SECONDS,
    }
