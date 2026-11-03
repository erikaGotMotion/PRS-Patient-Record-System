"""Patient domain model."""
import re
from datetime import date, datetime

PATIENT_ID_PATTERN = re.compile(r"\d{5}")
DATE_FORMAT = "%Y-%m-%d"


class Patient:
    """A patient record.

    The Patient ID is write-once: it is set in ``__init__`` and every later
    attempt to rebind or delete it raises ``AttributeError`` (UR-02). The
    database enforces the same rule with a trigger (see persistence.database).
    """

    EDITABLE_FIELDS = ("name", "date_of_birth", "phone")

    def __init__(self, patient_id, name, date_of_birth=None, phone=None, version=1):
        if not PATIENT_ID_PATTERN.fullmatch(str(patient_id)):
            raise ValueError("Patient ID must be exactly 5 digits")
        self._patient_id = patient_id
        self.name = name
        self.date_of_birth = date_of_birth
        self.phone = phone
        self.version = version

    # -- write-once Patient ID -------------------------------------------
    def __setattr__(self, key, value):
        if key == "_patient_id" and "_patient_id" in self.__dict__:
            raise AttributeError("Patient ID is immutable")
        super().__setattr__(key, value)

    def __delattr__(self, key):
        if key == "_patient_id":
            raise AttributeError("Patient ID is immutable")
        super().__delattr__(key)

    @property
    def patient_id(self):
        return self._patient_id

    # -- validated fields ------------------------------------------------
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = self.validate_name(value)

    @property
    def date_of_birth(self):
        return self._date_of_birth

    @date_of_birth.setter
    def date_of_birth(self, value):
        self._date_of_birth = self.validate_date_of_birth(value)

    # -- validation rules (single source of truth) -----------------------
    @staticmethod
    def validate_name(value):
        if not value or not value.strip():
            raise ValueError("Patient name is required")
        return value.strip()

    @staticmethod
    def validate_date_of_birth(value):
        """Accept None or a real, non-future YYYY-MM-DD date."""
        if value is None:
            return None
        try:
            parsed = datetime.strptime(value, DATE_FORMAT).date()
        except ValueError:
            raise ValueError("Date of birth must be a valid date in YYYY-MM-DD format")
        if parsed > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value

    @classmethod
    def validate_changes(cls, changes):
        """Return the permitted, validated subset of ``changes``.

        Unknown fields (including ``patient_id``) and ``None`` values are dropped.
        """
        allowed = {k: v for k, v in changes.items()
                   if k in cls.EDITABLE_FIELDS and v is not None}
        if "name" in allowed:
            allowed["name"] = cls.validate_name(allowed["name"])
        if "date_of_birth" in allowed:
            allowed["date_of_birth"] = cls.validate_date_of_birth(allowed["date_of_birth"])
        return allowed

    def __str__(self):
        return (f"[{self.patient_id}] {self.name} | DOB: {self.date_of_birth or '-'} "
                f"| Phone: {self.phone or '-'}")
