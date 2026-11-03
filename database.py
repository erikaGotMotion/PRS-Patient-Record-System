"""SQLite persistence layer for the Patient Record System (PRS)."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS staff (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    date_of_birth TEXT,
    phone TEXT,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS patient_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);
CREATE TABLE IF NOT EXISTS visit_notes (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    visit_date TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);
"""


class Database:
    def __init__(self, path="prs.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()
