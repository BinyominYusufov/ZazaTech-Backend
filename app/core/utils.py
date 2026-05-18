"""Misc helpers: slug generation and uniqueness.

`unique_slug` is synchronous (sync SQLAlchemy project — no AsyncSession).
"""

from __future__ import annotations

from slugify import slugify as _slugify
from sqlmodel import Session, select

from app.models.blog import Blog


def slugify(title: str) -> str:
    """Title -> URL slug. python-slugify lowercases, replaces spaces with '-',
    strips non-alphanumerics and transliterates Cyrillic to Latin."""
    return _slugify(title)


def unique_slug(
    base: str,
    session: Session,
    exclude_id: int | None = None,
) -> str:
    """Return `base`, or `base-2`, `base-3`, ... until free in `blogs.slug`.

    `exclude_id` lets a row keep its own slug on PUT without self-conflict.
    """
    base = base or "post"
    candidate = base
    suffix = 2
    while True:
        existing = session.exec(
            select(Blog).where(Blog.slug == candidate)
        ).first()
        if existing is None or existing.id == exclude_id:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1
