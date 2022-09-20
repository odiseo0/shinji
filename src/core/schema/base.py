from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import BaseModel as _BaseModel, ValidationError, Field
from pydantic.error_wrappers import ErrorWrapper
from pydantic.utils import ROOT_KEY

from ..utils import deserialize_object, serialize_object, add_timezone_to_datetime

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny


class BaseModel(_BaseModel):
    """Base schema for all objects."""

    id: Any = Field(default_factory=uuid4)

    class Config:
        exclude = set()
        orm_mode = True
        smart_union = True
        use_enum_values = True
        arbitrary_types_allowed = True
        json_loads = deserialize_object
        json_dumps = serialize_object
        json_encoders = {
            datetime: add_timezone_to_datetime,
        }

    @classmethod
    def parse_obj(cls: type[BaseModel], obj: Any) -> BaseModel:
        """Redefined to use `vars()` instead of `dict()`."""
        obj = cls._enforce_dict_if_root(obj)

        if not isinstance(obj, dict):
            try:
                obj = dict(obj)
            except Exception:
                try:
                    obj = vars(obj)
                except Exception as e:
                    exc = TypeError(
                        f"{cls.__name__} expected dict not {obj.__class__.__name__}"
                    )
                    raise ValidationError([ErrorWrapper(exc, loc=ROOT_KEY)], cls) from e

        return cls(**obj)

    def dict(
        self,
        *,
        include: AbstractSetIntStr | MappingIntStrAny = None,
        exclude: AbstractSetIntStr | MappingIntStrAny = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
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
