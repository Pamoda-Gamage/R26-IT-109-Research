from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "local_service_discovery.db"

PROVIDER_ROWS = [
    ("Nimal", "Perera", "plumber", "Colombo", 6.9271, 79.8612, 4.8, 0.94, 18, 0.91, "online", 248, 0.92, 0.32, "+94710000001"),
    ("Saman", "Silva", "plumber", "Maharagama", 6.8480, 79.9265, 4.6, 0.88, 24, 0.84, "online", 133, 0.86, 0.18, "+94710000002"),
    ("Kamal", "Fernando", "electrician", "Colombo", 6.9147, 79.8721, 4.9, 0.96, 16, 0.94, "online", 311, 0.95, 0.41, "+94710000003"),
    ("Priyantha", "Jayasekara", "electrician", "Kandy", 7.2906, 80.6337, 4.5, 0.83, 34, 0.78, "busy", 91, 0.81, 0.21, "+94710000004"),
    ("Aruna", "Kumara", "mechanic", "Colombo", 6.9320, 79.8478, 4.7, 0.90, 22, 0.87, "online", 207, 0.89, 0.27, "+94710000005"),
    ("Ravi", "Nathan", "mechanic", "Jaffna", 9.6615, 80.0255, 4.4, 0.81, 38, 0.72, "online", 75, 0.77, 0.12, "+94710000006"),
    ("Asha", "De Silva", "hospital", "Colombo", 6.9180, 79.8650, 4.9, 0.98, 12, 0.97, "online", 510, 0.97, 0.55, "+94710000007"),
    ("Dr. Meera", "Raman", "hospital", "Kandy", 7.2950, 80.6350, 4.8, 0.95, 20, 0.92, "online", 402, 0.93, 0.43, "+94710000008"),
    ("Lal", "Wijesinghe", "taxi", "Colombo", 6.9300, 79.8500, 4.6, 0.88, 10, 0.82, "online", 880, 0.87, 0.68, "+94710000009"),
    ("Fathima", "Nazeer", "taxi", "Negombo", 7.2083, 79.8358, 4.7, 0.90, 14, 0.86, "online", 641, 0.89, 0.38, "+94710000010"),
    ("Officer", "Support", "police", "Colombo", 6.9350, 79.8420, 5.0, 0.99, 8, 0.98, "online", 1200, 0.99, 0.50, "119"),
    ("Fire", "Response", "fire", "Colombo", 6.9345, 79.8428, 5.0, 0.99, 7, 0.99, "online", 1100, 0.99, 0.47, "110"),
    ("Mala", "Ranasinghe", "cleaning", "Colombo", 6.9220, 79.8600, 4.6, 0.85, 40, 0.70, "online", 164, 0.82, 0.10, "+94710000013"),
    ("Dinesh", "Raj", "cleaning", "Galle", 6.0535, 80.2210, 4.5, 0.82, 45, 0.66, "offline", 88, 0.75, 0.07, "+94710000014"),
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                service_category TEXT NOT NULL,
                city TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                rating REAL NOT NULL,
                reliability REAL NOT NULL,
                response_speed_minutes REAL NOT NULL,
                urgent_task_success_rate REAL NOT NULL,
                current_status TEXT NOT NULL,
                completed_jobs INTEGER NOT NULL,
                trust_score REAL NOT NULL,
                fairness_load_index REAL NOT NULL,
                phone_number TEXT UNIQUE NOT NULL,
                preferred_language TEXT DEFAULT 'English',
                voice_phrase TEXT DEFAULT '',
                profile_photo_url TEXT DEFAULT NULL
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM providers").fetchone()[0]
        if count == 0:
            conn.executemany(
                """
                INSERT INTO providers (
                    first_name, last_name, service_category, city, latitude, longitude, rating, reliability,
                    response_speed_minutes, urgent_task_success_rate, current_status, completed_jobs, trust_score,
                    fairness_load_index, phone_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                PROVIDER_ROWS,
            )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS service_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcript TEXT NOT NULL,
                intent TEXT NOT NULL,
                urgency TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                success_probability REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def list_providers(service_category: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        if service_category:
            rows = conn.execute("SELECT * FROM providers WHERE service_category = ?", (service_category,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM providers ORDER BY service_category, rating DESC").fetchall()
    return [row_to_dict(r) for r in rows]


def get_provider_by_phone(phone_number: str) -> Optional[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM providers WHERE phone_number = ?", (phone_number,)).fetchone()
    return row_to_dict(row) if row else None


def create_or_partial_provider(data: Dict[str, Any]) -> Dict[str, Any]:
    init_db()
    existing = get_provider_by_phone(data.get("phone_number", ""))
    if existing:
        return existing
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO providers (
                first_name, last_name, service_category, city, latitude, longitude, rating, reliability,
                response_speed_minutes, urgent_task_success_rate, current_status, completed_jobs, trust_score,
                fairness_load_index, phone_number, preferred_language, voice_phrase, profile_photo_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("first_name") or "Pending",
                data.get("last_name") or "Provider",
                data.get("service_category") or "pending",
                data.get("city") or "Pending City",
                float(data.get("latitude") or 6.9271),
                float(data.get("longitude") or 79.8612),
                4.0,
                0.70,
                35,
                0.60,
                "online",
                0,
                0.70,
                0.0,
                data["phone_number"],
                data.get("preferred_language") or "English",
                data.get("voice_phrase") or "",
                data.get("profile_photo_url"),
            ),
        )
        conn.commit()
        pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        row = conn.execute("SELECT * FROM providers WHERE id = ?", (pid,)).fetchone()
    return row_to_dict(row)


def save_request(transcript: str, intent: str, urgency: str, latitude: float | None, longitude: float | None, success_probability: float) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO service_requests (transcript, intent, urgency, latitude, longitude, success_probability) VALUES (?, ?, ?, ?, ?, ?)",
            (transcript, intent, urgency, latitude, longitude, success_probability),
        )
        conn.commit()


def list_requests(limit: int = 25) -> List[Dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM service_requests ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [row_to_dict(r) for r in rows]
