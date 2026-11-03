"""SQLite persistence layer for the Patient Record System (PRS).

The schema itself enforces the rules the clinic confirmed in Assignment #2,
so the rules hold even if application code is bypassed:

* ``patient_id`` is the PRIMARY KEY (uniqueness, FR-01 / NFR-02) and must be
  exactly five digits (CHECK constraint).
* A trigger aborts any UPDATE that tries to change ``patient_id``
  (immutability, UR-02).
* Foreign keys keep visit notes tied to an existing patient (FR-03 / FR-06).
"""
import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS staff (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY
        CHECK (length(patient_id) = 5 AND patient_id NOT GLOB '*[^0-9]*'),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    date_of_birth TEXT,
    phone TEXT,
    version INTEGER NOT NULL DEFAULT 1
);
CREATE TRIGGER IF NOT EXISTS patients_id_immutable
BEFORE UPDATE OF patient_id ON patients
WHEN NEW.patient_id IS NOT OLD.patient_id
BEGIN
    SELECT RAISE(ABORT, 'patient_id is immutable');
END;
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
CREATE INDEX IF NOT EXISTS idx_visit_notes_patient ON visit_notes(patient_id);
"""


class Database:
    """Owns the SQLite connection and schema. Only repositories use ``conn``."""

    def __init__(self, path="prs_v2.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    @contextmanager
    def transaction(self):
        """Commit on success, roll back on any exception."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def close(self):
        self.conn.close()
