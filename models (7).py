"""Visit note domain model."""


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

    def __str__(self):
        cat = self.category or "Uncategorized"
        return f"#{self.note_id} {self.visit_date} [{cat}] {self.description}"
