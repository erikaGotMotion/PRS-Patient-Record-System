"""Data access for staff accounts (keeps SQL out of AuthService)."""
import sqlite3


class StaffRepository:
    def __init__(self, db):
        self._db = db

    def insert(self, username, password_hash, salt_hex, role):
        try:
            with self._db.transaction() as conn:
                conn.execute(
                    "INSERT INTO staff (username, password_hash, salt, role) "
                    "VALUES (?,?,?,?)", (username, password_hash, salt_hex, role))
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Username '{username}' already exists") from exc

    def find_by_username(self, username):
        """Return the staff row or None."""
        return self._db.conn.execute(
            "SELECT * FROM staff WHERE username = ?", (username,)).fetchone()

    def count(self):
        return self._db.conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
