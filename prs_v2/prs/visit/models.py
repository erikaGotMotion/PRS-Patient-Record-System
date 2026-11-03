"""Visit note domain model."""
from datetime import date, datetime

DATE_FORMAT = "%Y-%m-%d"


class VisitNote:
    MAX_LENGTH = 1000

    def __init__(self, note_id, patient_id, visit_date, description,
                 category=None, created_by=None, created_at=None):
        self.note_id = note_id
        self.patient_id = patient_id
        self.visit_date = visit_date
        self.description = description
        self.category = category
        self.created_by = created_by
        self.created_at = created_at

    @classmethod
    def validate_description(cls, text):
        """Return the stripped description or raise ValueError (FR-03)."""
        text = (text or "").strip()
        if not text:
            raise ValueError("Visit note description is required")
        if len(text) > cls.MAX_LENGTH:
            raise ValueError(f"Visit note exceeds {cls.MAX_LENGTH:,} characters")
        return text

    @staticmethod
    def normalize_date(value):
        """Return a valid YYYY-MM-DD string; default to today when blank."""
        if not value:
            return date.today().isoformat()
        try:
            datetime.strptime(value, DATE_FORMAT)
        except ValueError:
            raise ValueError("Visit date must be a valid date in YYYY-MM-DD format")
        return value

    def __str__(self):
        cat = self.category or "Uncategorized"
        return f"#{self.note_id} {self.visit_date} [{cat}] {self.description}"
