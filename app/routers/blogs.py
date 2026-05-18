"""CRUD for Blogs. Sync SQLModel session (project is synchronous).

GET endpoints are public; POST/PUT/DELETE require an authenticated user.
`tags` is sent as a JSON-array string and stored as a JSON string;
BlogResponse always emits it back as list[str].
"""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.files import delete_file, save_upload
from app.core.utils import slugify, unique_slug
from app.dependencies.auth import get_current_user
from app.models.blog import Blog, BlogResponse

router = APIRouter(prefix="/api/blogs", tags=["blogs"])

SessionDep = Annotated[Session, Depends(get_session)]


def _parse_tags(raw: str) -> list[str]:
    """Parse a JSON-array string like '["python","fastapi"]' into list[str]."""
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='tags must be a JSON array, e.g. ["python","fastapi"]',
        )
    if not isinstance(value, list) or not all(isinstance(i, str) for i in value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tags must be a JSON array of strings",
        )
    return value


@router.get("", response_model=list[BlogResponse])
def list_blogs(
    session: SessionDep,
    published: bool | None = None,
):
    statement = select(Blog)
    if published is not None:
        statement = statement.where(Blog.published == published)
    return session.exec(statement).all()


@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(blog_id: int, session: SessionDep):
    blog = session.get(Blog, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found"
        )
    return blog


@router.post(
    "",
    response_model=BlogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
def create_blog(
    session: SessionDep,
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    tags: Annotated[str, Form()] = "[]",
    published: Annotated[bool, Form()] = False,
    cover_image: Annotated[UploadFile | None, File()] = None,
):
    blog = Blog(
        title=title,
        content=content,
        slug=unique_slug(slugify(title), session),
        tags=json.dumps(_parse_tags(tags)),
        published=published,
    )
    if cover_image is not None:
        blog.cover_image = save_upload(cover_image, "blogs")

    session.add(blog)
    session.commit()
    session.refresh(blog)
    return blog


@router.put(
    "/{blog_id}",
    response_model=BlogResponse,
    dependencies=[Depends(get_current_user)],
)
def update_blog(
    blog_id: int,
    session: SessionDep,
    title: Annotated[str | None, Form()] = None,
    content: Annotated[str | None, Form()] = None,
    tags: Annotated[str | None, Form()] = None,
    published: Annotated[bool | None, Form()] = None,
    cover_image: Annotated[UploadFile | None, File()] = None,
):
    blog = session.get(Blog, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found"
        )

    if title is not None and title != blog.title:
        blog.title = title
        blog.slug = unique_slug(slugify(title), session, exclude_id=blog.id)
    if content is not None:
        blog.content = content
    if tags is not None:
        blog.tags = json.dumps(_parse_tags(tags))
    if published is not None:
        blog.published = published
    if cover_image is not None:
        if blog.cover_image:
            delete_file(blog.cover_image)
        blog.cover_image = save_upload(cover_image, "blogs")

    session.add(blog)
    session.commit()
    session.refresh(blog)
    return blog


@router.delete("/{blog_id}", dependencies=[Depends(get_current_user)])
def delete_blog(blog_id: int, session: SessionDep) -> dict:
    blog = session.get(Blog, blog_id)
    if blog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found"
        )
    if blog.cover_image:
        delete_file(blog.cover_image)
    session.delete(blog)
    session.commit()
    return {"success": True, "message": "Blog deleted"}
