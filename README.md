# LetterDB

> Check out the [running version of the website](https://obruchevletters.pythonanywhere.com/)

This repository contains the source code for LetterDB, a web application that allows the interactive storage of letters of Vladimir Obruchev.

## Installation
1) Clone the repository to your local machine.
2) Install [uv](https://docs.astral.sh/uv/) and run `uv sync` to create the virtual environment and install the dependencies.
3) (Development) Run `uv run pre-commit install` to enable the ruff and ty hooks.
4) Use the built in `manager` tool to quickly set everything up:
    - open terminal and cd to the directory of the project
    - run `uv run manager.py quick_setup --email=<email>` (you will be prompted for a password; `--password` is also accepted)

    This creates the letter database, a `SECRET_KEY` in `.env`, and the first user.
5) Run the application using `uv run app.py` (or `uv run uvicorn app:app --reload` for development).
This serves plain HTTP on 127.0.0.1:8000; put it behind a TLS-terminating server for release.

## Database
The app uses SQLAlchemy. The database is set by `DATABASE_URL` (in the environment or `.env`) and defaults to `sqlite:///maindb.db`.
To use another database, install its driver and point `DATABASE_URL` at it:
- PostgreSQL: `uv add "psycopg[binary]"`, then `DATABASE_URL=postgresql+psycopg://user:password@host/dbname`
- MySQL: `uv add pymysql`, then `DATABASE_URL=mysql+pymysql://user:password@host/dbname`

Missing tables are created when the app or `manager.py` starts. Other `manager.py` commands:
- `new [--force]`: create the tables (`--force` recreates the letters table; users are kept)
- `load`: load the letters from `documents-txt/`
- `clear`: delete every letter
- `backup -dir <directory>`: copy the SQLite database file (for other databases use `pg_dump` / `mysqldump`)

## Migrations
One-off schema migrations live in `migration/`. Run them from the project root, in order; each backs up a SQLite database into `maindb-backups/` first and skips itself if already applied:
- `uv run python -m migration.m01_cleanup_columns`: drops the legacy `published` and `filename` columns, moves stray filename/image-link text into comments, makes `catalogue` an integer and strips trailing dots from dates

## Pages
- `/`, `/about`, `/instructions`: information pages
- `/search`: the full catalogue. Text search covers the letter text, the addressee, and comments/notes (case-insensitive, ё = е). It also accepts one filter: `?year=`, `?addressee=`, `?keyword=` or `?region=`
- `/list/date`, `/list/addressee`, `/list/keywords`, `/list/region`: the catalogue lists; each entry links to the filtered search
- `/viewitem/<catalogue>`: a single letter
- Staff only: `/newletter`, `/edit/<catalogue>`, and delete (a POST from the letter page)

## Users
Staff log in at `/login` (deliberately not linked from any page) with an email and password (stored hashed in `maindb.db`). Manage them with:
- `uv run manager.py user_add <email> [-p <password>]`
- `uv run manager.py user_edit <email> [-e <new_email>] [-p [<new_password>]]`
- `uv run manager.py user_delete <email>`
- `uv run manager.py user_list`

If the password is omitted it is prompted for.

## Development
Linting and formatting use `ruff`, type checking uses `ty`; both run in pre-commit and in the CI workflow.
- `uv run ruff check .`
- `uv run ruff format .`
- `uv run ty check .`
