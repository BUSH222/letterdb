import os
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app_helper import (
    CHECKBOX_INPUT_FIELDS,
    TEXT_INPUT_FIELDS,
    add_row,
    delete_row,
    filter_data,
    unload_data,
    update_row,
)

# Internal imports
from user import User

app = FastAPI()

# Load data at start
DATADICT = unload_data()

# Login management: the id of the logged in user is kept in a signed session cookie
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY") or os.urandom(24).hex())
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request) -> User | None:
    """Return the logged in user, if any."""
    user_id = request.session.get("user_id")
    return User.get(user_id) if user_id is not None else None


CurrentUser = Annotated[User | None, Depends(get_current_user)]


def require_user(user: CurrentUser) -> User:
    """Dependency which rejects requests from anonymous visitors."""
    if user is None:
        raise HTTPException(status_code=403)
    return user


def redirect(url: str) -> RedirectResponse:
    """Redirect after an action; 303 makes the browser follow with a GET."""
    return RedirectResponse(url, status_code=303)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Index of the webpage."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page."""
    return templates.TemplateResponse(request, "about.html")


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """Contact page."""
    return templates.TemplateResponse(request, "contact.html")


@app.get("/search_manual", response_class=HTMLResponse)
async def search_manual(request: Request):
    """Contact page."""
    return templates.TemplateResponse(request, "search_manual.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """The login form."""
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Log in with an email and a password."""
    form = await request.form()
    user = User.authenticate(str(form.get("email", "")), str(form.get("password", "")))
    if user is None:
        return templates.TemplateResponse(
            request, "login.html", {"error": "Неверный email или пароль."}, status_code=401
        )
    request.session["user_id"] = user.id
    return redirect("/")


@app.get("/logout")
async def logout(request: Request, user: CurrentUser):
    """Log out"""
    if user is None:
        raise HTTPException(status_code=401)
    request.session.clear()
    return redirect("/")


@app.get("/viewitem/{itemindex}", response_class=HTMLResponse)
async def viewitem(request: Request, itemindex: str, user: CurrentUser):
    """The page of a specific letter."""
    if not itemindex.isdigit():
        raise HTTPException(status_code=400)
    current_letter_data = {}

    for elem in DATADICT:
        if elem["catalogue"] == itemindex:
            current_letter_data = elem
            break

    hidden = "" if user else "hidden"
    print(current_letter_data)
    return templates.TemplateResponse(request, "letterview.html", {"data": current_letter_data, "hidden": hidden})


@app.get("/newletter", response_class=HTMLResponse, dependencies=[Depends(require_user)])
async def newletter(request: Request):
    """The page for creating a new letter"""
    return templates.TemplateResponse(request, "newletter.html")


@app.post("/finalise_new_letter", dependencies=[Depends(require_user)])
async def finalise_new_letter(request: Request):
    """Finalise the process of creating a new letter."""
    formdata = dict(await request.form())

    DATADICT.append(formdata)
    add_row(formdata.values())

    return redirect(f"/viewitem/{formdata['catalogue']}")


@app.get("/edit/{itemindex}", response_class=HTMLResponse, dependencies=[Depends(require_user)])
async def edititem(request: Request, itemindex: str):
    """Edit page of a specific letter."""
    if not itemindex.isdigit():
        raise HTTPException(status_code=400)
    current_letter_data = {}

    for elem in DATADICT:
        if elem["catalogue"] == itemindex:
            current_letter_data = elem
            break

    return templates.TemplateResponse(request, "letteredit.html", {"data": current_letter_data})


@app.post("/finalise_edit/{itemindex}", dependencies=[Depends(require_user)])
async def finalise_edit(request: Request, itemindex: str):
    """Finalise the editing process, save results."""
    if not itemindex.isdigit():
        raise HTTPException(status_code=400)
    formdata = dict(await request.form())
    for cnt, elem in enumerate(DATADICT):
        if elem["catalogue"] == itemindex and formdata.keys() == elem.keys():
            DATADICT[cnt] = formdata
            break
    update_row(formdata, itemindex)
    return redirect(f"/viewitem/{itemindex}")


@app.get("/delete/{itemindex}", dependencies=[Depends(require_user)])
async def delete_letter(itemindex: str):
    if not itemindex.isdigit():
        raise HTTPException(status_code=400)
    todel = None
    for elem in DATADICT:
        if elem["catalogue"] == itemindex:
            todel = elem
            break
    DATADICT.remove(todel)
    delete_row(itemindex)
    return redirect("/search")


@app.get("/search", response_class=HTMLResponse)
@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, user: CurrentUser):
    """Return the search values."""
    context = {"data": DATADICT, "notfoundhidden": "hidden", "authenticated": user is not None}
    if request.method == "POST":
        query = dict(await request.form())
        textfields = {}
        checkbox_items_on = []
        for key, value in query.items():
            if key in TEXT_INPUT_FIELDS:
                textfields[key] = value
            elif key in CHECKBOX_INPUT_FIELDS and value == "on":
                checkbox_items_on.append(key)
        context["data"] = filter_data(DATADICT, textfields, sorting_params=checkbox_items_on)
        if len(context["data"]) == 0:
            context["notfoundhidden"] = ""
    return templates.TemplateResponse(request, "search.html", context)


if __name__ == "__main__":
    uvicorn.run(app)
