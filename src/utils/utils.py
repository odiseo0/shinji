import unicodedata
import itertools
import functools
from typing import Sequence, Any, Callable, TypeVar, Coroutine, Awaitable, ParamSpec
from uuid import UUID

import anyio
from anyio._core._eventloop import threadlocals


T = TypeVar("T")
T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")


def strip_accents(s: str) -> str:
    """
    Remove accents from string \n
    `Reference:` https://stackoverflow.com/a/518232/15441507
    """
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def common_entries(*dcts: list[dict[str, Any]]):
    """Returns a tuple with common entries."""
    if not dcts:
        return

    for i in set(dcts[0]).intersection(*dcts[1:]):
        yield (i,) + tuple(d[i] for d in dcts)


def chunks(iterable: Sequence, n: int, fill_value=None):
    """Allow iteration by chunks."""
    return itertools.zip_longest(*[iter(iterable)] * n, fillvalue=fill_value)


def is_valid_uuid(uuid_to_check: Any) -> UUID | None:
    """
    Check if uuid_to_test is a valid UUID.
    """
    try:
        uuid_obj = UUID(uuid_to_check, version=4)
    except (ValueError, AttributeError):
        return False

    return uuid_obj


def syncify(
    func: Callable[T_ParamSpec, Coroutine[Any, Any, T_Retval]],
    raise_sync_error: bool = True,
) -> Callable[T_ParamSpec, T_Retval]:
    """
    Take an async function and return a sync function that takes the same parameters as the original.
    """

    @functools.wraps(func)
    def wrapper(*args: T_ParamSpec.args, **kwargs: T_ParamSpec.kwargs) -> T_Retval:
        current_async_module = getattr(threadlocals, "current_async_module", None)
        partial_f = functools.partial(func, *args, **kwargs)  # bind parameters here.

        if current_async_module is None and raise_sync_error is False:
            return anyio.run(partial_f)

        return anyio.from_thread.run(partial_f)

    return wrapper


def asyncify(
    func: Callable[T_ParamSpec, T_Retval],
    *,
    cancellable: bool = False,
    limiter: anyio.CapacityLimiter | None = None
) -> Callable[T_ParamSpec, Awaitable[T_Retval]]:
    """
    Take a sync function and return an async function that takes the same parameters as the original
    """

    async def wrapper(
        *args: T_ParamSpec.args, **kwargs: T_ParamSpec.kwargs
    ) -> T_Retval:
        # bind parameters here.
        partial_f = functools.partial(func, *args, **kwargs)
        return await anyio.to_thread.run_sync(
            partial_f, cancellable=cancellable, limiter=limiter
        )

    return wrapper
