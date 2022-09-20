import re
import uuid
from datetime import datetime

from sqlalchemy import Column, MetaData, DateTime
from sqlalchemy.dialects.postgresql import UUID
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

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date_added: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_updated: datetime = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    registry = _registry(metadata=MetaData(naming_convention=convention))

    @declared_attr
    def __tablename__(cls) -> str:
        return re.sub(cls.table_name_pattern, "_", f"{cls.__name__}s").lower()
