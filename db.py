"""Database connection helpers."""
import sqlite3
import os
from config import WEBAPP_DB, YCCD_DB


def get_webapp_db():
    """Get connection to webapp.db (read-write)."""
    conn = sqlite3.connect(WEBAPP_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_yccd_db():
    """Get connection to yccd.db (read-only)."""
    conn = sqlite3.connect(f"file:{YCCD_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def init_webapp_db():
    """Create webapp.db tables if they don't exist."""
    conn = get_webapp_db()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        lop INTEGER DEFAULT 1,
        avatar TEXT DEFAULT 'default',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lop INTEGER NOT NULL,
        tuan INTEGER NOT NULL,
        section TEXT NOT NULL DEFAULT 'practice',
        sort_order INTEGER NOT NULL DEFAULT 0,
        exercise_type TEXT NOT NULL,
        title_vi TEXT NOT NULL,
        title_en TEXT,
        instruction_vi TEXT NOT NULL,
        instruction_en TEXT,
        hint_vi TEXT,
        hint_en TEXT,
        config TEXT NOT NULL DEFAULT '{}',
        images TEXT DEFAULT '[]',
        yccd_ids TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_by INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        exercise_id INTEGER NOT NULL REFERENCES exercises(id),
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        answers TEXT DEFAULT '{}',
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lop INTEGER NOT NULL,
        tuan INTEGER NOT NULL,
        word_en TEXT NOT NULL,
        word_vi TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS week_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lop INTEGER NOT NULL,
        tuan INTEGER NOT NULL,
        title_vi TEXT,
        title_en TEXT,
        chu_de_vi TEXT,
        chu_de_en TEXT,
        yccd_summary TEXT DEFAULT '[]',
        UNIQUE(lop, tuan)
    );

    CREATE TABLE IF NOT EXISTS exercise_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        exercise_type TEXT NOT NULL,
        instruction_template TEXT NOT NULL DEFAULT '',
        default_config TEXT NOT NULL DEFAULT '{}',
        sample_config TEXT NOT NULL DEFAULT '{}',
        applicable_grades TEXT NOT NULL DEFAULT '[1,2,3,4,5]',
        tags TEXT NOT NULL DEFAULT '[]',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_exercises_lop_tuan ON exercises(lop, tuan);
    CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id);
    CREATE INDEX IF NOT EXISTS idx_results_exercise ON results(exercise_id);
    CREATE INDEX IF NOT EXISTS idx_vocabulary_lop_tuan ON vocabulary(lop, tuan);
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_webapp_db()
    print(f"webapp.db initialized at {WEBAPP_DB}")
