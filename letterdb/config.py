import os

from dotenv import load_dotenv, set_key

# The project root. Paths are resolved from here, not from the working directory,
# because under Apache/mod_wsgi the working directory is not the project.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

dotenv_file = os.path.join(BASE_DIR, ".env")
if not os.path.exists(dotenv_file):
    with open(dotenv_file, "x"):
        pass
load_dotenv(dotenv_file)  # load secret keys

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "maindb.db"))
DOC_TXT_REL_DIR = "documents-txt"
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")


def secret_key() -> str:
    """The key used to sign session cookies (a random one if none is configured)."""
    return os.environ.get("SECRET_KEY") or os.urandom(24).hex()


def set_env_value(key: str, value: str) -> None:
    """Store a value in the .env file."""
    set_key(dotenv_file, key, value)
