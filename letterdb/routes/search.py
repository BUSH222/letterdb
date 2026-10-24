"""The search page: the full catalogue, a text search, and the filters the catalogue lists link to."""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from letterdb import letters
from letterdb.web import CurrentUser, SessionDep, templates

if TYPE_CHECKING:
    from letterdb.models import Letter

router = APIRouter()


def _render(request: Request, user: CurrentUser, data: list[Letter], active_filter: dict[str, str] | None = None):
    context = {"data": data, "authenticated": user is not None, "active_filter": active_filter}
    return templates.TemplateResponse(request, "search.html", context)


@router.get("/search", response_class=HTMLResponse)
def search_page(
    request: Request,
    session: SessionDep,
    user: CurrentUser,
    year: str = "",
    addressee: str = "",
    keyword: str = "",
    region: str = "",
):
    """All letters, or those matching one filter such as /search?year=1955."""
    data = letters.all_letters(session)
    for kind, value in (("year", year), ("addressee", addressee), ("keyword", keyword), ("region", region)):
        if value.strip():
            data = letters.filter_by(data, kind, value)
            return _render(request, user, data, {"label": letters.FILTER_LABELS[kind], "value": value.strip()})
    return _render(request, user, data)


@router.post("/search", response_class=HTMLResponse)
def search_submit(
    request: Request,
    session: SessionDep,
    user: CurrentUser,
    contents: Annotated[str, Form()] = "",
    addressee: Annotated[str, Form()] = "",
    comments_notes: Annotated[str, Form()] = "",
):
    data = letters.search(letters.all_letters(session), contents, addressee, comments_notes)
    return _render(request, user, data)
