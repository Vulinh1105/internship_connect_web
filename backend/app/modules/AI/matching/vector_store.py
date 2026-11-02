"""Adapter for the existing matching vectors, isolated from RAG embeddings."""
from .embeddings import cosine

class MemoryStore:
    backend = "memory"
    def __init__(self):
        self.collections = {}
    def replace(self, collection, items, dim):
        self.collections[collection] = list(items)
    def search(self, collection, vector, limit):
        hits = [(key, cosine(vector, stored), payload)
                for key, stored, payload in self.collections.get(collection, [])]
        return sorted(hits, key=lambda item: item[1], reverse=True)[:limit]

_store = MemoryStore()
def get_store():
    return _store
