"""Upload managed knowledge through the existing document pipeline."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--owner-id", type=int, required=True)
    args = parser.parse_args()
    from starlette.datastructures import UploadFile
    from app.main import app  # register all models before using metadata
    from app.core.database import SessionLocal
    from app.modules.auth.models import User
    from app.modules.documents import service
    with SessionLocal() as db:
        owner = db.get(User, args.owner_id)
        if owner is None or owner.role not in {"staff", "admin"}:
            parser.error("--owner-id must identify an existing staff/admin user")
        with args.file.open("rb") as stream:
            document = service.upload(db, owner, UploadFile(stream, filename=args.file.name))
        result = service.index(db, document.id)
        print(result)
        if result["status"] != "indexed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
