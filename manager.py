import argparse
import app_helper


def main():
    """Main argparser function."""
    parser = argparse.ArgumentParser(description='Manage your database.')
    subparsers = parser.add_subparsers(dest='command')

    new_parser = subparsers.add_parser('new', help='Create a new database.')
    new_parser.add_argument('--force', action='store_true', help='Forcefully overwrite the database.')

    subparsers.add_parser('load', help='Load a database.')
    subparsers.add_parser('clear', help='Clear a database.')
    subparsers.add_parser('close', help='Close a database.')

    quick_setup_parser = subparsers.add_parser('quick_setup', help='Quick setup')
    quick_setup_parser.add_argument('-s', '--secret', type=str, help='Client secret.', required=True)
    quick_setup_parser.add_argument('-id', '--id', type=str, help='Client ID.', required=True)
    quick_setup_parser.add_argument('-set', '--emails', type=str, help='List of emails', required=True)

    envedit_parser = subparsers.add_parser('envedit', help='Edit environment variables.')
    envedit_parser.add_argument('-s', '--secret', type=str, help='Client secret.')
    envedit_parser.add_argument('-id', '--id', type=str, help='Client ID.')
    group = envedit_parser.add_mutually_exclusive_group()
    group.add_argument('-add', '--add_email', type=str, help='Email address to add.')
    group.add_argument('-rm', '--remove_email', type=str, help='Email address to remove.')
    group.add_argument('-set', '--emails', type=str, help='List of emails')

    args = parser.parse_args()

    if args.command == 'new':
        app_helper.create_table(args.force)
    elif args.command == 'load':
        app_helper.load_data()
    elif args.command == 'clear':
        app_helper.clear_table()
    elif args.command == 'close':
        app_helper.close_conn()
    elif args.command == 'quick_setup':
        # Initialise and load the database
        app_helper.create_table(force=True)
        app_helper.load_data()
        envdata = {}
        emailenvdata = {}
        envdata['GOOGLE_CLIENT_SECRET'] = args.secret
        envdata['GOOGLE_CLIENT_ID'] = args.id
        emailenvdata['SET'] = args.emails
        app_helper.envedit(envdata, emailenvdata)
    elif args.command == 'envedit':
        envdata = {}
        emailenvdata = {}
        if args.secret:
            envdata['GOOGLE_CLIENT_SECRET'] = args.secret
        if args.id:
            envdata['GOOGLE_CLIENT_ID'] = args.id
        if args.add_email:
            emailenvdata['ADD'] = args.add_email
        if args.remove_email:
            emailenvdata['REMOVE'] = args.remove_email
        if args.emails:
            emailenvdata['SET'] = args.emails
        app_helper.envedit(envdata, emailenvdata)
    else:
        parser.print_help()
    print('Done!')


if __name__ == '__main__':
    main()
