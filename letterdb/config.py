import os

from dotenv import find_dotenv, load_dotenv, set_key

dotenv_file = find_dotenv(usecwd=True)
if not dotenv_file:
    with open(".env", "x"):
        pass
    dotenv_file = find_dotenv(usecwd=True)
load_dotenv(dotenv_file)  # load secret keys

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///maindb.db")
DOC_TXT_REL_DIR = "documents-txt"


def secret_key() -> str:
    """The key used to sign session cookies (a random one if none is configured)."""
    return os.environ.get("SECRET_KEY") or os.urandom(24).hex()


def set_env_value(key: str, value: str) -> None:
    """Store a value in the .env file."""
    set_key(dotenv_file, key, value)
