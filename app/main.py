from pathlib import Path
import os
from starlette.middleware.sessions import SessionMiddleware

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import create_tables, get_db
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.document import Document
from app.services.authorization import get_current_active_user
from app.models.user import User
from app.services.authorization import get_current_admin_user
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.admin import router as admin_router

BASE_DIR = Path("app").resolve()

app = FastAPI(
    title="SecureDoc",
    description="Secure Document Management System",
    version="1.0.0"
)

secret_key = os.getenv("SECUREDOC_SECRET_KEY")

if not secret_key:
    raise RuntimeError("SECUREDOC_SECRET_KEY is not configured")

app.add_middleware(
    SessionMiddleware,
    secret_key=secret_key,
    session_cookie="securedoc_session",
    max_age=3600,
    same_site="lax",
    https_only=False
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def startup():
    create_tables()


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

