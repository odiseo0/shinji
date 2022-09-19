from datetime import datetime
from enum import Enum, EnumMeta
from typing import Any

from pydantic import BaseModel as _BaseModel
from pydantic.typing import AbstractSetIntStr, MappingIntStrAny

from src.utils import deserialize_object, serialize_object, add_timezone_to_datetime


SetIntStr = set[int | str]
DictStrAny = dict[str, Any]


class BaseModel(_BaseModel):
    class Config:
        """Configuration for schemas."""

        exclude: set[str] = set()
        orm_mode = True
        use_enum_values = True
        arbitrary_types_allowed = True
        json_loads = deserialize_object
        json_dumps = serialize_object
        json_encoders = {
            datetime: add_timezone_to_datetime,
            Enum: lambda enum: enum.value if enum else None,
            EnumMeta: None,
        }

    def dict(
        self,
        *,
        include: AbstractSetIntStr | MappingIntStrAny = None,
        exclude: AbstractSetIntStr | MappingIntStrAny = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False
    ) -> DictStrAny:
        exclude = exclude or set()
        exclude = exclude.union(getattr(self.Config, "exclude", set()))

        if len(exclude) == 0:
            exclude = None

        return super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
