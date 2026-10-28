"""Request checks that would normally live in the web server config.

Neither uvicorn nor gunicorn limits the size of a request body, so the app does it.
"""

from typing import TYPE_CHECKING

from starlette.responses import PlainTextResponse

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send


class RequestGuardMiddleware:
    """Rejects request bodies the app never needs.

    - Bodies over `max_body_size` get 413, so form parsing can't be fed huge inputs.
    - Bodies sent without Content-Length (chunked) get 411, so the size check can't be bypassed.
    - multipart/form-data gets 415: every form here is urlencoded, so the multipart parser is never needed.
    """

    def __init__(self, app: ASGIApp, max_body_size: int) -> None:
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        error = self._check(dict(scope["headers"]))
        if error is not None:
            status, message = error
            await PlainTextResponse(message, status_code=status)(scope, receive, send)
            return
        await self.app(scope, receive, send)

    def _check(self, headers: dict[bytes, bytes]) -> tuple[int, str] | None:
        if b"transfer-encoding" in headers:
            return 411, "Length Required"
        content_length = headers.get(b"content-length", b"0")
        if not content_length.isdigit():
            return 400, "Bad Request"
        if int(content_length) > self.max_body_size:
            return 413, "Request Entity Too Large"
        if headers.get(b"content-type", b"").lower().startswith(b"multipart/"):
            return 415, "Unsupported Media Type"
        return None
