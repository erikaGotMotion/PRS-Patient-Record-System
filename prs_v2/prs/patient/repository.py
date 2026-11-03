"""Data access for patients. The only patient module that contains SQL."""
import sqlite3
from datetime import datetime
from .errors import DuplicatePatientIdError
from .models import Patient


class PatientRepository:
    def __init__(self, db):
        self._db = db

    def insert(self, patient):
        try:
            with self._db.transaction() as conn:
                conn.execute(
                    "INSERT INTO patients (patient_id, name, date_of_birth, phone, version) "
                    "VALUES (?,?,?,?,?)",
                    (patient.patient_id, patient.name, patient.date_of_birth,
                     patient.phone, patient.version))
        except sqlite3.IntegrityError as exc:
            raise DuplicatePatientIdError(
                f"Patient ID {patient.patient_id} is already in use") from exc

    def find_by_id(self, patient_id):
        row = self._db.conn.execute(
            "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
        if row is None:
            return None
        return Patient(row["patient_id"], row["name"], row["date_of_birth"],
                       row["phone"], row["version"])

    def exists(self, patient_id):
        return self._db.conn.execute(
            "SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,)).fetchone() is not None

    def update_fields(self, patient_id, changes, expected_version, changed_by):
        """Apply ``changes`` only if the stored version still matches.

        The update and its history rows commit together or not at all.
        Returns True on success, False if the version was stale.
        """
        unknown = set(changes) - set(Patient.EDITABLE_FIELDS)
        if unknown:
            raise ValueError(f"Fields cannot be updated: {', '.join(sorted(unknown))}")
        with self._db.transaction() as conn:
            current = self.find_by_id(patient_id)
            sets = ", ".join(f"{col} = ?" for col in changes)  # columns whitelisted above
            cur = conn.execute(
                f"UPDATE patients SET {sets}, version = version + 1 "
                f"WHERE patient_id = ? AND version = ?",
                (*changes.values(), patient_id, expected_version))
            if cur.rowcount == 0:
                return False
            changed_at = datetime.now().isoformat(timespec="seconds")
            conn.executemany(
                "INSERT INTO patient_history (patient_id, field, old_value, new_value, "
                "changed_by, changed_at) VALUES (?,?,?,?,?,?)",
                [(patient_id, field, getattr(current, field), new, changed_by, changed_at)
                 for field, new in changes.items()])
        return True

    def get_history(self, patient_id):
        return self._db.conn.execute(
            "SELECT * FROM patient_history WHERE patient_id = ? ORDER BY history_id",
            (patient_id,)).fetchall()
