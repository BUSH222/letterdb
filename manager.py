import argparse
import getpass
import os
import secrets
import shutil
from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.engine import make_url

from letterdb import users
from letterdb.config import DATABASE_URL, set_env_value
from letterdb.db import SessionLocal, create_tables
from letterdb.models import Keyword, Letter, LetterKeyword, LetterRegion, Region


def prompt_password():
    """Ask for a password twice without echoing it."""
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("The passwords do not match.")
    return password


def clear_letters():
    """Delete every letter."""
    with SessionLocal() as session:
        for model in (LetterKeyword, LetterRegion, Letter, Keyword, Region):
            session.execute(delete(model))
        session.commit()


def backup(directory):
    """Copy the SQLite database file into `directory`, keeping at most ~10 backups."""
    url = make_url(DATABASE_URL)
    if url.get_backend_name() != "sqlite" or url.database is None:
        raise ValueError("backup only supports SQLite; use pg_dump / mysqldump for other databases.")
    if not os.path.isdir(directory):
        raise ValueError(f"Not a directory: {directory}")
    backups = sorted(os.listdir(directory))
    if len(backups) > 10 and os.path.isfile(os.path.join(directory, backups[0])):
        os.remove(os.path.join(directory, backups[0]))
    stamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
    shutil.copy(url.database, os.path.join(directory, f"maindb_{stamp}.db"))


def main():
    """Main argparser function."""
    parser = argparse.ArgumentParser(description="Manage your database.")
    subparsers = parser.add_subparsers(dest="command")

    new_parser = subparsers.add_parser("new", help="Create the database tables.")
    new_parser.add_argument("--force", action="store_true", help="Drop and recreate the tables.")

    clear_parser = subparsers.add_parser("clear", help="Delete every letter.")
    clear_parser.add_argument("--force", action="store_true", help="Recreate the tables, overwriting the data.")

    quick_setup_parser = subparsers.add_parser("quick_setup", help="Quick setup")
    quick_setup_parser.add_argument("-e", "--email", type=str, help="Email (prompted for if omitted).")
    quick_setup_parser.add_argument("-p", "--password", type=str, help="Password (prompted for if omitted).")

    user_add_parser = subparsers.add_parser("user_add", help="Create a user.")
    user_add_parser.add_argument("email", type=str, help="Email of the user.")
    user_add_parser.add_argument("-p", "--password", type=str, help="Password (prompted for if omitted).")

    user_edit_parser = subparsers.add_parser("user_edit", help="Edit a user.")
    user_edit_parser.add_argument("email", type=str, help="Current email of the user.")
    user_edit_parser.add_argument("-e", "--new_email", type=str, help="New email.")
    user_edit_parser.add_argument(
        "-p", "--password", nargs="?", const="", help="New password (prompted for if empty)."
    )

    user_delete_parser = subparsers.add_parser("user_delete", help="Delete a user.")
    user_delete_parser.add_argument("email", type=str, help="Email of the user.")

    subparsers.add_parser("user_list", help="List all users.")

    backup_parser = subparsers.add_parser("backup", help="Create a backup of the database (SQLite only).")
    backup_parser.add_argument("-dir", "--directory", type=str, required=True, help="Directory of the backups.")

    args = parser.parse_args()

    try:
        run(args, parser)
    except ValueError as e:
        raise SystemExit(f"Error: {e}") from e
    print("Done!")


def run(args, parser):
    """Run the chosen command."""
    if args.command not in (None, "new", "quick_setup", "backup"):
        create_tables()  # creates any missing table (e.g. users); existing data is untouched
    if args.command == "new":
        create_tables(force=args.force)
    elif args.command == "clear":
        if args.force:
            create_tables(force=True)
        else:
            clear_letters()
    elif args.command == "quick_setup":
        email = args.email or input("Email: ").strip()
        password = args.password or prompt_password()
        create_tables()
        if not os.environ.get("SECRET_KEY", ""):
            set_env_value("SECRET_KEY", secrets.token_hex(32))
        with SessionLocal() as session:
            users.create(session, email, password)
    elif args.command == "user_add":
        with SessionLocal() as session:
            users.create(session, args.email, args.password or prompt_password())
    elif args.command == "user_edit":
        if args.new_email is None and args.password is None:
            parser.error("user_edit needs --new_email and/or --password.")
        new_password = None
        if args.password is not None:
            new_password = args.password or prompt_password()
        with SessionLocal() as session:
            users.update(session, args.email, new_email=args.new_email, new_password=new_password)
    elif args.command == "user_delete":
        with SessionLocal() as session:
            users.delete(session, args.email)
    elif args.command == "user_list":
        with SessionLocal() as session:
            for user in users.all_users(session):
                print(f"{user.id}\t{user.email}")
    elif args.command == "backup":
        backup(args.directory)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
