"""Catalogue lists: letters grouped by year, addressee, keyword and region."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from letterdb import letters
from letterdb.web import SessionDep, templates

router = APIRouter(prefix="/list")


@router.get("/date", response_class=HTMLResponse)
def list_date(request: Request, session: SessionDep):
    decades = letters.years_by_decade(letters.all_letters(session))
    total = sum(len(years) for _, years in decades)
    return templates.TemplateResponse(request, "list_date.html", {"decades": decades, "total": total})


@router.get("/addressee", response_class=HTMLResponse)
def list_addressee(request: Request, session: SessionDep):
    groups = letters.addressees_by_letter(letters.all_letters(session))
    total = sum(len(people) for _, people in groups)
    return templates.TemplateResponse(request, "list_addressee.html", {"groups": groups, "total": total})


@router.get("/keywords", response_class=HTMLResponse)
def list_keywords(request: Request, session: SessionDep):
    items = letters.term_counts(letters.all_letters(session), "keywords")
    return templates.TemplateResponse(request, "list_keywords.html", {"items": items, "total": len(items)})


@router.get("/region", response_class=HTMLResponse)
def list_region(request: Request, session: SessionDep):
    items = letters.term_counts(letters.all_letters(session), "regions")
    return templates.TemplateResponse(request, "list_region.html", {"items": items, "total": len(items)})
