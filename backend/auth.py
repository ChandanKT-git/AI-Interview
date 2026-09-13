"""Unified session-token auth: email/password (JWT-style).
Uses an opaque session_token stored in the user_sessions collection and an
httpOnly cookie. Avoids MongoDB _id exposure by using custom user_id (UUID)."""
import os
import uuid
import bcrypt
import httpx
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Request, Response, HTTPException, Depends

from db import db
from models import RegisterRequest, LoginRequest
router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_DAYS = 7
COOKIE_NAME = "session_token"



def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def public_user(user: dict) -> dict:
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", "candidate"),
        "picture": user.get("picture"),
        "auth_provider": user.get("auth_provider", "email"),
        "badges": user.get("badges", []),
        "created_at": user.get("created_at"),
    }


async def create_session(user_id: str) -> str:
    token = f"st_{uuid.uuid4().hex}{uuid.uuid4().hex}"
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
        "created_at": datetime.now(timezone.utc),
    })
    return token


def set_session_cookie(response: Response, token: str):
    response.set_cookie(
        key=COOKIE_NAME, value=token, httponly=True, secure=True,
        samesite="none", max_age=SESSION_DAYS * 24 * 3600, path="/",
    )


def _extract_token(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    return token


async def get_current_user(request: Request) -> dict:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    sess = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid session")
    expires_at = sess["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    user = await db.users.find_one({"user_id": sess["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_role(*roles):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker


@router.post("/register")
async def register(body: RegisterRequest, response: Response):
    email = body.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    role = body.role if body.role in ("candidate", "recruiter") else "candidate"
    user = {
        "user_id": f"user_{uuid.uuid4().hex[:12]}",
        "email": email,
        "name": body.name.strip() or email.split("@")[0],
        "password_hash": hash_password(body.password),
        "role": role,
        "picture": None,
        "auth_provider": "email",
        "badges": [],
        "created_at": datetime.now(timezone.utc),
    }
    await db.users.insert_one(user)
    token = await create_session(user["user_id"])
    set_session_cookie(response, token)
    return {"user": public_user(user), "token": token}


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not user.get("password_hash") or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = await create_session(user["user_id"])
    set_session_cookie(response, token)
    return {"user": public_user(user), "token": token}



@router.post("/logout")
async def logout(request: Request, response: Response):
    token = _extract_token(request)
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return public_user(user)


async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@interviewcoach.ai").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@12345")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": admin_email,
            "name": "Platform Admin",
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "picture": None,
            "auth_provider": "email",
            "badges": [],
            "created_at": datetime.now(timezone.utc),
        })
    elif not verify_password(admin_password, existing.get("password_hash") or ""):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
