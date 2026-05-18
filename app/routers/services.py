"""CRUD for Services. Sync SQLModel session (project is synchronous).

GET endpoints are public; POST/PUT/DELETE require an authenticated user.
`technologies` is sent as a JSON-array string in the form and stored as a
JSON string; ServiceResponse always emits it back as list[str].
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
from app.models.service import Service, ServiceResponse

router = APIRouter(prefix="/api/services", tags=["services"])

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


@router.get("", response_model=list[ServiceResponse])
def list_services(session: SessionDep):
    return session.exec(select(Service)).all()


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: int, session: SessionDep):
    service = session.get(Service, service_id)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return service


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_user)],
)
def create_service(
    session: SessionDep,
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    short_description: Annotated[str, Form()],
    price: Annotated[float, Form()],
    technologies: Annotated[str, Form()] = "[]",
    image: Annotated[UploadFile | None, File()] = None,
):
    service = Service(
        title=title,
        description=description,
        short_description=short_description,
        price=price,
        technologies=json.dumps(_parse_technologies(technologies)),
    )
    if image is not None:
        service.image = save_upload(image, "services")

    session.add(service)
    session.commit()
    session.refresh(service)
    return service


@router.put(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[Depends(get_current_user)],
)
def update_service(
    service_id: int,
    session: SessionDep,
    title: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    short_description: Annotated[str | None, Form()] = None,
    price: Annotated[float | None, Form()] = None,
    technologies: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
):
    service = session.get(Service, service_id)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )

    if title is not None:
        service.title = title
    if description is not None:
        service.description = description
    if short_description is not None:
        service.short_description = short_description
    if price is not None:
        service.price = price
    if technologies is not None:
        service.technologies = json.dumps(_parse_technologies(technologies))
    if image is not None:
        if service.image:
            delete_file(service.image)
        service.image = save_upload(image, "services")

    session.add(service)
    session.commit()
    session.refresh(service)
    return service


@router.delete("/{service_id}", dependencies=[Depends(get_current_user)])
def delete_service(service_id: int, session: SessionDep) -> dict:
    service = session.get(Service, service_id)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    if service.image:
        delete_file(service.image)
    session.delete(service)
    session.commit()
    return {"success": True, "message": "Service deleted"}
