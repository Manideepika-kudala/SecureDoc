from pathlib import Path
import os
from starlette.middleware.sessions import SessionMiddleware

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import create_tables
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router

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

