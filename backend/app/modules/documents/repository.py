from sqlalchemy import select
from .models import Document


class DocumentRepository:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, document_id):
        return self.db.get(Document, document_id)

    def list_all(self):
        return list(self.db.scalars(select(Document).order_by(Document.id)))

    def save(self, document):
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
