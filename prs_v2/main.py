"""PRS entry point (composition root: wires the components together)."""
from prs.persistence.database import Database
from prs.authentication.auth import AuthService
from prs.authentication.repository import StaffRepository
from prs.patient.repository import PatientRepository
from prs.patient.service import PatientService
from prs.visit.repository import VisitRepository
from prs.visit.service import VisitService
from prs.ai_integration.categorizer import CategorizationService
from prs.ui.cli import CLI


def main():
    db = Database("prs_v2.db")
    try:
        auth = AuthService(StaffRepository(db))
        auth.seed_demo_users()
        patients = PatientService(PatientRepository(db))
        visits = VisitService(VisitRepository(db), patients, CategorizationService())
        CLI(auth, patients, visits).run()
    finally:
        db.close()


if __name__ == "__main__":
    main()
