"""PRS entry point."""
from prs.persistence.database import Database
from prs.authentication.auth import AuthService
from prs.patient.repository import PatientRepository
from prs.patient.service import PatientService
from prs.visit.repository import VisitRepository
from prs.visit.service import VisitService
from prs.ai_integration.categorizer import CategorizationService
from prs.ui.cli import CLI


def main():
    db = Database("prs.db")
    auth = AuthService(db)
    auth.seed_demo_users()
    patient_repo = PatientRepository(db)
    visit_repo = VisitRepository(db)
    patients = PatientService(patient_repo)
    visits = VisitService(visit_repo, patient_repo, CategorizationService())
    CLI(auth, patients, visits).run()
    db.close()


if __name__ == "__main__":
    main()
