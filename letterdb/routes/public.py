"""Static information pages."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from letterdb.web import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(request, "about.html")


@router.get("/instructions", response_class=HTMLResponse)
def instructions(request: Request):
    return templates.TemplateResponse(request, "instructions.html")


# Old pages, kept so that existing links keep working.
@router.get("/contact")
def contact():
    return RedirectResponse("/#contacts", status_code=301)


@router.get("/search_manual")
def search_manual():
    return RedirectResponse("/instructions", status_code=301)
