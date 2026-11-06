from pathlib import Path
from contextlib import asynccontextmanager
import os
import logging
from starlette.middleware.sessions import SessionMiddleware
from app.csrf import CSRFMiddleware

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import create_tables, get_db
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from app.models.document import Document
from app.services.authorization import get_current_active_user
from app.models.user import User
from app.services.authorization import get_current_admin_user
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.admin import router as admin_router

BASE_DIR = Path("app").resolve()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


logger = logging.getLogger("securedoc")


app = FastAPI(
    lifespan=lifespan,
    title="SecureDoc",
    description="Secure Document Management System",
    version="1.0.0"
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": ".".join(str(part) for part in error.get("loc", ())),
            "message": error.get("msg", "Invalid input"),
            "type": error.get("type", "validation_error")
        }
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled application error on %s %s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


app.add_middleware(CSRFMiddleware, secure=os.getenv("SECUREDOC_HTTPS_ONLY", "false").lower() in ("true", "1", "yes"))

secret_key = os.getenv("SECUREDOC_SECRET_KEY")

if not secret_key:
    raise RuntimeError("SECUREDOC_SECRET_KEY is not configured")

app.add_middleware(
    SessionMiddleware,
    secret_key=secret_key,
    session_cookie="securedoc_session",
    max_age=3600,
    same_site="lax",
    https_only=os.getenv("SECUREDOC_HTTPS_ONLY", "false").lower() in ("true", "1", "yes")
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(admin_router)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )



@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={}
    )

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )

@app.get("/dashboard")
def dashboard(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"username": request.session.get("username", "User")}
    )



@app.get("/share/{document_id}")
def share_page(
    request: Request,
    document_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.owner_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the document owner can manage sharing"
        )

    return templates.TemplateResponse(
        request=request,
        name="share.html",
        context={
            "document_id": document.id,
            "document_name": document.original_filename
        }
    )

@app.get("/admin/dashboard")
def admin_dashboard(
    request: Request,
    admin: User = Depends(get_current_admin_user)
):
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={"username": admin.username}
    )









