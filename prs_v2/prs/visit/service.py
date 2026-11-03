"""Visit Management component (FR-03, FR-04, FR-05, FR-06)."""
from prs.authentication.auth import require
from prs.ai_integration.categorizer import CATEGORIES, Suggestion
from .models import VisitNote


class VisitNoteNotFoundError(Exception):
    """No visit note exists with the requested ID."""


class VisitService:
    """Depends on PatientService (not the patient repository) to validate patients."""

    def __init__(self, visit_repo, patient_service, categorization_service):
        self._visits = visit_repo
        self._patients = patient_service
        self._ai = categorization_service

    def add_note(self, user, patient_id, description, visit_date=None):
        """Validate, save the note FIRST, then request an AI suggestion.

        Returns ``(note, suggestion)``. The note is already persisted when the
        AI is called, so AI problems can never block saving (FR-05, AIR-02).
        """
        require(user, "add_note")
        self._patients.ensure_exists(patient_id)
        description = VisitNote.validate_description(description)
        visit_date = VisitNote.normalize_date(visit_date)
        note = self._visits.insert(patient_id, visit_date, description, user.username)
        return note, self._request_suggestion(description)

    def _request_suggestion(self, description):
        """Ask the AI for a suggestion; any failure becomes an 'unavailable' one."""
        try:
            return self._ai.suggest(description)
        except Exception as exc:  # AI must never break note saving
            return Suggestion.unavailable(str(exc))

    def accept_suggestion(self, user, note_id, category):
        """Store a staff-approved category (AIR-01). Also used for manual choices."""
        require(user, "categorize_note")
        if category not in CATEGORIES:
            raise ValueError("Invalid category")
        if not self._visits.set_category(note_id, category):
            raise VisitNoteNotFoundError(f"No visit note with ID {note_id}")

    def get_visit_history(self, user, patient_id):
        require(user, "view_history")
        self._patients.ensure_exists(patient_id)
        return self._visits.find_by_patient(patient_id)
