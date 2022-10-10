import time
from typing import TYPE_CHECKING

from starlette.datastructures import MutableHeaders

from .protocol import MiddlewareProtocol

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Scope, Receive, Send
    from starlite.types import Message


class TimingMiddleware(MiddlewareProtocol):
    """Measure time of requests"""

    def __init__(self, app: "ASGIApp"):
        self.app = app

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send"):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.time()

        async def send_wrapper(message: "Message") -> None:
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                headers = MutableHeaders(scope=message)
                headers.append(
                    "X-Process-Time",
                    f"{scope.get('path')[1:].replace('/', '.')} {str(process_time) + ' time:wall'}",
                )

            await send(message)

        await self.app(scope, receive, send_wrapper)
