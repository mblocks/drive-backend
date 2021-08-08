# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), index=True)
    type = Column(String(100))
    parent = Column(Integer, index=True)
    file = Column(String(200))
    size = Column(Integer)

    data_enabled = Column(Boolean, default=True)
    data_created_at = Column(TIMESTAMP,default=datetime.utcnow)
    data_updated_at = Column(TIMESTAMP,onupdate=datetime.utcnow)
    data_deleted_at = Column(TIMESTAMP)
    data_created_by = Column(Integer)
    data_updated_by = Column(Integer)
    data_deleted_by = Column(Integer)

    breadcrumb = relationship("Ship",
                        primaryjoin="and_(Document.id==foreign(Ship.parent),Ship.category=='breadcrumb',Ship.data_enabled==1)",
                        lazy='subquery',
                        order_by='Ship.order.asc()'
                        )


class Ship(Base):
    __tablename__ = "ships"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(20))
    parent = Column(Integer) #Document.id,parent has many object_id
    object_id = Column(Integer)
    order = Column(Integer)

    data_enabled = Column(Boolean, default=True)
    data_created_at = Column(TIMESTAMP,default=datetime.utcnow)
    data_updated_at = Column(TIMESTAMP,onupdate=datetime.utcnow)
    data_deleted_at = Column(TIMESTAMP)
    data_created_by = Column(Integer)
    data_updated_by = Column(Integer)
    data_deleted_by = Column(Integer)
