"""CRUD for Projects. Sync SQLModel session (project is synchronous).

GET endpoints are public; POST/PUT/DELETE require an authenticated user.
`technologies` is sent as a JSON-array string in the form and stored as a
JSON string; ProjectResponse always emits it back as list[str].
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
from app.dependencies.auth import get_current_user
from app.models.project import Project, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])

SessionDep = Annotated[Session, Depends(get_session)]


def _parse_technologies(raw: str) -> list[str]:
    """Parse a JSON-array string like '["React","Node"]' into list[str]."""
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='technologies must be a JSON array, e.g. ["React","Node"]',
        )
    if not isinstance(value, list) or not all(isinstance(i, str) for i in value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="technologies must be a JSON array of strings",
        )
    return value


@router.get("", response_model=list[ProjectResponse])
def list_projects(session: SessionDep):
    return session.exec(select(Project)).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, session: SessionDep):
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
def create_project(
    session: SessionDep,
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    category: Annotated[str, Form()],
    technologies: Annotated[str, Form()] = "[]",
    github_url: Annotated[str | None, Form()] = None,
    live_url: Annotated[str | None, Form()] = None,
    featured: Annotated[bool, Form()] = False,
    image: Annotated[UploadFile | None, File()] = None,
):
    project = Project(
        title=title,
        description=description,
        category=category,
        technologies=json.dumps(_parse_technologies(technologies)),
        github_url=github_url,
        live_url=live_url,
        featured=featured,
    )
    if image is not None:
        project.image = save_upload(image, "projects")

    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    dependencies=[Depends(get_current_user)],
)
def update_project(
    project_id: int,
    session: SessionDep,
    title: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    category: Annotated[str | None, Form()] = None,
    technologies: Annotated[str | None, Form()] = None,
    github_url: Annotated[str | None, Form()] = None,
    live_url: Annotated[str | None, Form()] = None,
    featured: Annotated[bool | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
):
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if title is not None:
        project.title = title
    if description is not None:
        project.description = description
    if category is not None:
        project.category = category
    if technologies is not None:
        project.technologies = json.dumps(_parse_technologies(technologies))
    if github_url is not None:
        project.github_url = github_url
    if live_url is not None:
        project.live_url = live_url
    if featured is not None:
        project.featured = featured
    if image is not None:
        if project.image:
            delete_file(project.image)
        project.image = save_upload(image, "projects")

    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.delete("/{project_id}", dependencies=[Depends(get_current_user)])
def delete_project(project_id: int, session: SessionDep) -> dict:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.image:
        delete_file(project.image)
    session.delete(project)
    session.commit()
    return {"success": True, "message": "Project deleted"}
