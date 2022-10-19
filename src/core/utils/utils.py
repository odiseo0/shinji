import functools
import itertools
import unicodedata
from itertools import chain
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Iterable,
    Mapping,
    ParamSpec,
    Sequence,
    TypeVar,
)
from uuid import UUID

import anyio
from anyio._core._eventloop import threadlocals


T = TypeVar("T")
T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")


def strip_accents(s: str) -> str:
    """
    Remove accents from string.

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


def is_valid_uuid(uuid_to_check: Any, version: int = 4) -> UUID | bool:
    """Check if uuid_to_test is a valid UUID."""
    if isinstance(uuid_to_check, UUID):
        return uuid_to_check

    try:
        uuid_obj = UUID(uuid_to_check, version=version)
    except (ValueError, AttributeError):
        return False

    return uuid_obj


def is_hashable(obj: Any) -> bool:
    """Check if an object is hashable."""
    try:
        hash(obj)
        return True
    except TypeError:
        return False


def convert_to_camel_case(string: str) -> str:
    """Converts a string to camel case"""
    return "".join(
        word if index == 0 else word.capitalize()
        for index, word in enumerate(string.split("_"))
    )


def unique(value: Iterable[T]) -> list[T]:
    """Return all unique values in a given sequence or iterator."""
    output: list[T] = []

    for element in value:
        if element not in output:
            output.append(element)

    return output


def merge_dicts(value_1: Mapping, value_2: Mapping) -> dict:
    """Merge two dictionaries into a single one."""
    if not value_1 or not value_2:
        return {}

    if not isinstance(value_1, dict):
        try:
            value_1 = dict(value_1)
        except Exception as e:
            errors = [e]
            try:
                value_1 = vars(value_1)
            except Exception as e:
                errors.append(e)
                raise ValueError(errors)

    if not isinstance(value_2, dict):
        try:
            value_2 = dict(value_2)
        except Exception as e:
            errors = [e]
            try:
                value_2 = vars(value_2)
            except Exception as e:
                errors.append(e)
                raise ValueError(errors)

    return dict(chain(value_1.items(), value_2.items()))


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

        if current_async_module is None and not raise_sync_error:
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
