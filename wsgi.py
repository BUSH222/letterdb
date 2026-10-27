"""WSGI entry point, for Apache/mod_wsgi. Point the .wsgi file at `application`.

a2wsgi does not run the ASGI lifespan, so the startup work in app.lifespan is done here instead.
"""

from a2wsgi import ASGIMiddleware

from app import app as asgi_app
from letterdb.db import create_tables

create_tables()  # creates any missing table (e.g. users); existing data is untouched

_wsgi_app = ASGIMiddleware(asgi_app)  # ty: ignore[invalid-argument-type]  # a2wsgi types are stricter than Starlette's


def application(environ, start_response):
    # Hide the .wsgi script name from the app so URLs stay clean (/, /search, ...)
    environ["SCRIPT_NAME"] = ""
    return _wsgi_app(environ, start_response)
