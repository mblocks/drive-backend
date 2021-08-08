# -*- coding: utf-8 -*-
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from minio.datatypes import PostPolicy
from datetime import datetime, timedelta
from app import deps, schemas, utils
from app.db import crud

router = APIRouter()


@router.get("/dirs", response_model=List[schemas.Document])
async def query_dir(db: Session = Depends(deps.get_db),
                    current_user: schemas.CurrentUser = Depends(
                        deps.get_current_user),
                    parent: int = None):
    """
    Find current_user's home dir.\n
    Filter parent by home if parent is none.
    """
    home = crud.document.get_home(db, current_user=current_user)
    search = {
        'type': 'dir',
        'parent': parent if parent else home.id,
        'data_created_by': current_user.id
    }
    return crud.document.get_multi(db, search=search)


@router.post("/dirs", response_model=schemas.Document)
async def create_dir(payload: schemas.DirCreate,
                     db: Session = Depends(deps.get_db),
                     current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    obj_in = payload.dict()
    obj_in['data_created_by'] = current_user.id
    obj_in['type'] = 'dir'
    if payload.parent:
        parent_dir = crud.document.get_dir(
            db, id=payload.parent, current_user=current_user)
        if parent_dir:
            obj_in['parent'] = payload.parent
        else:
            raise HTTPException(status_code=404, detail=[
                {
                    "loc": ["body", "parent"],
                    "msg": "parent not exists",
                    "type": "value_error"
                },
            ])
    else:
        home = crud.document.get_home(db, current_user=current_user)
        obj_in['parent'] = home.id
    created_dir = crud.document.create(db=db, obj_in=obj_in)
    return created_dir


@router.get("/presigned")
async def get_presigned(minio_client=Depends(deps.get_minio),
                        db: Session = Depends(deps.get_db),
                        current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Generate minio presigned url
    """
    policy = PostPolicy(
        "hello", datetime.utcnow() + timedelta(days=10),
    )
    upload_path = '{}/uploads/{}/{}'.format(
        current_user.id, datetime.today().strftime('%Y%m%d'), utils.get_uuid())
    policy.add_starts_with_condition('key', upload_path)
    form_data = minio_client.presigned_post_policy(policy)
    form_data['upload_path'] = upload_path
    return form_data


@router.get("/breadcrumb")
async def get_breadcrumb(dir: str = None,
                         db: Session = Depends(deps.get_db),
                         current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Get breadcrumb
    """
    if dir is None:
        return []
    return crud.ship.get_breadcrumb(db, id=dir)


@router.get("/documents")
async def query_document(db: Session = Depends(deps.get_db),
                         current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    home = crud.document.get_home(db, current_user=current_user)
    search = {'data_created_by': current_user.id, 'parent': home.id}
    return crud.document.get_multi(db, search=search)


@router.post("/documents/move")
async def move_document(payload: schemas.ShipMove,
                        db: Session = Depends(deps.get_db),
                        current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Find target's breadcrumb and documents's breadcrumb,compare document's max order with target's max order and count offset
    """
    return crud.document.move(db, payload.target, payload.documents, current_user=current_user)


@router.post("/documents/copy")
async def copy_document(payload: schemas.ShipCopy,
                        db: Session = Depends(deps.get_db),
                        current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Find target's breadcrumb and documents's breadcrumb,compare document's max order with target's max order and count offset
    """
    return crud.document.copy(db, payload.target, payload.documents, current_user=current_user)


@router.post("/documents/delete")
async def delete_document(payload: List[int],
                        db: Session = Depends(deps.get_db),
                        current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Find target's breadcrumb and documents's breadcrumb,compare document's max order with target's max order and count offset
    """
    return crud.document.delete(db, documents=payload, current_user=current_user)


@router.post("/documents/update")
async def move_document(payload: schemas.DocumentUpdate,
                        db: Session = Depends(deps.get_db),
                        current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Find target's breadcrumb and documents's breadcrumb,compare document's max order with target's max order and count offset
    """
    document = crud.document.find(db, search={
                                  'id': payload.id, 'data_created_by': current_user.id, 'data_enabled': 1})
    if not document:
        raise HTTPException(status_code=404, detail=[
            {
                "loc": ["body", "id"],
                "msg": "document not exists",
                "type": "value_error"
            },
        ])
    return crud.document.update(db, db_obj=document, obj_in=payload)


@router.get("/documents/download")
async def get_breadcrumb(id: str = Query(...),
                         db: Session = Depends(deps.get_db),
                         current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Generate minio download url,keep directory structure
    """
    document = crud.document.download(db, id=id, current_user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail=[
            {
                "loc": ["body", "id"],
                "msg": "document not exists",
                "type": "value_error"
            },
        ])
    return document
