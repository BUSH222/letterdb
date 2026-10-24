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

## Users
Users log in at `/login` with an email and password (stored hashed in `maindb.db`). Manage them with:
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
