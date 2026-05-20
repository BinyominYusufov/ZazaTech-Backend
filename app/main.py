"""ZazaTech API — application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.exceptions import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.files import UPLOAD_DIR
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.trailing_slash import TrailingSlashMiddleware
from app.routers import (
    auth,
    blogs,
    contacts,
    dashboard,
    health,
    projects,
    services,
    users,
)
from app.routers.ambassador_applications import (
    router as ambassador_applications_router,
)
from app.routers.admin_ambassador_applications import (
    router as admin_ambassador_applications_router,
)
from app.routers.ambassadors import router as ambassadors_router
from app.routers.admin_ambassadors import router as admin_ambassadors_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("zazatech")


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    create_db_and_tables()
    logger.info("Database initialized — application startup complete")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="ZazaTech API",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware. Starlette runs the LAST-added middleware FIRST (outermost),
# so CORS must be added last to wrap everything (incl. rate-limit 429s).
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)
app.add_middleware(TrailingSlashMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers.
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# StaticFiles needs the directory to exist at mount time.
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(services.router)
app.include_router(projects.router)
app.include_router(blogs.router)
app.include_router(contacts.router)
app.include_router(dashboard.router)
app.include_router(ambassador_applications_router)
app.include_router(admin_ambassador_applications_router)
app.include_router(ambassadors_router)
app.include_router(admin_ambassadors_router)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"service": "ZazaTech API", "status": "running"}
