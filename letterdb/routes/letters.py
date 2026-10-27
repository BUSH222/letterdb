"""Viewing a letter, and the staff pages for creating, editing and deleting letters."""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from letterdb import letters
from letterdb.web import CurrentUser, SessionDep, redirect, require_user, templates

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from letterdb.models import Letter

router = APIRouter()
staff = [Depends(require_user)]


class LetterForm(BaseModel):
    """The fields of the new letter / edit letter forms."""

    catalogue: str = ""
    date: str = ""
    addressee: str = ""
    keywords: str = ""
    regions: str = ""
    contents_txt: str = ""
    imagelink: str = ""
    comments: str = ""
    notes: str = ""


LetterFormDep = Annotated[LetterForm, Form()]


def _get_or_404(session: Session, catalogue: str) -> Letter:
    """The letter for a catalogue number from the URL; old zero-padded links such as /viewitem/007 still work."""
    if not catalogue.isdigit():
        raise HTTPException(status_code=400)
    letter = letters.get(session, int(catalogue))
    if letter is None:
        raise HTTPException(status_code=404)
    return letter


@router.get("/viewitem/{catalogue}", response_class=HTMLResponse)
def viewitem(request: Request, catalogue: str, session: SessionDep, user: CurrentUser):
    letter = _get_or_404(session, catalogue)
    return templates.TemplateResponse(
        request, "letterview.html", {"data": letters.as_dict(letter), "authenticated": user is not None}
    )


@router.get("/newletter", response_class=HTMLResponse, dependencies=staff)
def newletter(request: Request):
    return templates.TemplateResponse(request, "newletter.html", {"data": {}, "error": None})


@router.post("/finalise_new_letter", dependencies=staff)
def finalise_new_letter(request: Request, session: SessionDep, letter_form: LetterFormDep):
    form = letter_form.model_dump()
    try:
        letter = letters.create(session, form)
    except letters.InvalidLetter as e:
        context = {"data": form, "error": str(e)}
        return templates.TemplateResponse(request, "newletter.html", context, status_code=400)
    return redirect(f"/viewitem/{letter.catalogue}")


@router.get("/edit/{catalogue}", response_class=HTMLResponse, dependencies=staff)
def edititem(request: Request, catalogue: str, session: SessionDep):
    letter = _get_or_404(session, catalogue)
    context = {"data": letters.as_dict(letter), "original_catalogue": letter.catalogue, "error": None}
    return templates.TemplateResponse(request, "letteredit.html", context)


@router.post("/finalise_edit/{catalogue}", dependencies=staff)
def finalise_edit(request: Request, catalogue: str, session: SessionDep, letter_form: LetterFormDep):
    original = _get_or_404(session, catalogue).catalogue
    form = letter_form.model_dump()
    try:
        letter = letters.update(session, original, form)
    except letters.InvalidLetter as e:
        context = {"data": form, "original_catalogue": original, "error": str(e)}
        return templates.TemplateResponse(request, "letteredit.html", context, status_code=400)
    assert letter is not None  # checked by _get_or_404
    return redirect(f"/viewitem/{letter.catalogue}")


@router.post("/delete/{catalogue}", dependencies=staff)
def delete_letter(catalogue: str, session: SessionDep):
    letters.delete(session, _get_or_404(session, catalogue).catalogue)
    return redirect("/search")
