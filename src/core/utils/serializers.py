from datetime import datetime, timezone
from typing import Any

import orjson
from asyncpg.pgproto import pgproto


def serialize_object(obj: Any) -> str:
    """Encodes a python object to a json string."""

    def _serialize(val: Any) -> Any:
        if isinstance(val, pgproto.UUID):
            return str(val)

    return orjson.dumps(
        obj,
        default=_serialize,
        option=orjson.OPT_NAIVE_UTC | orjson.OPT_SERIALIZE_NUMPY,
    ).decode()


def deserialize_object(
    obj: bytes | bytearray | memoryview | str | dict[str, Any]
) -> Any:
    """Decodes an object to a python datatype."""
    if isinstance(obj, dict):
        return obj

    return orjson.loads(obj)


def add_timezone_to_datetime(dt: datetime) -> str:
    """Handles datetime serialization for nested timestamps."""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.isoformat().replace("+00:00", "Z")
