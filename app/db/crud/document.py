# -*- coding: utf-8 -*-
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.models import Document, Ship
from app.schemas import DocumentCreate, DocumentUpdate
from .base import CRUDBase


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):

    def get_home(self, db: Session, current_user):
        find_home = db.query(Document).with_entities(Document.id).filter(
            Document.parent == 1, Document.name == current_user.id).first()
        if find_home:
            return find_home
        else:
            home = Document(name=current_user.id, type='dir',
                            parent=1, data_created_by=current_user.id)
            db.add(home)
            db.flush()
            db.add(Ship(category='breadcrumb', parent=home.id,
                   object_id='1', order=1, data_created_by=current_user.id))
            db.add(Ship(category='breadcrumb', parent=home.id,
                   object_id=home.id, order=2, data_created_by=current_user.id))
            db.commit()
            return db.query(Document).with_entities(Document.id).filter(Document.parent == 1, Document.name == current_user.id).first()

    def get_dir(self, db: Session, id, current_user):
        return db.query(Document)\
                 .with_entities(Document.id)\
                 .filter(Document.id == id, Document.data_created_by == current_user.id).first()

    def move(self, db: Session, target, documents, current_user):
        query_orders = db.query(Ship.parent, func.max(Ship.order).label('order'))\
                         .filter(Ship.parent.in_(documents+[target]), Document.data_created_by == current_user.id)\
                         .group_by(Ship.parent).all()
        offset_orders = {}
        target_ship = [(item.object_id, item.order) for item in db.query(Ship).with_entities(
            Ship.object_id, Ship.order).filter(Ship.parent == target).order_by(Ship.order.asc()).all()]
        for item in query_orders:
            offset_orders[item.parent] = item.order
        for item in query_orders:
            if item.parent != target:
                #offset_orders[item.parent] = offset_orders[item.parent] - offset_orders[target]
                item_offset = offset_orders[item.parent] - \
                    offset_orders[target]
                filter_exists = db.query(Ship).filter(
                    Ship.object_id == item.parent, Ship.data_enabled == 1, Ship.data_created_by == current_user.id)

                # delete self ship before self
                db.query(Ship)\
                    .filter(filter_exists.exists(), Ship.data_created_by == current_user.id, Ship.order < offset_orders[item.parent])\
                    .update({'data_enabled': 0}, synchronize_session=False)
                # insert target ship before self
                for item_target_object_id, item_target_order in target_ship:
                    db.add(Ship(category='breadcrumb', parent=item.parent,
                           object_id=item_target_object_id, order=item_target_order, data_created_by=current_user.id))
                # fix self ship
                db.query(Ship)\
                    .filter(Ship.parent == item.parent, Ship.data_created_by == current_user.id)\
                    .update({'order': (Ship.order - (item_offset) + 1)})
                # fix ship after self
                db.query(Ship)\
                    .filter(filter_exists.exists(), Ship.order > offset_orders[item.parent])\
                    .update({"order": (Ship.order - (item_offset) + 1)}, synchronize_session=False)

                db.commit()

        return offset_orders

    def _loop_copy(self, db: Session, target, documents, current_user):
        for item in documents:
            document = Document(name=item.name,
                                type=item.type,
                                file=item.file,
                                size=item.size,
                                parent=target.id,
                                data_created_by=current_user.id,
                                )
            db.add(document)
            db.flush()
            if document.type == 'dir':
                for item_breadcrumb in target.breadcrumb:
                    db.add(Ship(category='breadcrumb', parent=document.id,
                           object_id=item_breadcrumb.object_id, order=item_breadcrumb.order, data_created_by=current_user.id,))
                db.add(Ship(category='breadcrumb', parent=document.id,
                       object_id=document.id, order=len(target.breadcrumb)+1, data_created_by=current_user.id,))
            if len(item.children) > 0:
                self._loop_copy(db, target=document,
                            documents=item.children, current_user=current_user)

    def copy(self, db: Session, target, documents, current_user):
        """
        find relationship documents with selected documents generate a dict with document's parent as key
        """
        target_document = self.get(db, id=target)
        if not target_document:
            # target not exists
            return []
        relation_exists = db.query(Ship).filter(Ship.object_id.in_(
            documents), Ship.parent == Document.id, Ship.data_enabled == 1, Ship.data_created_by == current_user.id)
        relation_documents = {}
        for item in db.query(Document).filter(relation_exists.exists(), Document.data_enabled == 1).all():
            item.children = []
            relation_documents[item.id] = item

        while len(list(filter(lambda item: not hasattr(item, 'checked'), relation_documents.values()))) > 0:
            for item in filter(lambda item: not hasattr(item, 'checked'), relation_documents.values()):
                if relation_documents.get(int(item.parent)):
                    relation_documents[int(item.parent)].children.append(item)
                relation_documents[item.id].checked = True
        tree_documents = list(
            filter(lambda item: item.id in documents, relation_documents.values()))

        self._loop_copy(db, target=target_document,
                    documents=tree_documents, current_user=current_user)
        db.commit()
        return tree_documents

    def delete(self, db: Session, documents, current_user):
        relation_exists = db.query(Ship)\
                            .filter(Ship.object_id.in_(documents),
                                    Ship.parent == Document.id,
                                    Ship.data_enabled == 1)
        db.query(Document)\
          .filter(relation_exists.exists(),
                  Document.data_created_by == current_user.id,
                  Document.data_enabled == 1)\
          .update({'data_enabled': 0}, synchronize_session=False)
        db.commit()
        return documents

    def download(self, db: Session, id, current_user):
        document = db.query(Document)\
                     .with_entities(Document.id, Document.name, Document.file)\
                     .filter(Document.id == id,
                             Document.data_created_by == current_user.id,
                             Document.data_enabled == 1).first()
        if not document:
            return None
        return '/minio/download_{}_url'.format(document.id)

    def download_multiple(self, db: Session, documents, current_user):
        relation_exists = db.query(Ship)\
                            .filter(Ship.object_id.in_(documents),
                                    Ship.parent == Document.id,
                                    Ship.data_enabled == 1)
        download_documents = db.query(Document)\
                               .with_entities(Document.id, Document.name, Document.file)\
                               .filter(relation_exists.exists(),
                                       Document.data_created_by == current_user.id,
                                       Document.data_enabled == 1)
        return '/minio/download_{}_url'.format(documents)

    def after_create(self, db: Session, *, db_obj, obj_in):
        if db_obj.type == 'dir':
            breadcrumb = db.query(Ship).filter(
                Ship.parent == db_obj.parent).all()
            for item in breadcrumb:
                db.add(Ship(category='breadcrumb', parent=db_obj.id,
                       object_id=item.object_id, order=item.order, data_created_by=db_obj.data_created_by))
            db.add(Ship(category='breadcrumb', parent=db_obj.id,
                   object_id=db_obj.id, order=len(breadcrumb)+1, data_created_by=db_obj.data_created_by))


document = CRUDDocument(Document)
