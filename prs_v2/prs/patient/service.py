"""Patient Management component (FR-01, FR-02, FR-07, UR-02, UR-03)."""
import random
from prs.authentication.auth import require
from .errors import (ConcurrentEditError, DuplicatePatientIdError,
                     IdSpaceExhaustedError, PatientNotFoundError)
from .models import Patient

__all__ = ["PatientService", "PatientNotFoundError", "ConcurrentEditError"]


class PatientService:
    _MAX_ID_ATTEMPTS = 1000

    def __init__(self, repository):
        self._repo = repository

    def _generate_id(self):
        """Return an unused random 5-digit ID (FR-01)."""
        for _ in range(self._MAX_ID_ATTEMPTS):
            candidate = f"{random.randint(0, 99999):05d}"
            if not self._repo.exists(candidate):
                return candidate
        raise IdSpaceExhaustedError("Could not find an unused Patient ID")

    def register_patient(self, user, name, date_of_birth=None, phone=None):
        require(user, "register_patient")
        # The database primary key is the final authority on uniqueness: if another
        # writer takes the candidate between exists() and insert(), retry.
        for _ in range(self._MAX_ID_ATTEMPTS):
            patient = Patient(self._generate_id(), name, date_of_birth, phone)
            try:
                self._repo.insert(patient)
                return patient
            except DuplicatePatientIdError:
                continue
        raise IdSpaceExhaustedError("Could not register patient: no unused ID found")

    def ensure_exists(self, patient_id):
        """Raise PatientNotFoundError unless the patient exists.

        Used by Visit Management so it depends on this component rather than on
        the patient repository (matches the Assignment #3 package diagram).
        """
        if not self._repo.exists(patient_id):
            raise PatientNotFoundError(f"No patient with ID {patient_id}")

    def get_patient(self, user, patient_id):
        require(user, "view_patient")
        patient = self._repo.find_by_id(patient_id)
        if patient is None:
            raise PatientNotFoundError(f"No patient with ID {patient_id}")
        return patient

    def update_patient(self, user, patient_id, expected_version, **changes):
        require(user, "update_patient")
        allowed = Patient.validate_changes(changes)
        self.ensure_exists(patient_id)
        if allowed and not self._repo.update_fields(
                patient_id, allowed, expected_version, user.username):
            raise ConcurrentEditError(
                "Warning: another staff member already saved changes to this record. "
                "Your changes were not applied. Reload the record and try again.")
        return self._repo.find_by_id(patient_id)

    def get_change_history(self, user, patient_id):
        require(user, "view_history")
        return self._repo.get_history(patient_id)
