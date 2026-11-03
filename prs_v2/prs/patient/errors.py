"""Patient-domain exceptions."""


class PatientNotFoundError(Exception):
    """No patient exists with the requested ID."""


class ConcurrentEditError(Exception):
    """Another staff member saved the record first (FR-07)."""


class DuplicatePatientIdError(Exception):
    """The Patient ID is already in use."""


class IdSpaceExhaustedError(Exception):
    """No unused 5-digit Patient ID could be generated."""
