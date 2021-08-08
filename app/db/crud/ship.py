# -*- coding: utf-8 -*-
from typing import List
from sqlalchemy.orm import Session
from app.db.models import Ship, Document
from app.schemas import ShipCreate, ShipUpdate
from .base import CRUDBase

class CRUDShip(CRUDBase[Ship, ShipCreate, ShipUpdate]):

    def get_breadcrumb(self, db: Session, *, id: int):
        return db.query(Ship, Document)\
                 .with_entities(Document.id, Document.name)\
                 .filter(Ship.object_id==Document.id, Ship.parent==id, Ship.data_enabled==1)\
                 .order_by(Ship.order.asc()).all()


ship = CRUDShip(Ship)
