"""Data access for visit notes."""
from datetime import datetime
from .models import VisitNote


class VisitRepository:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _to_note(row):
        return VisitNote(row["note_id"], row["patient_id"], row["visit_date"],
                         row["description"], row["category"], row["created_by"],
                         row["created_at"])

    def insert(self, patient_id, visit_date, description, created_by):
        cur = self.db.conn.execute(
            "INSERT INTO visit_notes (patient_id, visit_date, description, created_by, "
            "created_at) VALUES (?,?,?,?,?)",
            (patient_id, visit_date, description, created_by,
             datetime.now().isoformat(timespec="seconds")))
        self.db.conn.commit()
        return self.find_by_id(cur.lastrowid)

    def find_by_id(self, note_id):
        row = self.db.conn.execute(
            "SELECT * FROM visit_notes WHERE note_id = ?", (note_id,)).fetchone()
        return self._to_note(row) if row else None

    def find_by_patient(self, patient_id):
        rows = self.db.conn.execute(
            "SELECT * FROM visit_notes WHERE patient_id = ? ORDER BY visit_date, note_id",
            (patient_id,)).fetchall()
        return [self._to_note(r) for r in rows]

    def set_category(self, note_id, category):
        self.db.conn.execute(
            "UPDATE visit_notes SET category = ? WHERE note_id = ?", (category, note_id))
        self.db.conn.commit()
