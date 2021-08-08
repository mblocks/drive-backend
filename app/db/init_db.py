# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.db import models


def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next line
    # Base.metadata.create_all(bind=engine)
    if db.query(models.Document).count() == 0:
        db.add(models.Document(name='root',type='dir')) # first user is admin
        db.add(models.Ship(category='breadcrumb',parent='1',object_id='1',order=1))        
        db.commit()
