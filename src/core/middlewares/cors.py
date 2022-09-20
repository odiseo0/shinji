import re
from typing import Sequence, cast

from starlette.middleware.cors import CORSMiddleware as _CORSMiddleware
from starlette.types import ASGIApp


class CORSMiddleware(_CORSMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: Sequence[str] = (),
        allow_methods: Sequence[str] = ("GET",),
        allow_headers: Sequence[str] = (),
        allow_credentials: bool = False,
        allow_origin_regex: str | None = None,
        allow_origins_regex: Sequence[str] | re.Pattern = (),
        expose_headers: Sequence[str] = (),
        max_age: int = 600,
    ) -> None:
        compiled_origins_regex = None

        if allow_origins_regex and isinstance(allow_origins_regex, (list, tuple, set)):
            compiled_origins_regex = tuple(
                re.compile(origin_regex) for origin_regex in allow_origins_regex
            )
            compiled_origins_regex = cast(tuple[re.Pattern])

        self.allow_origins_regex = cast(
            tuple[re.Pattern], compiled_origins_regex or (allow_origins_regex,)
        )

        super().__init__(
            app,
            allow_origins,
            allow_methods,
            allow_headers,
            allow_credentials,
            allow_origin_regex,
            expose_headers,
            max_age,
        )

    def is_allowed_origin(self, origin: str) -> bool:
        if self.allow_all_origins:
            return True

        if self.allow_origin_regex is not None and self.allow_origin_regex.fullmatch(
            origin
        ):
            return True

        if self.allow_origins_regex is not None and any(
            origin_regex.fullmatch(origin) for origin_regex in self.allow_origins_regex
        ):
            return True

        return origin in self.allow_origins
