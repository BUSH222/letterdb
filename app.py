from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from letterdb.config import MAX_REQUEST_BODY, STATIC_DIR, secret_key
from letterdb.db import create_tables
from letterdb.middleware import RequestGuardMiddleware
from letterdb.routes import auth, letters, lists, public, search


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_tables()  # creates any missing table (e.g. users); existing data is untouched
    yield


app = FastAPI(lifespan=lifespan)

# Login management: the id of the logged in user is kept in a signed session cookie
app.add_middleware(SessionMiddleware, secret_key=secret_key())
# Added last so it runs first: rejects oversized/multipart bodies (see letterdb/middleware.py)
app.add_middleware(RequestGuardMiddleware, max_body_size=MAX_REQUEST_BODY)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

for module in (public, search, lists, letters, auth):
    app.include_router(module.router)


if __name__ == "__main__":
    uvicorn.run(app)
