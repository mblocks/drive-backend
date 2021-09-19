# -*- coding: utf-8 -*-
from PIL import Image
from io import BytesIO
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app import deps
from app.db import models

router = APIRouter()
minio_client = deps.get_minio()


def generate_thumbnail(key, *, content_type):
    [category, suffix] = content_type.split('/')
    if category != 'image':
        return None

    file = minio_client.get_object("drive", key)
    thumbnail = 'thumbnail/{}'.format(key)
    with Image.open(file) as im:
        im.thumbnail((400, 400))
        file_stream = BytesIO()
        im.save(file_stream, format=im.format)
        file_stream.seek(0)
        # print(im.format,im.info,im.size,file_stream.tell(),file_stream.getvalue())
        minio_client.put_object(
            "drive", thumbnail, data=file_stream, length=-1, part_size=10*1024*1024)
    return thumbnail


@router.post("/minio")
async def webhooks_minio(request: Request,
                         db: Session = Depends(deps.get_db)):
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
    file_name = split_key[-1]
    file_suffix = file_name.split(".")[-1].lower()  # file's name's suffix
    file_path = key[len(bucket)+1:]  # exclude bucket name
    for record in event.get('Records'):
        object = record.get('s3').get('object')
        thumbnail = generate_thumbnail(
            file_path, content_type=object.get('contentType'))
        db.add(models.Document(name=file_name,
                               type=file_suffix,
                               content_type=object.get('contentType'),
                               file=file_path,
                               parent=parent,
                               thumbnail=thumbnail,
                               size=object.get('size'),
                               etag=object.get('eTag'),
                               data_created_by=user_id
                               ))
        db.commit()
    return 'save'
