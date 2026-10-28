"""Request checks that would normally live in the web server config.

Starlette and python-multipart can't be upgraded on Python 3.8, so their known DoS issues are blocked here instead.
"""

from typing import Dict, Optional, Tuple

from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestGuardMiddleware:
    """Rejects request bodies the app never needs and removes the Range header.

    - Bodies over `max_body_size` get 413, so slow form parsing can't be fed huge inputs
      (starlette PYSEC-2026-249, python-multipart PYSEC-2026-3036).
    - Bodies sent without Content-Length (chunked) get 411, so the size check can't be bypassed.
    - multipart/form-data gets 415: every form here is urlencoded, and the multipart parser has DoS bugs
      (python-multipart PYSEC-2026-3038 / 3039, starlette PYSEC-2026-1941).
    - The Range header is dropped: Starlette's Range parsing for static files can be made very slow
      (starlette PYSEC-2026-1942). Files are then always sent whole, which is fine for small static files.
    """

    def __init__(self, app: ASGIApp, max_body_size: int) -> None:
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = [(name, value) for name, value in scope["headers"] if name != b"range"]
        scope = dict(scope, headers=headers)
        error = self._check(dict(headers))
        if error is not None:
            status, message = error
            await PlainTextResponse(message, status_code=status)(scope, receive, send)
            return
        await self.app(scope, receive, send)

    def _check(self, headers: Dict[bytes, bytes]) -> Optional[Tuple[int, str]]:
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
