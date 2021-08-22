# -*- coding: utf-8 -*-
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from minio.datatypes import PostPolicy
from datetime import datetime, timedelta
from app import deps, schemas, utils
from app.db import crud

router = APIRouter()


@router.get("/dirs", response_model=List[schemas.Dir])
async def query_dir(db: Session = Depends(deps.get_db),
                    current_user: schemas.CurrentUser = Depends(
                        deps.get_current_user),
                    parent: int = None):
    """
    Find current_user's home dir.\n
    Filter parent by home if parent is none.
    """
    search = {
        'type': 'dir',
        'data_enabled': True,
        'data_created_by': current_user.id,
        'parent': parent
    }
    if not parent:
        home = crud.document.get_home(db, current_user=current_user)
        search['parent'] = home.id
    return crud.document.get_multi(db, search=search, select=['id', 'name'], select_alias={'parent': 'NULL' if parent is None else str(parent)})


@router.post("/dirs", response_model=schemas.Document)
async def create_dir(payload: schemas.DirCreate,
                     db: Session = Depends(deps.get_db),
                     current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    dir = crud.document.create_dir(db=db, dir=payload, current_user=current_user)  # nopep8
    if not dir:
        raise HTTPException(status_code=404, detail=[
            {
                "loc": ["body", "parent"],
                "msg": "parent not exists",
                "type": "value_error"
            },
        ])
    return dir


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
    upload_path = '{}/uploads/{}/{}/'.format(
        current_user.id, datetime.today().strftime('%Y%m%d'), utils.get_uuid())
    policy.add_starts_with_condition('key', upload_path)
    form_data = minio_client.presigned_post_policy(policy)
    form_data['key'] = upload_path
    return form_data


@router.get("/breadcrumb")
async def get_breadcrumb(parent: str = None,
                         db: Session = Depends(deps.get_db),
                         current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Get breadcrumb
    """
    if parent is None:
        return []
    dir = crud.document.find(db, search={
        'id': parent,
        'data_enabled': True,
        'data_created_by': current_user.id
    }, select=['id'])
    if not dir:
        return []
    breadcrumb = crud.ship.get_breadcrumb(db, id=dir.id)
    return breadcrumb[2:]


@router.get("/documents")
async def query_document(db: Session = Depends(deps.get_db),
                         current_user: schemas.CurrentUser = Depends(
                             deps.get_current_user),
                         parent: int = None,
                         page: int = 1,
                         per_page: int = 50,
                         ):
    search = {
        'data_created_by': current_user.id,
        'data_enabled': True,
        'parent': parent
    }
    if not parent:
        home = crud.document.get_home(db, current_user=current_user)
        search['parent'] = home.id
    return crud.document.get_multi(db, search=search, skip=(page-1)*per_page, limit=per_page)


@router.post("/documents/move")
async def move_document(payload: schemas.ShipMove,
                        db: Session = Depends(deps.get_db),
                        current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Find target's breadcrumb and documents's breadcrumb,compare document's max order with target's max order and count offset
    """
    if not payload.target:
        home = crud.document.get_home(db, current_user=current_user)
        payload.target = home.id
    return crud.document.move(db, target=payload.target, documents=payload.documents, current_user=current_user)


@router.post("/documents/copy", response_model=List[schemas.Document])
async def copy_document(payload: schemas.ShipCopy,
                        db: Session = Depends(deps.get_db),
                        current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Find target's breadcrumb and documents's breadcrumb,compare document's max order with target's max order and count offset
    """
    if not payload.target:
        home = crud.document.get_home(db, current_user=current_user)
        payload.target = home.id
    crud.document.copy(db, payload.target, payload.documents, current_user=current_user)  # nopep8
    search = {
        'type': 'dir',
        'data_enabled': True,
        'data_created_by': current_user.id,
        'parent': payload.target
    }
    return crud.document.get_multi(db, search=search, select=['id', 'name', 'type', 'parent'])


@router.post("/documents/delete")
async def delete_document(payload: List[int],
                          db: Session = Depends(deps.get_db),
                          current_user: schemas.CurrentUser = Depends(deps.get_current_user)):
    """
    Find target's breadcrumb and documents's breadcrumb,compare document's max order with target's max order and count offset
    """
    return crud.document.delete(db, documents=payload, current_user=current_user)


@router.post("/documents/update")
async def update_document(payload: schemas.DocumentUpdate,
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
