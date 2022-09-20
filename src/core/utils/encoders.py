import dataclasses
from collections import defaultdict
from types import GeneratorType
from typing import Any, Callable

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


def schema_encoder(
    obj: Any,
    include: SetIntStr | DictIntStrAny | None = None,
    exclude: SetIntStr | DictIntStrAny | None = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    custom_encoder: Callable = None,
) -> dict:
    if isinstance(obj, BaseModel):
        encoder = getattr(obj.__config__, "json_encoders", {})

        if custom_encoder:
            encoder.update(custom_encoder)

        obj_dict = obj.dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            custom_encoder=encoder,
        )

        if "__root__" in obj_dict:
            obj_dict = obj_dict["__root__"]

        return jsonable_encoder(
            obj_dict,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            custom_encoder=encoder,
        )
    elif dataclasses.is_dataclass(obj):
        obj_dict = dataclasses.asdict(obj)

        return jsonable_encoder(
            obj_dict,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            custom_encoder=encoder,
        )


def dict_encoder(
    obj: dict,
    include: SetIntStr | DictIntStrAny | None = None,
    exclude: SetIntStr | DictIntStrAny | None = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    custom_encoder: Callable = None,
):
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
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                custom_encoder=custom_encoder,
            )
            encoded_dict[encoded_key] = encoded_value

    return encoded_dict


def sequence_encoder(
    obj: Any,
    include: SetIntStr | DictIntStrAny | None = None,
    exclude: SetIntStr | DictIntStrAny | None = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    custom_encoder: Callable = None,
) -> list:
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
                custom_encoder=custom_encoder,
            ),
            obj,
        )
    )


def jsonable_encoder(
    obj: Any,
    include: SetIntStr | DictIntStrAny | None = None,
    exclude: SetIntStr | DictIntStrAny | None = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    custom_encoder: Callable = None,
) -> Any:
    if isinstance(obj, (str, int, float, type(None))):
        return obj

    if isinstance(obj, dict):
        return dict_encoder(
            obj,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
            exclude_unset=exclude_unset,
            custom_encoder=custom_encoder,
        )

    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return sequence_encoder(
            obj,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
            exclude_unset=exclude_unset,
            custom_encoder=custom_encoder,
        )

    if isinstance(obj, BaseModel) or dataclasses.is_dataclass(obj):
        return schema_encoder(
            obj,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            custom_encoder=custom_encoder,
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
        custom_encoder=custom_encoder,
    )
