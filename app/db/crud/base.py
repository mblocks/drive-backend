# -*- coding: utf-8 -*-
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from copy import deepcopy
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
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
            if value is not None:
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
                elif attr.endswith(' is NUll'):
                    query = query.filter(getattr(self.model, attr[:-8]) == None)  # noqa: E501
                else:
                    query = query.filter(getattr(self.model, attr) == value)

        return query

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def find(self, db: Session, *, search: Dict[str, str] = {}):
        query = db.query(self.model)
        query = self.__filter(query, search)
        return query.first()

    def get_multi(
        self,
        db: Session,
        *,
        search: Dict[str, str] = {},
        skip: int = 0,
        limit: int = None
    ) -> List[ModelType]:
        query = db.query(self.model)
        query = self.__filter(query, search)
        if limit is not None:
            query = query.offset(skip).limit(limit)
        return query.all()

    def count(
        self,
        db: Session,
        *,
        search: Dict[str, str] = {},
    ) -> int:
        query = db.query(self.model)
        query = self.__filter(query, search)
        return query.count()

    def create(self,
               db: Session,
               *,
               obj_in: CreateSchemaType,
               refresh: bool = True
               ) -> ModelType:
        obj_in_clone = deepcopy(obj_in)
        self.before_create(db, obj_in=obj_in)
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.flush()
        self.after_create(db, db_obj=db_obj, obj_in=obj_in_clone)
        obj_out = jsonable_encoder(db_obj)
        db.commit()
        if refresh:
            db.refresh(db_obj)
            return db_obj
        else:
            return obj_out

    def before_create(self, db: Session, *, obj_in):
        pass

    def after_create(self, db: Session, *, db_obj, obj_in):
        pass

    def before_update(self, db: Session, *, db_obj, obj_in):
        pass

    def after_update(self, db: Session, *, db_obj, obj_in):
        pass

    def create_multi(self,
                     db: Session,
                     *,
                     obj_in: List[CreateSchemaType],
                     refresh: bool = True
                     ) -> List[ModelType]:
        obj_id = []
        obj_out = []
        for item in obj_in:
            item_data = jsonable_encoder(item)
            db_item = self.model(**item_data)
            db.add(db_item)
            db.flush()
            obj_id.append(db_item.id)
            obj_out.append(jsonable_encoder(db_item))
        db.commit()
        if refresh:
            return db.query(self.model).filter(self.model.id.in_(obj_id)).all()
        else:
            return obj_out

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        self.before_update(db, db_obj = db_obj, obj_in= obj_in)
        obj_data = jsonable_encoder(obj_in)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        self.after_update(db, db_obj=db_obj, obj_in=obj_in)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
            return obj
        else:
            return dict(id=id)

    def remove_multi(self, db: Session, *, search: Dict[str, str]) -> List[ModelType]:
        query = db.query(self.model)
        query = self.__filter(query, search)
        affected_rows = query.delete(synchronize_session=False)
        db.commit()
        return affected_rows
