"""Patient Management component (FR-01, FR-02, UR-03, FR-07)."""
import random
from prs.authentication.auth import require
from .models import Patient


class PatientNotFoundError(Exception):
    pass


class ConcurrentEditError(Exception):
    pass


class PatientService:
    def __init__(self, repository):
        self.repo = repository

    def _generate_id(self):
        while True:
            candidate = f"{random.randint(0, 99999):05d}"
            if not self.repo.exists(candidate):
                return candidate

    def register_patient(self, user, name, date_of_birth=None, phone=None):
        require(user, "register_patient")
        if not name or not name.strip():
            raise ValueError("Warning: patient name is required")
        patient = Patient(self._generate_id(), name, date_of_birth, phone)
        self.repo.insert(patient)
        return patient

    def get_patient(self, user, patient_id):
        require(user, "view_patient")
        patient = self.repo.find_by_id(patient_id)
        if patient is None:
            raise PatientNotFoundError(f"No patient with ID {patient_id}")
        return patient

    def update_patient(self, user, patient_id, expected_version, **changes):
        require(user, "update_patient")
        allowed = {k: v for k, v in changes.items()
                   if k in Patient.EDITABLE_FIELDS and v is not None}
        if "name" in allowed and not allowed["name"].strip():
            raise ValueError("Patient name cannot be blank")
        if not self.repo.exists(patient_id):
            raise PatientNotFoundError(f"No patient with ID {patient_id}")
        if not allowed:
            return self.repo.find_by_id(patient_id)
        ok = self.repo.update_fields(patient_id, allowed, expected_version, user.username)
        if not ok:
            raise ConcurrentEditError(
                "Warning: another staff member already saved changes to this record. "
                "Your changes were not applied. Reload the record and try again.")
        return self.repo.find_by_id(patient_id)

    def get_change_history(self, user, patient_id):
        require(user, "view_history")
        return self.repo.get_history(patient_id)
