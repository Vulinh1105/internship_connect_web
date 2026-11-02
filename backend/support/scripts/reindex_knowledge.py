import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))
from app.main import app
from app.core.database import SessionLocal
from app.modules.documents.service import reindex_knowledge

if __name__ == "__main__":
    with SessionLocal() as db:
        results = reindex_knowledge(db)
        for result in results:
            print(result)
        if any(r["status"] != "indexed" for r in results):
            raise SystemExit(1)
