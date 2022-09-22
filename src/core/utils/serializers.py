from collections import defaultdict
from enum import Enum
from types import GeneratorType
from typing import Any, Callable
from datetime import datetime, timezone

import orjson
from pydantic import BaseModel
from pydantic.json import ENCODERS_BY_TYPE


SetIntStr = set[int | str]
DictIntStrAny = dict[int | str, Any]


def generate_encoders_by_class_tuples(
    type_encoder_map: dict[Any, Callable[[Any], Any]]
) -> dict[Callable[[Any], Any], tuple[Any, ...]]:
    encoders_by_class_tuples = defaultdict(tuple)

    for type_, encoder in type_encoder_map.items():
        encoders_by_class_tuples[encoder] += (type_,)

    return encoders_by_class_tuples


encoders_by_class_tuples = generate_encoders_by_class_tuples(ENCODERS_BY_TYPE)


def jsonable_encoder(
    obj: Any,
    include: SetIntStr | DictIntStrAny | None = None,
    exclude: SetIntStr | DictIntStrAny | None = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
) -> dict:
    if isinstance(obj, BaseModel):
        encoder = getattr(obj.__config__, "json_encoders", {})

        obj_dict = obj.dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )

        if "__root__" in obj_dict:
            obj_dict = obj_dict["__root__"]

        return jsonable_encoder(
            obj_dict,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
            custom_encoder=encoder,
        )

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, (str, int, float, type(None))):
        return obj

    if isinstance(obj, dict):
        encoded_dict = {}
        allowed_keys = set(obj.keys())

        if include is not None:
            allowed_keys &= set(include)

        if exclude is not None:
            allowed_keys -= set(exclude)

        for key, value in obj.items():
            if (
                ((not isinstance(key, str)) or (not key.startswith("_sa")))
                and (value is not None or not exclude_none)
                and key in allowed_keys
            ):
                encoded_key = jsonable_encoder(key, by_alias=by_alias)
                encoded_value = jsonable_encoder(
                    value,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_none=exclude_none,
                )
                encoded_dict[encoded_key] = encoded_value

        return encoded_dict

    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return list(
            map(
                lambda item: jsonable_encoder(
                    item,
                    include=include,
                    exclude=exclude,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                ),
                obj,
            )
        )

    if type(obj) in ENCODERS_BY_TYPE:
        return ENCODERS_BY_TYPE[type(obj)](obj)

    for encoder, classes_tuple in encoders_by_class_tuples.items():
        if isinstance(obj, classes_tuple):
            return encoder(obj)

    try:
        data = dict(obj)
    except Exception as e:
        errors: list[Exception] = []
        errors.append(e)
        try:
            data = vars(obj)
        except Exception as e:
            errors.append(e)
            raise ValueError(errors)

    return jsonable_encoder(
        data,
        include=include,
        exclude=exclude,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
    )


def serialize_object(obj: Any) -> str:
    """Encodes a python object to a json string."""
    return orjson.dumps(
        obj,
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