"""Visit Management component (FR-03, FR-04, FR-05, FR-06)."""
from datetime import date, datetime
from prs.authentication.auth import require
from prs.patient.service import PatientNotFoundError
from prs.ai_integration.categorizer import CATEGORIES


class VisitService:
    def __init__(self, visit_repo, patient_repo, categorization_service):
        self.visit_repo = visit_repo
        self.patient_repo = patient_repo
        self.ai = categorization_service

    def add_note(self, user, patient_id, description, visit_date=None):
        """Validate patient, save the note FIRST, then request an AI suggestion."""
        require(user, "add_note")
        if not self.patient_repo.exists(patient_id):
            raise PatientNotFoundError(f"Cannot add note: patient {patient_id} does not exist")
        description = (description or "").strip()
        if not description:
            raise ValueError("Visit note description is required")
        if len(description) > 1000:
            raise ValueError("Visit note exceeds 1,000 characters")
        visit_date = visit_date or date.today().isoformat()
        datetime.strptime(visit_date, "%Y-%m-%d")
        note = self.visit_repo.insert(patient_id, visit_date, description, user.username)
        suggestion = self.ai.suggest(description)
        return note, suggestion

    def accept_suggestion(self, user, note_id, category):
        require(user, "categorize_note")
        if category not in CATEGORIES:
            raise ValueError("Invalid category")
        self.visit_repo.set_category(note_id, category)

    def get_visit_history(self, user, patient_id):
        require(user, "view_history")
        if not self.patient_repo.exists(patient_id):
            raise PatientNotFoundError(f"No patient with ID {patient_id}")
        return self.visit_repo.find_by_patient(patient_id)
