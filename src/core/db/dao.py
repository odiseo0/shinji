import asyncio
from contextlib import contextmanager
from typing import Protocol, TypeVar, Any, Generic, overload, cast
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func as sql_func
from sqlalchemy.engine import Result
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty
from sqlalchemy.sql import Executable, select, Select
from sqlalchemy.sql.selectable import ReturnsRows
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.utils import jsonable_encoder
from .model import Base
from .exceptions import DAOConflictException, DAOExceptionBase


select = cast(Select, select)
ModelType = TypeVar("ModelType", bound=Base)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class DAOProtocol(Protocol[ModelType]):
    """Protocol for all data access objects."""

    @contextmanager
    def catch_sqlalchemy_exception(self) -> Any:
        """
        Catch `SQLAlchemyError` within context to raise a `DAOExceptionBase`.
        """
        try:
            yield
        except IntegrityError as e:
            raise DAOConflictException() from e
        except SQLAlchemyError as e:
            raise DAOExceptionBase(500, f"An exception occurred: {e}") from e

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

    async def create(self, db: AsyncSession, db_obj: CreateSchema) -> ModelType:
        ...

    async def update(
        self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchema
    ) -> ModelType:
        ...

    async def delete(self, db: AsyncSession, db_obj: ModelType) -> ModelType:
        ...


class DAOBase(DAOProtocol, Generic[ModelType]):
    """DAO Base that performs all the basic CRUD operations."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def execute(
        self, session: AsyncSession, statement: Executable, **kwargs: Any
    ) -> Result:
        """
        Execute an `statement`.
        """
        with self.catch_sqlalchemy_exception():
            return await session.execute(statement, **kwargs)

    async def get(self, db: AsyncSession, id: UUID) -> ModelType | None:
        """Get single item by id."""
        statement: Select = select(self.model).where(self.model.id == id)

        with self.catch_sqlalchemy_exception():
            results = await self.execute(db, statement)
            db_object = results.first()

        if db_object is None:
            return None

        return cast(ModelType, db_object[0])

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> tuple[list[ModelType], int]:
        """Get multiple items."""
        statement: Select = select(self.model)
        paginated = statement.offset(skip).limit(limit)

        with self.catch_sqlalchemy_exception():
            [count, results] = await asyncio.gather(
                self.count(db, statement), self.execute(db, paginated)
            )

        return [result[0] for result in results.unique().all()], count

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchema, commit: bool = True
    ) -> ModelType:
        """Insert item."""
        with self.catch_sqlalchemy_exception():
            obj_in_data = jsonable_encoder(obj_in)

            db_obj = self.model(**obj_in_data)
            db.add(db_obj)

            if commit:
                await db.commit()
                await db.refresh(db_obj)

        return db_obj

    async def create_many(
        self,
        db: AsyncSession,
        db_objects: list[CreateSchema],
        commit: bool = True,
    ) -> list[ModelType]:
        """Create Many"""
        with self.catch_sqlalchemy_exception():
            list(map(db.add, db_objects))

            if commit:
                await db.commit()

        return db_objects

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

        with self.catch_sqlalchemy_exception():
            db.add(db_obj)

            if commit:
                await db.commit()
                await db.refresh(db_obj)

        return db_obj

    async def delete(
        self, db: AsyncSession, db_object: ModelType, commit: bool = True
    ) -> ModelType:
        with self.catch_sqlalchemy_exception():
            deleted = await db.delete(db_object)

            if commit:
                await db.commit()

        return deleted

    async def count(self, db: AsyncSession, statement: Select) -> int:
        count_statement = statement.with_only_columns(
            [sql_func.count()],
            maintain_column_froms=True,
        ).order_by(None)

        with self.catch_sqlalchemy_exception():
            results = await self.execute(db, count_statement)

        return results.scalar_one()

    def order_by(
        self,
        statement: Select,
        ordering: list[tuple[list[str], bool]],
    ) -> Select:
        for (accessors, is_desc) in ordering:
            field: InstrumentedAttribute

            if len(accessors) == 1:
                try:
                    field = getattr(self.model, accessors[0])
                    statement = statement.order_by(
                        field.desc() if is_desc else field.asc()
                    )
                except AttributeError:
                    pass
            else:
                valid_field = True
                model = self.model

                for accessor in accessors:
                    try:
                        field = getattr(model, accessor)

                        if isinstance(field.prop, RelationshipProperty):
                            if field.prop.lazy != "joined":
                                statement = statement.join(field)

                            model = field.prop.entity.class_
                    except AttributeError:
                        valid_field = False
                        break

                if valid_field:
                    statement = statement.order_by(
                        field.desc() if is_desc else field.asc()
                    )

        return statement