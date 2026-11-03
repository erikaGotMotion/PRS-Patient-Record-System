"""Command-line user interface."""
from getpass import getpass
from prs.authentication.auth import AuthenticationError, AuthorizationError
from prs.patient.service import PatientNotFoundError, ConcurrentEditError
from prs.ai_integration.categorizer import CATEGORIES


class CLI:
    def __init__(self, auth, patients, visits):
        self.auth, self.patients, self.visits = auth, patients, visits
        self.user = None

    def run(self):
        print("=== Patient Record System (synthetic data only) ===")
        while self.user is None:
            u = input("Username: ")
            p = getpass("Password: ") if False else input("Password: ")
            try:
                self.user = self.auth.login(u, p)
            except AuthenticationError as e:
                print(e)
        print(f"Logged in as {self.user.username} ({self.user.role})")
        actions = {"1": self.register, "2": self.lookup, "3": self.update,
                   "4": self.add_note, "5": self.history, "6": self.audit}
        while True:
            print("\n1) Register patient  2) Find patient  3) Update patient\n"
                  "4) Add visit note  5) Visit history  6) Change history  0) Quit")
            choice = input("> ").strip()
            if choice == "0":
                break
            action = actions.get(choice)
            if not action:
                print("Invalid choice")
                continue
            try:
                action()
            except (ValueError, PatientNotFoundError, ConcurrentEditError,
                    AuthorizationError) as e:
                print(f"! {e}")

    def register(self):
        name = input("Name: ")
        dob = input("Date of birth (YYYY-MM-DD, optional): ") or None
        phone = input("Phone (optional): ") or None
        p = self.patients.register_patient(self.user, name, dob, phone)
        print(f"Registered. Patient ID: {p.patient_id}")

    def lookup(self):
        print(self.patients.get_patient(self.user, input("Patient ID: ").strip()))

    def update(self):
        pid = input("Patient ID: ").strip()
        p = self.patients.get_patient(self.user, pid)
        print(p)
        print("Leave blank to keep a value. Patient ID cannot be changed.")
        name = input("New name: ") or None
        dob = input("New DOB: ") or None
        phone = input("New phone: ") or None
        updated = self.patients.update_patient(self.user, pid, p.version,
                                               name=name, date_of_birth=dob, phone=phone)
        print("Saved:", updated)

    def add_note(self):
        pid = input("Patient ID: ").strip()
        d = input("Visit date (YYYY-MM-DD, blank = today): ") or None
        text = input("Note: ")
        note, s = self.visits.add_note(self.user, pid, text, d)
        print(f"Note #{note.note_id} saved (uncategorized).")
        if s.usable:
            print(f"AI suggestion (not a diagnosis): {s.category} "
                  f"[confidence {s.confidence:.0%}, source: {s.source}]")
            ans = input("Accept (a), reject (r), or choose manually (m)? ").strip().lower()
            if ans == "a":
                self.visits.accept_suggestion(self.user, note.note_id, s.category)
                print("Category saved.")
            elif ans == "m":
                self._manual(note.note_id)
            else:
                print("Suggestion rejected; note left uncategorized.")
        else:
            print(s.message or "No suggestion available.")
            if input("Categorize manually? (y/n) ").lower() == "y":
                self._manual(note.note_id)

    def _manual(self, note_id):
        for i, c in enumerate(CATEGORIES, 1):
            print(f"  {i}) {c}")
        idx = int(input("Choice: ")) - 1
        self.visits.accept_suggestion(self.user, note_id, CATEGORIES[idx])
        print("Category saved.")

    def history(self):
        notes = self.visits.get_visit_history(self.user, input("Patient ID: ").strip())
        for n in notes or []:
            print(n)
        if not notes:
            print("No visit notes.")

    def audit(self):
        for h in self.patients.get_change_history(self.user, input("Patient ID: ").strip()):
            print(f"{h['changed_at']} {h['changed_by']}: {h['field']} "
                  f"'{h['old_value']}' -> '{h['new_value']}'")
