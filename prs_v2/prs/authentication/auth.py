"""Authentication and role-based authorization for clinic staff."""
import hashlib
import hmac
import os

PERMISSIONS = {
    "staff": frozenset({"register_patient", "view_patient", "update_patient",
                        "add_note", "view_history", "categorize_note"}),
    "it_admin": frozenset({"view_patient", "view_history", "view_audit"}),
}


class AuthenticationError(Exception):
    """Raised when credentials are invalid."""


class AuthorizationError(Exception):
    """Raised when a user lacks permission for an operation."""


class StaffUser:
    """An authenticated user. Never carries password data."""

    def __init__(self, username, role):
        self.username = username
        self.role = role

    def can(self, permission):
        return permission in PERMISSIONS.get(self.role, frozenset())


def require(user, permission):
    """Raise AuthorizationError unless ``user`` holds ``permission``."""
    if user is None or not user.can(permission):
        raise AuthorizationError(f"Not permitted: {permission}")


class AuthService:
    _ITERATIONS = 100_000

    def __init__(self, staff_repository):
        self._repo = staff_repository

    @classmethod
    def _hash(cls, password, salt):
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt,
                                   cls._ITERATIONS).hex()

    def create_user(self, username, password, role):
        if role not in PERMISSIONS:
            raise ValueError("Unknown role")
        if not username or not password:
            raise ValueError("Username and password are required")
        salt = os.urandom(16)
        self._repo.insert(username, self._hash(password, salt), salt.hex(), role)

    def login(self, username, password):
        row = self._repo.find_by_username(username)
        if row is None:
            raise AuthenticationError("Invalid username or password")
        candidate = self._hash(password, bytes.fromhex(row["salt"]))
        if not hmac.compare_digest(candidate, row["password_hash"]):
            raise AuthenticationError("Invalid username or password")
        return StaffUser(row["username"], row["role"])

    def seed_demo_users(self):
        """Create synthetic demo accounts on an empty staff table."""
        if self._repo.count() == 0:
            self.create_user("nurse1", "staffpass", "staff")
            self.create_user("itadmin", "adminpass", "it_admin")
