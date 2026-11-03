"""Authentication and role-based authorization for clinic staff."""
import hashlib
import hmac
import os

PERMISSIONS = {
    "staff": {"register_patient", "view_patient", "update_patient",
              "add_note", "view_history", "categorize_note"},
    "it_admin": {"view_patient", "view_history", "view_audit"},
}


class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class StaffUser:
    def __init__(self, username, role):
        self.username = username
        self.role = role

    def can(self, permission):
        return permission in PERMISSIONS.get(self.role, set())


class AuthService:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _hash(password, salt):
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()

    def create_user(self, username, password, role):
        if role not in PERMISSIONS:
            raise ValueError("Unknown role")
        salt = os.urandom(16)
        self.db.conn.execute(
            "INSERT INTO staff (username, password_hash, salt, role) VALUES (?,?,?,?)",
            (username, self._hash(password, salt), salt.hex(), role))
        self.db.conn.commit()

    def login(self, username, password):
        row = self.db.conn.execute(
            "SELECT * FROM staff WHERE username = ?", (username,)).fetchone()
        if row is None:
            raise AuthenticationError("Invalid username or password")
        candidate = self._hash(password, bytes.fromhex(row["salt"]))
        if not hmac.compare_digest(candidate, row["password_hash"]):
            raise AuthenticationError("Invalid username or password")
        return StaffUser(row["username"], row["role"])

    def seed_demo_users(self):
        """Synthetic demo accounts only."""
        count = self.db.conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
        if count == 0:
            self.create_user("nurse1", "staffpass", "staff")
            self.create_user("itadmin", "adminpass", "it_admin")


def require(user, permission):
    if user is None or not user.can(permission):
        raise AuthorizationError(f"Not permitted: {permission}")
