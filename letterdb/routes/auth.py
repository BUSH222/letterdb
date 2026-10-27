"""Staff login. Intentionally not linked from any page."""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from letterdb import users
from letterdb.web import CurrentUser, SessionDep, redirect, templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    session: SessionDep,
    email: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
):
    user = users.authenticate(session, email, password)
    if user is None:
        return templates.TemplateResponse(
            request, "login.html", {"error": "Неверный email или пароль."}, status_code=401
        )
    request.session["user_id"] = user.id
    return redirect("/")


@router.get("/logout")
def logout(request: Request, user: CurrentUser):
    if user is None:
        raise HTTPException(status_code=401)
    request.session.clear()
    return redirect("/")
