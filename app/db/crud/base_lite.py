# -*- coding: utf-8 -*-
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import literal_column
from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def __filter(self, query, search):
        for attr, value in search.items():
            if value:
                if type(value) == str and (value.startswith('*') or value.endswith('*')):  # noqa: E501
                    if value.startswith('*'):
                        value = '%{}'.format(value[1:])
                    if value.endswith('*'):
                        value = '{}%'.format(value[:-1])
                    query = query.filter(getattr(self.model, attr).like(value))
                elif attr.endswith(' !='):
                    query = query.filter(getattr(self.model, attr.strip(' !=')) != value)  # noqa: E501
                elif attr.endswith(' >='):
                    query = query.filter(getattr(self.model, attr.strip(' >=')) >= value)  # noqa: E501
                elif attr.endswith(' <='):
                    query = query.filter(getattr(self.model, attr.strip(' <=')) <= value)  # noqa: E501
                elif attr.endswith(' not in'):
                    query = query.filter(getattr(self.model, attr[:-7]).notin_(value))  # noqa: E501
                elif attr.endswith(' in'):
                    query = query.filter(getattr(self.model, attr[:-3]).in_(value))  # noqa: E501
                else:
                    query = query.filter(getattr(self.model, attr) == value)

        return query

    def _query_data(self, db: Session,
                    *,
                    filter: Dict[str, str] = {},
                    select: List[str] = [],
                    select_alias: Dict[str, str] = {}):
        query = db.query(self.model).filter(self.model.data_enabled == True)
        query = self.__filter(query, filter)
        if select or select_alias:
            query = query.with_entities(*[getattr(self.model, i) for i in select],
                                        *[literal_column(v).label(k) for k, v in select_alias.items()])
        return query

    def get(self,
            db: Session,
            *,
            filter: Dict[str, str],
            select: List[str] = [],
            select_alias: Dict[str, str] = {}) -> Optional[ModelType]:
        query = self._query_data(
            db, filter=filter, select=select, select_alias=select_alias)
        return query.first()

    def query(
        self,
        db: Session,
        *,
        filter: Dict[str, str]={},
        select: List[str] = [],
        select_alias: Dict[str, str] = {},
        skip: int = 0,
        limit: int = None
    ) -> List[ModelType]:
        query = self._query_data(
            db, filter=filter, select=select, select_alias=select_alias)
        if limit is not None:
            query = query.offset(skip).limit(limit)
        return query.all()

    def count(
        self,
        db: Session,
        *,
        filter: Dict[str, str] = {},
    ) -> int:
        query = self._query_data(db, filter=filter, select_alias={
                                 'count': 'count(*)'})
        return query.scalar()

    def create(self,
               db: Session,
               payload: Union[List[CreateSchemaType], CreateSchemaType],
               *,
               refresh: bool = False,
               commit: bool = False,
               ) -> Union[List[ModelType], ModelType]:
        data_id = []
        out_data = []
        create_data = payload if isinstance(payload, list) else [payload]
        for item in create_data:
            db_item = self.model(**jsonable_encoder(item))
            db.add(db_item)
            db.flush()
            data_id.append(db_item.id)
            out_data.append(jsonable_encoder(db_item))
        if commit:
            db.commit()
        if refresh:
            return self.query(db, search={'id in': data_id}) if isinstance(payload, list) else self.get(db, filter={'id in': data_id})
        else:
            return out_data

    def update(
        self,
        db: Session,
        *,
        filter: Dict[str, str],
        payload: Union[UpdateSchemaType, Dict[str, Any]],
        refresh: bool = False,
        commit: bool = False
    ) -> Union[List[ModelType], int]:
        update_data = payload if isinstance(
            payload, dict) else payload.dict(exclude_unset=True)
        query = self._query_data(db, filter=filter)
        affected_rows = query.update({getattr(self.model, k): v for k, v in update_data.items()},  # nopep8
                                     synchronize_session=False
                                    )
        if commit:
            db.commit()
        if refresh:
            return self.get(db, search=filter) if 'id' in filter else self.query(db, search=filter)
        else:
            return affected_rows

    def remove(self, db: Session, filter: Dict[str, str], commit: bool = False) -> ModelType:
        affected_rows = self.update(db, filter=filter, payload={'data_enabled': False}, commit=commit)
        return affected_rows
