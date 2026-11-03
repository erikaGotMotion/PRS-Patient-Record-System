"""Data access for patients."""
from datetime import datetime
from .models import Patient


class PatientRepository:
    def __init__(self, db):
        self.db = db

    def insert(self, patient):
        self.db.conn.execute(
            "INSERT INTO patients (patient_id, name, date_of_birth, phone, version) "
            "VALUES (?,?,?,?,?)",
            (patient.patient_id, patient.name, patient.date_of_birth,
             patient.phone, patient.version))
        self.db.conn.commit()

    def find_by_id(self, patient_id):
        row = self.db.conn.execute(
            "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
        if row is None:
            return None
        return Patient(row["patient_id"], row["name"], row["date_of_birth"],
                       row["phone"], row["version"])

    def exists(self, patient_id):
        return self.db.conn.execute(
            "SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,)).fetchone() is not None

    def update_fields(self, patient_id, changes, expected_version, changed_by):
        """Apply changes only if version still matches. Returns True on success."""
        current = self.find_by_id(patient_id)
        sets = ", ".join(f"{col} = ?" for col in changes)
        cur = self.db.conn.execute(
            f"UPDATE patients SET {sets}, version = version + 1 "
            f"WHERE patient_id = ? AND version = ?",
            (*changes.values(), patient_id, expected_version))
        if cur.rowcount == 0:
            self.db.conn.rollback()
            return False
        for field, new in changes.items():
            self.db.conn.execute(
                "INSERT INTO patient_history (patient_id, field, old_value, new_value, "
                "changed_by, changed_at) VALUES (?,?,?,?,?,?)",
                (patient_id, field, getattr(current, field), new, changed_by,
                 datetime.now().isoformat(timespec="seconds")))
        self.db.conn.commit()
        return True

    def get_history(self, patient_id):
        return self.db.conn.execute(
            "SELECT * FROM patient_history WHERE patient_id = ? ORDER BY history_id",
            (patient_id,)).fetchall()
