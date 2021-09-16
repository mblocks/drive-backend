# -*- coding: utf-8 -*-
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased
from app.db.models import Document, Ship
from app.schemas import DocumentCreate, DocumentUpdate
from .base_lite import CRUDBase


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):

    def create_dir(self, db: Session, *, dir, current_user):
        if dir.parent:
            parent = self.get_dir(db, id=dir.parent, current_user=current_user)
            if not parent:
                return None
        else:
            parent = self.get_home(db, current_user=current_user)

        db_dir = Document(type='dir', name=dir.name,
                          parent=parent.id, data_created_by=current_user.id)
        db.add(db_dir)
        db.flush()
        breadcrumb = db.query(Ship).filter(Ship.parent == parent.id).all()
        for item in breadcrumb:
            db.add(Ship(category='breadcrumb', parent=db_dir.id, object_id=item.object_id,
                   order=item.order, data_created_by=db_dir.data_created_by))
        db.add(Ship(category='breadcrumb', parent=db_dir.id, object_id=db_dir.id,
               order=len(breadcrumb)+1, data_created_by=db_dir.data_created_by))
        db.commit()
        return db_dir

    def get_home(self, db: Session, current_user):
        find_home = super().get(db,
                                filter={'parent': 1, 'name': current_user.id},
                                select=['id']
                                )
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
            return super().get(db,
                               filter={'parent': 1, 'name': current_user.id},
                               select=['id']
                               )

    def get_dir(self, db: Session, id, current_user):
        if id:
            dir = super().get(db,
                           filter={'id': id, 'data_created_by': current_user.id},
                           select=['id']
                           )
            if dir:
                return dir
        return self.get_home(db, current_user)

    def move(self, db: Session, *, target, documents, current_user):
        db.query(Document)\
            .filter(Document.id.in_(documents))\
            .update({'parent': target}, synchronize_session=False)
        query_orders = db.query(Ship.parent, func.max(Ship.order).label('order'))\
                         .filter(Ship.parent.in_(documents+[target]),
                                 Ship.data_enabled == True,
                                 Ship.data_created_by == current_user.id)\
                         .group_by(Ship.parent).all()
        query_target_ship = db.query(Ship).with_entities(Ship.object_id, Ship.order).filter(
            Ship.parent == target, Ship.data_enabled == True).order_by(Ship.order.asc()).all()
        offset_orders = {}
        target_ship = [(item.object_id, item.order)
                       for item in query_target_ship]
        Ship_alias = aliased(Ship)
        for item in query_orders:
            offset_orders[item.parent] = item.order
        for item in query_orders:
            if item.parent != target:
                #offset_orders[item.parent] = offset_orders[item.parent] - offset_orders[target]
                item_offset = offset_orders[item.parent] - \
                    offset_orders[target]
                filter_exists = db.query(Ship_alias).filter(
                    Ship_alias.parent == Ship.parent,
                    Ship_alias.object_id == item.parent, Ship_alias.data_enabled == True, Ship_alias.data_created_by == current_user.id)

                # delete self ship before self
                db.query(Ship)\
                    .filter(filter_exists.exists(), Ship.data_created_by == current_user.id, Ship.order < offset_orders[item.parent])\
                    .update({'data_enabled': False}, synchronize_session=False)
                # insert target ship before self
                for item_ship in db.query(Ship).filter(filter_exists.exists(), Ship.parent == Ship.object_id).all():
                    for item_target_object_id, item_target_order in target_ship:
                        db.add(Ship(category='breadcrumb', parent=item_ship.parent,
                                    object_id=item_target_object_id, order=item_target_order, data_created_by=current_user.id))
                # fix self ship
                db.query(Ship)\
                    .filter(Ship.object_id == item.parent, Ship.data_created_by == current_user.id)\
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
        target_document = self.get(db, filter={'id': target})
        if not target_document:
            # target not exists
            return []
        relation_exists = db.query(Ship).filter(Ship.object_id.in_(
            documents), Ship.parent == Document.id, Ship.data_enabled == True, Ship.data_created_by == current_user.id)
        relation_documents = {}
        for item in db.query(Document).filter(relation_exists.exists(), Document.data_enabled == True).all():
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
                                    Ship.data_enabled == True)
        db.query(Document)\
          .filter(relation_exists.exists(),
                  Document.data_created_by == current_user.id,
                  Document.data_enabled == True)\
          .update({'data_enabled': False}, synchronize_session=False)
        db.query(Ship)\
          .filter(relation_exists.exists(),
                  Ship.data_created_by == current_user.id,
                  Ship.data_enabled == True)\
          .update({'data_enabled': False}, synchronize_session=False)
        db.query(Document)\
          .filter(Document.id.in_(documents),
                  Document.data_created_by == current_user.id,
                  Document.data_enabled == True)\
          .update({'data_enabled': False}, synchronize_session=False)
        db.commit()
        return documents

    def download(self, db: Session, *, id, current_user):
        document = super().get(db, filter={
            'id': id, 'data_created_by': current_user.id}, select=['id', 'name', 'file'])
        if not document:
            return None
        return '/minio/download_{}_url'.format(document.id)

    def download_multiple(self, db: Session, documents, current_user):
        relation_exists = db.query(Ship)\
                            .filter(Ship.object_id.in_(documents),
                                    Ship.parent == Document.id,
                                    Ship.data_enabled == True)
        download_documents = db.query(Document)\
                               .with_entities(Document.id, Document.name, Document.file)\
                               .filter(relation_exists.exists(),
                                       Document.data_created_by == current_user.id,
                                       Document.data_enabled == True)
        return '/minio/download_{}_url'.format(documents)


document = CRUDDocument(Document)
