# -*- coding: utf-8 -*-
from posixpath import split
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app import deps
from app.db import models

router = APIRouter()


@router.post("/minio")
async def webhooks_minio(request: Request, db: Session = Depends(deps.get_db)):
    """
    Recive minio send request notification\
    key sample: /drive/home/{user_id}/{dir_id}/{timestamp}/filename.jpg
    """
    event = await request.json()
    key = event.get('Key')
    split_key = key.split("/")
    bucket = split_key[0]  # record.get('s3').get('bucket').get('name')
    user_id = split_key[2]
    parent = split_key[3]
    name = split_key[-1]  # file's name with ext
    type = name.split(".")[-1]  # file's name's ext
    file = key[len(bucket)+1:]  # exclude bucket name
    for record in event.get('Records'):
        object = record.get('s3').get('object')
        db.add(models.Document(name=name,
                               type=type.lower(),
                               content_type=object.get('contentType'),
                               file=file,
                               parent=parent,
                               size=object.get('size'),
                               etag=object.get('eTag'),
                               data_created_by=user_id
                               ))
        db.commit()
    return 'save'
