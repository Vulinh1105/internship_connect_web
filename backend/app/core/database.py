"""Kết nối cơ sở dữ liệu dùng chung cho mọi module."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings


class Base(DeclarativeBase):
    """Class cha của mọi model."""


_url = settings.DATABASE_URL
_kwargs: dict = {"pool_pre_ping": True}

if _url.startswith("sqlite"):
    # SQLite chỉ dùng khi chạy kiểm thử hoặc học thử
    _kwargs["connect_args"] = {"check_same_thread": False}
    if _url in ("sqlite://", "sqlite:///:memory:"):
        _kwargs["poolclass"] = StaticPool

engine = create_engine(_url, **_kwargs)

if _url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, _record):
        # SQLite mặc định không kiểm tra khóa ngoại, bật lên cho giống MySQL
        dbapi_conn.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """Dependency: mở một phiên làm việc cho mỗi request và đóng khi xong."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
