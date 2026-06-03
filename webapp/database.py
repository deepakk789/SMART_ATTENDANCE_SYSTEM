"""
database.py — SQLite schema, seeding, and query helpers.
All SQL queries live here; app.py only calls these functions.
"""

import sqlite3
import uuid
import hashlib
import pickle
import os
import random
from datetime import datetime, timedelta

import config


# ═══════════════════════════════════════════════════════
#  Connection helper
# ═══════════════════════════════════════════════════════

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ═══════════════════════════════════════════════════════
#  Password utilities
# ═══════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# ═══════════════════════════════════════════════════════
#  Read existing ML dataset students
# ═══════════════════════════════════════════════════════

def get_existing_students() -> list:
    """Return student names already in the face-embedding database."""
    labels_path = os.path.join(config.EMBEDDINGS_DIR, "labels.pkl")
    if os.path.exists(labels_path):
        with open(labels_path, "rb") as f:
            return pickle.load(f)

    emb_path = os.path.join(config.EMBEDDINGS_DIR, "embeddings.pkl")
    if os.path.exists(emb_path):
        with open(emb_path, "rb") as f:
            return list(pickle.load(f).keys())

    # Fallback demo names if no dataset exists yet
    return ["Arjun Sharma", "Priya Patel", "Rahul Verma",
            "Sneha Gupta", "Amit Kumar", "Deepak Singh",
            "Kavya Reddy", "Rohan Mehta"]


# ═══════════════════════════════════════════════════════
#  Schema creation + seeding
# ═══════════════════════════════════════════════════════

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id           TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            email        TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role         TEXT NOT NULL CHECK(role IN ('teacher','student')),
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS classrooms (
            id            TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            subject       TEXT NOT NULL,
            teacher_id    TEXT NOT NULL,
            join_code     TEXT UNIQUE NOT NULL,
            dataset_ready INTEGER DEFAULT 0,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            id              TEXT PRIMARY KEY,
            classroom_id    TEXT NOT NULL,
            student_name    TEXT NOT NULL,
            student_user_id TEXT,
            video_uploaded  INTEGER DEFAULT 0,
            dataset_built   INTEGER DEFAULT 0,
            UNIQUE(classroom_id, student_name),
            FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id                  TEXT PRIMARY KEY,
            classroom_id        TEXT NOT NULL,
            date                TEXT NOT NULL,
            total_present       INTEGER DEFAULT 0,
            total_absent        INTEGER DEFAULT 0,
            image_filename      TEXT,
            result_image_filename TEXT,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (classroom_id) REFERENCES classrooms(id)
        );

        CREATE TABLE IF NOT EXISTS attendance_records (
            id           TEXT PRIMARY KEY,
            session_id   TEXT NOT NULL,
            student_name TEXT NOT NULL,
            status       TEXT NOT NULL CHECK(status IN ('present','absent')),
            FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE
        );
    """)
    conn.commit()

    # Seed once
    row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    if row["c"] == 0:
        _seed_demo(conn)

    conn.close()


def _seed_demo(conn: sqlite3.Connection):
    """Pre-populate teacher account, demo classroom, students and 5 days of attendance."""
    cur = conn.cursor()

    # Teacher account
    cur.execute(
        "INSERT INTO users (id, name, email, password_hash, role) VALUES (?,?,?,?,?)",
        (config.DEMO_TEACHER_ID, "Deepak Singh",
         "deepak@college.edu", hash_password("teacher123"), "teacher"),
    )

    # Demo classroom
    cur.execute(
        "INSERT INTO classrooms (id, name, subject, teacher_id, join_code, dataset_ready)"
        " VALUES (?,?,?,?,?,?)",
        (config.DEMO_CLASSROOM_ID, "B.Tech CS — Section A",
         "Computer Science", config.DEMO_TEACHER_ID, "CS2024A", 1),
    )

    students = get_existing_students()

    # Enroll students
    for s in students:
        cur.execute(
            "INSERT INTO enrollments (id, classroom_id, student_name, video_uploaded, dataset_built)"
            " VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), config.DEMO_CLASSROOM_ID, s, 1, 1),
        )

    # 5 days of historic attendance
    today = datetime.now()
    for days_ago in range(5, 0, -1):
        session_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        session_id   = str(uuid.uuid4())
        present_list = random.sample(students, k=random.randint(max(1, int(len(students)*0.7)), len(students)))
        absent_list  = [s for s in students if s not in present_list]

        cur.execute(
            "INSERT INTO attendance_sessions"
            " (id, classroom_id, date, total_present, total_absent)"
            " VALUES (?,?,?,?,?)",
            (session_id, config.DEMO_CLASSROOM_ID, session_date,
             len(present_list), len(absent_list)),
        )
        for name in present_list:
            cur.execute(
                "INSERT INTO attendance_records (id, session_id, student_name, status)"
                " VALUES (?,?,?,?)",
                (str(uuid.uuid4()), session_id, name, "present"),
            )
        for name in absent_list:
            cur.execute(
                "INSERT INTO attendance_records (id, session_id, student_name, status)"
                " VALUES (?,?,?,?)",
                (str(uuid.uuid4()), session_id, name, "absent"),
            )

    conn.commit()
    print("[DB] Demo data seeded.")


# ═══════════════════════════════════════════════════════
#  Auth helpers
# ═══════════════════════════════════════════════════════

def create_session(user_id: str) -> str:
    token = str(uuid.uuid4())
    conn  = get_db()
    conn.execute("INSERT INTO sessions (token, user_id) VALUES (?,?)", (token, user_id))
    conn.commit()
    conn.close()
    return token

def get_user_by_token(token: str) -> dict | None:
    conn = get_db()
    row  = conn.execute(
        "SELECT u.id, u.name, u.email, u.role FROM sessions s"
        " JOIN users u ON u.id = s.user_id WHERE s.token = ?",
        (token,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def delete_session(token: str):
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()
