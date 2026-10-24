import argparse
import getpass
import os
import secrets
import shutil
from datetime import datetime

import app_helper
from user import User


def prompt_password():
    """Ask for a password twice without echoing it."""
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("The passwords do not match.")
    return password


def main():
    """Main argparser function."""
    parser = argparse.ArgumentParser(description="Manage your database.")
    subparsers = parser.add_subparsers(dest="command")

    new_parser = subparsers.add_parser("new", help="Create a new database.")
    new_parser.add_argument("--force", action="store_true", help="Forcefully overwrite the database.")

    subparsers.add_parser("load", help="Load a database.")
    subparsers.add_parser("clear", help="Clear a database.")
    subparsers.add_parser("close", help="Close a database.")

    quick_setup_parser = subparsers.add_parser("quick_setup", help="Quick setup")
    quick_setup_parser.add_argument("-e", "--email", type=str, help="Email of the first user.", required=True)
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

    backup_parser = subparsers.add_parser("backup", help="Create a backup of the database.")
    backup_parser.add_argument("-dir", "--directory", type=str, help="Directory of the backup folder.")

    args = parser.parse_args()

    try:
        run(args, parser)
    except ValueError as e:
        raise SystemExit(f"Error: {e}") from e
    print("Done!")


def run(args, parser):
    """Run the chosen command."""

    if args.command == "new":
        app_helper.create_table(args.force)
    elif args.command == "load":
        app_helper.load_data()
    elif args.command == "clear":
        app_helper.clear_table()
    elif args.command == "close":
        app_helper.close_conn()
    elif args.command == "quick_setup":
        # Initialise and load the database
        app_helper.create_table(force=True)
        app_helper.load_data()
        if not os.environ.get("SECRET_KEY"):
            app_helper.set_env_value("SECRET_KEY", secrets.token_hex(32))
        User.create(args.email, args.password or prompt_password())
    elif args.command == "user_add":
        User.create(args.email, args.password or prompt_password())
    elif args.command == "user_edit":
        if args.new_email is None and args.password is None:
            parser.error("user_edit needs --new_email and/or --password.")
        new_password = None
        if args.password is not None:
            new_password = args.password or prompt_password()
        User.update(args.email, new_email=args.new_email, new_password=new_password)
    elif args.command == "user_delete":
        User.delete(args.email)
    elif args.command == "user_list":
        for user in User.all():
            print(f"{user.id}\t{user.email}")
    elif args.command == "backup":
        bdir = args.directory
        assert os.path.isdir(bdir)
        filename = datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")
        backupcnt = len(os.listdir(bdir))
        if backupcnt > 10:
            oldest = sorted(os.listdir(bdir))[0]
            if os.path.isfile(os.path.join(bdir, oldest)):
                os.remove(os.path.join(bdir, oldest))
        shutil.copy("maindb.db", os.path.join(bdir, f"maindb_{filename}.db "))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
