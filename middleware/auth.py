from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from core.admin import ADMIN_IDS

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

PUBLIC_PATHS = [
    "/",
    "/mcp",
    "/docs",
    "/openapi.json",
    "/api/v1/users/create",
    "/api/v1/users/login",
    "/api/v1/asha/verify_and_register_device",
    "/api/v1/asha/twi_transcribe"
]


async def verify_token_middleware(request: Request, call_next):
    if (request.method == "OPTIONS" or
        request.url.path.startswith("/mcp") or
        request.url.path.startswith("/sse") or
        request.url.path.startswith("/messages") or
        request.url.path in PUBLIC_PATHS): # noqa
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401, content={"detail": "Missing or invalid token"}
        )

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(
            token, str(JWT_SECRET_KEY), algorithms=[str(JWT_ALGORITHM)]
        )
        request.state.user = payload
    except JWTError:
        return JSONResponse(
            status_code=401, content={"detail": "Invalid or expired token"}
        )

    response = await call_next(request)
    return response


async def get_current_user(request: Request) -> dict:
    """Extract current user from request state"""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"  # noqa
        )
    return request.state.user


async def get_current_user_optional(request: Request) -> dict | None:
    """Returns user if authenticated, None if not"""
    if not hasattr(request.state, "user"):
        return None
    return request.state.user


async def admin_protected_route(request: Request):
    user = await get_current_user(request)
    if user.get("sub") not in ADMIN_IDS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",  # noqa
        )
    else:
        return user
