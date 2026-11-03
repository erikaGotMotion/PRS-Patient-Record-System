"""Command-line user interface."""
from getpass import getpass
from prs.authentication.auth import AuthenticationError, AuthorizationError
from prs.patient.errors import ConcurrentEditError, PatientNotFoundError
from prs.visit.service import VisitNoteNotFoundError
from prs.ai_integration.categorizer import CATEGORIES

HANDLED_ERRORS = (ValueError, PatientNotFoundError, VisitNoteNotFoundError,
                  ConcurrentEditError, AuthorizationError)

MENU = ("\n1) Register patient  2) Find patient  3) Update patient\n"
        "4) Add visit note  5) Visit history  6) Change history  0) Quit")


class CLI:
    def __init__(self, auth, patients, visits):
        self._auth = auth
        self._patients = patients
        self._visits = visits
        self._user = None

    def run(self):
        try:
            self._login()
            self._menu_loop()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")

    def _login(self):
        print("=== Patient Record System (synthetic data only) ===")
        while self._user is None:
            username = input("Username: ")
            password = getpass("Password: ")
            try:
                self._user = self._auth.login(username, password)
            except AuthenticationError as exc:
                print(exc)
        print(f"Logged in as {self._user.username} ({self._user.role})")

    def _menu_loop(self):
        actions = {"1": self.register, "2": self.lookup, "3": self.update,
                   "4": self.add_note, "5": self.history, "6": self.audit}
        while True:
            print(MENU)
            choice = input("> ").strip()
            if choice == "0":
                break
            action = actions.get(choice)
            if action is None:
                print("Invalid choice")
                continue
            try:
                action()
            except HANDLED_ERRORS as exc:
                print(f"! {exc}")

    def register(self):
        name = input("Name: ")
        dob = input("Date of birth (YYYY-MM-DD, optional): ") or None
        phone = input("Phone (optional): ") or None
        patient = self._patients.register_patient(self._user, name, dob, phone)
        print(f"Registered. Patient ID: {patient.patient_id}")

    def lookup(self):
        print(self._patients.get_patient(self._user, input("Patient ID: ").strip()))

    def update(self):
        pid = input("Patient ID: ").strip()
        patient = self._patients.get_patient(self._user, pid)
        print(patient)
        print("Leave blank to keep a value. Patient ID cannot be changed.")
        name = input("New name: ") or None
        dob = input("New DOB: ") or None
        phone = input("New phone: ") or None
        updated = self._patients.update_patient(
            self._user, pid, patient.version,
            name=name, date_of_birth=dob, phone=phone)
        print("Saved:", updated)

    def add_note(self):
        pid = input("Patient ID: ").strip()
        visit_date = input("Visit date (YYYY-MM-DD, blank = today): ") or None
        text = input("Note: ")
        note, suggestion = self._visits.add_note(self._user, pid, text, visit_date)
        print(f"Note #{note.note_id} saved (uncategorized).")
        if suggestion.usable:
            self._review_suggestion(note, suggestion)
        else:
            print(suggestion.message or "No suggestion available.")
            if input("Categorize manually? (y/n) ").strip().lower() == "y":
                self._choose_category(note.note_id)

    def _review_suggestion(self, note, suggestion):
        print(f"AI suggestion (not a diagnosis): {suggestion.category} "
              f"[confidence {suggestion.confidence:.0%}, source: {suggestion.source}]")
        answer = input("Accept (a), reject (r), or choose manually (m)? ").strip().lower()
        if answer == "a":
            self._visits.accept_suggestion(self._user, note.note_id, suggestion.category)
            print("Category saved.")
        elif answer == "m":
            self._choose_category(note.note_id)
        else:
            print("Suggestion rejected; note left uncategorized.")

    def _choose_category(self, note_id):
        for i, category in enumerate(CATEGORIES, 1):
            print(f"  {i}) {category}")
        raw = input("Choice: ").strip()
        if not raw.isdigit() or not 1 <= int(raw) <= len(CATEGORIES):
            print("Invalid choice; note left uncategorized.")
            return
        self._visits.accept_suggestion(self._user, note_id, CATEGORIES[int(raw) - 1])
        print("Category saved.")

    def history(self):
        notes = self._visits.get_visit_history(self._user, input("Patient ID: ").strip())
        if not notes:
            print("No visit notes.")
        for note in notes:
            print(note)

    def audit(self):
        pid = input("Patient ID: ").strip()
        for h in self._patients.get_change_history(self._user, pid):
            print(f"{h['changed_at']} {h['changed_by']}: {h['field']} "
                  f"'{h['old_value']}' -> '{h['new_value']}'")
