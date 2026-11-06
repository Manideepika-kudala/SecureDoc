import secrets
import hmac

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class CSRFMiddleware(BaseHTTPMiddleware):
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    def __init__(self, app, secure=False):
        super().__init__(app)
        self.secure = secure

    async def dispatch(self, request, call_next):
        if request.method.upper() not in self.SAFE_METHODS:
            cookie_token = request.cookies.get("csrf_token")
            header_token = request.headers.get("X-CSRF-Token")

            if (
                not cookie_token
                or not header_token
                or not hmac.compare_digest(cookie_token, header_token)
            ):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing or invalid"}
                )

        response = await call_next(request)

        if (
            request.method.upper() in self.SAFE_METHODS
            and not request.cookies.get("csrf_token")
        ):
            response.set_cookie(
                key="csrf_token",
                value=secrets.token_urlsafe(32),
                httponly=False,
                secure=self.secure,
                samesite="lax",
                path="/",
                max_age=3600
            )

        return response
