"""Index managed knowledge files on startup without copying source files."""
import hashlib
import json
import logging
import os
from pathlib import Path
from sqlalchemy import select
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.modules.documents.models import Document
from app.modules.documents import service

log = logging.getLogger(__name__)

def sync_knowledge():
    root = Path(os.getenv('KNOWLEDGE_DIR', str(Path(__file__).resolve().parents[3] / 'data' / 'knowledge'))).resolve()
    manifest = Path(os.getenv('RAG_INDEX_DIR', str(root.parent / 'rag-index'))) / 'knowledge_manifest.json'
    if not root.is_dir():
        log.warning('Knowledge folder missing: %s', root)
        return
    manifest.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    counts = {'indexed': 0, 'skipped': 0, 'failed': 0}
    target = (os.getenv('QDRANT_URL', ''), os.getenv('QDRANT_COLLECTION', 'internship-connect-openai'))
    with SessionLocal() as db:
        owner = db.scalar(select(User).where(User.role.in_(['staff', 'admin']), User.is_active == True).order_by(User.id))
        if owner is None:
            log.error('Knowledge sync needs an existing active staff/admin account')
            return
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in {'.pdf', '.docx', '.txt'}:
                continue
            try:
                fingerprint = hashlib.sha256(path.read_bytes() + repr(target).encode()).hexdigest()
                key = str(path.resolve())
                previous = state.get(key, {})
                document = db.get(Document, previous['id']) if previous.get('id') else None
                if document is None:
                    document = db.scalar(select(Document).where(Document.file_path == key))
                if document is not None and document.status == 'indexed' and previous.get('hash') == fingerprint:
                    counts['skipped'] += 1
                    continue
                if document is None:
                    document = Document(owner_id=owner.id, original_filename=path.name, file_path=key, size=path.stat().st_size, status='pending', access_level='public')
                    db.add(document)
                document.size = path.stat().st_size
                db.commit()
                result = service.index(db, document.id)
                if result['status'] != 'indexed':
                    raise RuntimeError(str(result))
                state[key] = {'id': document.id, 'hash': fingerprint}
                temporary = manifest.with_suffix('.tmp')
                temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
                temporary.replace(manifest)
                counts['indexed'] += 1
                log.info('Knowledge indexed: %s', path)
            except Exception:
                db.rollback()
                counts['failed'] += 1
                log.exception('Knowledge indexing failed: %s', path)
    log.info('Knowledge sync finished: %s', counts)


def startup_sync():
    if os.getenv('KNOWLEDGE_AUTO_INDEX', 'false').lower() != 'true':
        return
    try:
        sync_knowledge()
    except Exception:
        log.exception('Knowledge sync failed; inspect configuration and retry')