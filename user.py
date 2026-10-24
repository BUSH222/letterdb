from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app_helper import con, cur

MIN_PASSWORD_LENGTH = 8

# Verified against when the email is unknown, so that response time does not reveal which emails exist.
_DUMMY_HASH = generate_password_hash("dummy-password")

cur.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)""")
con.commit()


def normalise_email(email):
    """Normalise an email address, raising ValueError if it is not valid."""
    email = email.strip().lower()
    local, _, domain = email.partition("@")
    if not local or "." not in domain or " " in email:
        raise ValueError(f"Invalid email address: {email!r}")
    return email


def validate_password(password):
    """Raise ValueError if the password is too short."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"The password must be at least {MIN_PASSWORD_LENGTH} characters long.")


class User(UserMixin):
    """A user, stored in the users table of the main database."""

    def __init__(self, id_, email, password_hash):
        self.id = id_
        self.email = email
        self.password_hash = password_hash

    @staticmethod
    def _from_row(row):
        return User(*row) if row else None

    @staticmethod
    def get(user_id):
        """Get a user by id."""
        cur.execute("SELECT id, email, password_hash FROM users WHERE id = ?", (user_id,))
        return User._from_row(cur.fetchone())

    @staticmethod
    def get_by_email(email):
        """Get a user by email."""
        cur.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (email.strip().lower(),))
        return User._from_row(cur.fetchone())

    @staticmethod
    def authenticate(email, password):
        """Return the user if the credentials are correct, otherwise None."""
        user = User.get_by_email(email)
        if user is None:
            check_password_hash(_DUMMY_HASH, password)
            return None
        return user if check_password_hash(user.password_hash, password) else None

    @staticmethod
    def all():
        """Return all users."""
        cur.execute("SELECT id, email, password_hash FROM users ORDER BY id")
        return [User(*row) for row in cur.fetchall()]

    @staticmethod
    def create(email, password):
        """Create a user with a hashed password."""
        email = normalise_email(email)
        validate_password(password)
        if User.get_by_email(email):
            raise ValueError(f"A user with the email {email} already exists.")
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, generate_password_hash(password)),
        )
        con.commit()

    @staticmethod
    def update(email, new_email=None, new_password=None):
        """Change the email and/or the password of a user."""
        user = User.get_by_email(email)
        if user is None:
            raise ValueError(f"No user with the email {email}.")
        if new_email is not None:
            new_email = normalise_email(new_email)
            other = User.get_by_email(new_email)
            if other and other.id != user.id:
                raise ValueError(f"A user with the email {new_email} already exists.")
            cur.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user.id))
        if new_password is not None:
            validate_password(new_password)
            cur.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_password), user.id),
            )
        con.commit()

    @staticmethod
    def delete(email):
        """Delete a user."""
        cur.execute("DELETE FROM users WHERE email = ?", (email.strip().lower(),))
        if cur.rowcount == 0:
            raise ValueError(f"No user with the email {email}.")
        con.commit()
