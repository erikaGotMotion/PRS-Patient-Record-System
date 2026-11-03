"""Patient domain model."""


class Patient:
    EDITABLE_FIELDS = ("name", "date_of_birth", "phone")

    def __init__(self, patient_id, name, date_of_birth=None, phone=None, version=1):
        if not name or not name.strip():
            raise ValueError("Patient name is required")
        self._patient_id = patient_id
        self._name = name.strip()
        self.date_of_birth = date_of_birth
        self.phone = phone
        self.version = version

    @property
    def patient_id(self):
        return self._patient_id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not value or not value.strip():
            raise ValueError("Patient name is required")
        self._name = value.strip()

    def __str__(self):
        return (f"[{self.patient_id}] {self.name} | DOB: {self.date_of_birth or '-'} "
                f"| Phone: {self.phone or '-'}")
