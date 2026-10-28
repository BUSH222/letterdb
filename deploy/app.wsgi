# MOVE THIS FILE TO ~/hostname.nichost.ru/docs

import os, sys, site

# Change 
PROJECT_DIR = os.path.expanduser("~h617995037/letterdb")

# Use the project's uv venv and make the project importable
site.addsitedir(os.path.join(PROJECT_DIR, ".venv/lib/python3.8/site-packages"))
sys.path.insert(0, PROJECT_DIR)

# Relative paths (maindb.db, templates/, static/, .env) resolve from here
os.chdir(PROJECT_DIR)

from wsgi import application as _letterdb_app

def application(environ, start_response):
    # nginx terminates HTTPS; tell the app so generated URLs use https://
    environ["wsgi.url_scheme"] = "https"
    return _letterdb_app(environ, start_response)