from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send


class MiddlewareProtocol(Protocol):
    """Protocol for ASGI Middlewares"""

    def __init__(self, app: "ASGIApp"):
        ...

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send"):
        ...
