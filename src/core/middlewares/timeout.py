from __future__ import annotations

import asyncio
from typing import Protocol, TYPE_CHECKING

from starlette import status

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Scope, Receive, Send


class MiddlewareProtocol(Protocol):
    """Protocol for ASGI Middlewares"""

    def __init__(self, app: ASGIApp):
        ...

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        ...


class TimeoutMiddleware(MiddlewareProtocol):
    """Middleware for timing out a request"""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        try:
            await asyncio.wait_for(self.app(scope, receive, send), timeout=10)
        except asyncio.TimeoutError:
            return await self.send_response(
                status.HTTP_504_GATEWAY_TIMEOUT, scope, send
            )

    async def send_response(self, status_code: int, scope: Scope, send: Send):
        """Return a response if an exception is raised."""

        message_head = {
            "type": "http.response.start",
            "status": status_code,
            "headers": scope["headers"],
        }
        await send(message_head)

        message_body = {
            "type": "http.response.body",
            "body": b"No timely response could be obtained.",
        }
        await send(message_body)
