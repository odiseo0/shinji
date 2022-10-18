from __future__ import annotations

import asyncio
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, cast, overload

from pydantic import BaseModel
from sqlalchemy import asc, desc
from sqlalchemy import func as sql_func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty
from sqlalchemy.sql import Executable, Select, select
from sqlalchemy.sql.selectable import ReturnsRows

from core.types import Empty, EmptyType
from ..utils import jsonable_encoder
from .model import Base

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import Result


select = cast("Select", select)
ModelType = TypeVar("ModelType", bound=Base)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


@contextmanager
def catch_sqlalchemy_exception() -> Any:
    """
    Catch `SQLAlchemyError` to raise a `DAOExceptionBase`.
    """
    try:
        yield
    except IntegrityError as e:
        raise Exception() from e
    except SQLAlchemyError as e:
        raise Exception() from e


class DAOProtocol(Protocol[ModelType]):
    """Protocol for all data access objects."""

    @overload
    async def execute(
        self,
        db: AsyncSession,
        statement: ReturnsRows,
        **kwargs: Any,
    ) -> tuple[Any, ...]:
        ...

    @overload
    async def execute(
        self, db: AsyncSession, statement: Executable, **kwargs: Any
    ) -> Result:
        ...

    async def execute(
        self, db: AsyncSession, statement: Executable, **kwargs: Any
    ) -> Result:
        ...

    async def get(self, db: AsyncSession, id: UUID) -> ModelType | None:
        ...

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, **kwargs
    ) -> tuple[list[ModelType], int]:
        ...

    async def create(self, db: AsyncSession, db_obj: CreateSchema) -> ModelType:
        ...

    async def create_many(
        self, db: AsyncSession, obj_ins: list[CreateSchema], commit: bool = True
    ):
        ...

    async def update(
        self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchema
    ) -> ModelType:
        ...

    async def delete(self, db: AsyncSession, db_obj: ModelType) -> ModelType:
        ...


class DAOBase(DAOProtocol, Generic[ModelType, CreateSchema, UpdateSchema]):
    """DAO Base that performs all the basic CRUD operations."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def execute(
        self, db: AsyncSession, statement: Executable, **kwargs: Any
    ) -> Result:
        """Execute an `statement`."""
        with catch_sqlalchemy_exception():
            return await db.execute(statement, **kwargs)

    async def get(self, db: AsyncSession, id: UUID) -> ModelType | EmptyType:
        """Get single item by id."""
        statement: Select = select(self.model).where(self.model.id == id)

        results = await self.execute(db, statement)
        db_object = results.first()

        if db_object is None:
            return Empty

        return cast("ModelType", db_object[0])

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, **kwargs
    ) -> tuple[list[ModelType], int]:
        """Get multiple items."""
        statement: Select = select(self.model).where(
            *[getattr(self.model, k) == v for k, v in kwargs.items()]
        )
        ordered = self.order_by(statement)
        paginated = ordered.offset(skip).limit(limit)

        [count, results] = await asyncio.gather(
            self.count(db, statement), self.execute(db, paginated)
        )

        return [result[0] for result in results.unique().all()], count

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchema, commit: bool = True
    ) -> ModelType:
        """Insert item."""
        with catch_sqlalchemy_exception():
            obj_in_data = jsonable_encoder(obj_in)

            db_obj = self.model(**obj_in_data)
            db.add(db_obj)

            if commit:
                await db.commit()
                await db.refresh(db_obj)

        return db_obj

    async def create_many(
        self, db: AsyncSession, obj_ins: list[CreateSchema], commit: bool = True
    ) -> list[ModelType]:
        """Create Many"""
        with catch_sqlalchemy_exception():
            list(map(db.add, obj_ins))

            if commit:
                await db.commit()

        return obj_ins

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchema | dict[str, Any],
        commit: bool = True,
    ) -> ModelType:
        """Update an item."""
        obj_data = jsonable_encoder(db_obj)

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        with catch_sqlalchemy_exception():
            db.add(db_obj)

            if commit:
                await db.commit()
                await db.refresh(db_obj)

        return db_obj

    async def delete(
        self, db: AsyncSession, db_object: ModelType, commit: bool = True
    ) -> ModelType:
        with catch_sqlalchemy_exception():
            deleted = await db.delete(db_object)

            if commit:
                await db.commit()

        return deleted

    async def count(self, db: AsyncSession, statement: Select) -> int:
        count_statement = statement.with_only_columns(
            [sql_func.count()],
            maintain_column_froms=True,
        ).order_by(None)

        results = await self.execute(db, count_statement)

        return results.scalar_one()

    def order_by(
        self, statement: Select, ordering: list[tuple[str, bool]] | None
    ) -> Select:
        if not ordering:
            return statement

        for (attr, is_desc) in ordering:
            field: InstrumentedAttribute

            try:
                field = getattr(self.model, attr)

                if isinstance(field.prop, RelationshipProperty):
                    if field.prop.lazy != "joined":
                        statement = statement.join(field)

                statement = statement.order_by(desc(field) if is_desc else asc(field))
            except AttributeError as e:
                # NOTE: Handle this error better.
                raise Exception() from e

        return statement
