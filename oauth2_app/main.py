from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, field_validator
import sqlite3

from database import init_db
from auth import (
    authenticate_user, create_user, create_access_token,
    create_refresh_token, decode_token, revoke_token, get_user,
)

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="OAuth2 Auth Demo", version="1.0.0")
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

@app.on_event("startup")
def startup():
    init_db()

# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def username_length(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: int
    created_at: str

# ── Dependency: get current user from Bearer token ────────────────────────────
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = get_user(username)
    if user is None or not user["is_active"]:
        raise credentials_exception
    return user

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.post("/auth/register", response_model=UserResponse, status_code=201,
          summary="Register a new user")
def register(body: RegisterRequest):
    if get_user(body.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    try:
        user = create_user(body.username, body.email, body.password)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user

@app.post("/auth/token", response_model=TokenResponse,
          summary="Login with username + password (OAuth2 Password Flow)")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(user["username"]),
        refresh_token=create_refresh_token(user["username"]),
    )

@app.post("/auth/refresh", response_model=TokenResponse,
          summary="Get a new access token using a refresh token")
def refresh(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    username = payload.get("sub")
    user = get_user(username)
    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    # Rotate: revoke old refresh token, issue fresh pair
    revoke_token(body.refresh_token)
    return TokenResponse(
        access_token=create_access_token(username),
        refresh_token=create_refresh_token(username),
    )

@app.post("/auth/logout", summary="Revoke the current access token")
def logout(token: str = Depends(oauth2_scheme)):
    revoke_token(token)
    return {"message": "Logged out successfully"}

# ── Protected routes ──────────────────────────────────────────────────────────
@app.get("/users/me", response_model=UserResponse,
         summary="Get current user profile (protected)")
def me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/dashboard", summary="A protected dashboard endpoint")
def dashboard(current_user: dict = Depends(get_current_user)):
    return {
        "message": f"Welcome, {current_user['username']}!",
        "email": current_user["email"],
        "member_since": current_user["created_at"],
    }

# ── Frontend routes ───────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
