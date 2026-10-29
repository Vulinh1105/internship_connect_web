"""Phân trang dùng chung: ?page=1&page_size=20."""
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import func, select

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginate(db, stmt, params: PageParams, order_by=None, options=()):
    """Chạy câu truy vấn có phân trang. Trả về (danh sách dòng, tổng số dòng)."""
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows_stmt = stmt
    if options:
        rows_stmt = rows_stmt.options(*options)
    if order_by:
        rows_stmt = rows_stmt.order_by(*order_by)
    rows = db.scalars(rows_stmt.limit(params.page_size).offset(params.offset)).unique().all()
    return rows, total


def make_page(items: list, total: int, params: PageParams) -> dict:
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}
