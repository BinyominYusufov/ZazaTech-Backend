"""Import every table model so they register on SQLModel.metadata.

`create_db_and_tables()` in app/core/database.py imports this package, so
every class listed here gets a CREATE TABLE.
"""

from app.models.blog import Blog, BlogCreate, BlogResponse, BlogUpdate
from app.models.contact import (
    Contact,
    ContactCreate,
    ContactResponse,
    ContactUpdate,
)
from app.models.project import (
    Project,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.models.service import (
    Service,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from app.models.user import (
    User,
    UserCreate,
    UserRegister,
    UserResponse,
    UserUpdate,
)

__all__ = [
    "Blog",
    "BlogCreate",
    "BlogResponse",
    "BlogUpdate",
    "Contact",
    "ContactCreate",
    "ContactResponse",
    "ContactUpdate",
    "Project",
    "ProjectCreate",
    "ProjectResponse",
    "ProjectUpdate",
    "Service",
    "ServiceCreate",
    "ServiceResponse",
    "ServiceUpdate",
    "User",
    "UserCreate",
    "UserRegister",
    "UserResponse",
    "UserUpdate",
]
