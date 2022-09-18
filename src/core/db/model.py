import re
from uuid import UUID, uuid4

from sqlalchemy import Column, MetaData
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import registry as _registry
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """Base for all declarative models."""

    table_name_pattern = re.compile(r"(?<!^)(?=[A-Z])")
    convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    id: UUID = Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)

    registry = _registry(metadata=MetaData(naming_convention=convention))

    @declared_attr
    def __tablename__(cls) -> str:
        return re.sub(cls.table_name_pattern, "_", cls.__name__).lower()
