"""Shared pieces of the web layer: templates and request dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from letterdb import users
from letterdb.db import get_session
from letterdb.models import User
from letterdb.text import split_terms

templates = Jinja2Templates(directory="templates")
templates.env.filters["terms"] = split_terms
templates.env.finalize = lambda value: "" if value is None else value  # NULL columns render as empty

SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(request: Request, session: SessionDep) -> User | None:
    """The logged in user, if any. Their id is kept in a signed session cookie."""
    user_id = request.session.get("user_id")
    return users.get(session, user_id) if user_id is not None else None


CurrentUser = Annotated[User | None, Depends(get_current_user)]


def require_user(user: CurrentUser) -> User:
    """Dependency which rejects requests from anonymous visitors."""
    if user is None:
        raise HTTPException(status_code=403)
    return user


def redirect(url: str) -> RedirectResponse:
    """Redirect after an action; 303 makes the browser follow with a GET."""
    return RedirectResponse(url, status_code=303)
