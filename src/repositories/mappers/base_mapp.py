from typing import TypeVar, Type, Generic

from pydantic import BaseModel
from sqlalchemy import Row, RowMapping

from src.db import Base

DBModelType = TypeVar("DBModelType", bound=Base)
SchemaType = TypeVar("SchemaType", bound=BaseModel)


class DataMapper(Generic[DBModelType, SchemaType]):
    db_model: Type[DBModelType]
    schemas: Type[SchemaType]

    @classmethod
    def map_to_domain_entity(cls, data: Base | dict | Row | RowMapping) -> SchemaType:
        return cls.schemas.model_validate(data, from_attributes=True)

    @classmethod
    def map_to_persistence_entity(cls, data: BaseModel) -> Base:
        return cls.db_model(**data.model_dump())
