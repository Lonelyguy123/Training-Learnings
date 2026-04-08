import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from database import get_db

# ── Config ──────────────────────────────────────────────────────────────────
SECRET_KEY = "9d17c199e4b74abc42cd61e00ad30bd0355bee9b3c479f838c9f36022749ecc9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Password helpers ─────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ── JWT helpers ───────────────────────────────────────────────────────────────
def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    payload = data.copy()
    payload.update({
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),        # unique token ID (for revocation)
        "type": token_type,
    })
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(username: str) -> str:
    return _create_token(
        {"sub": username},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
    )

def create_refresh_token(username: str) -> str:
    return _create_token(
        {"sub": username},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
    )

def decode_token(token: str) -> Optional[dict]:
    """Returns payload dict or None if invalid/expired/revoked."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    # Check revocation list
    jti = payload.get("jti")
    if jti:
        conn = get_db()
        row = conn.execute(
            "SELECT 1 FROM revoked_tokens WHERE jti = ?", (jti,)
        ).fetchone()
        conn.close()
        if row:
            return None

    return payload

def revoke_token(token: str):
    """Add a token's jti to the revocation list (logout)."""
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
            options={"verify_exp": False}   # allow revoking expired tokens too
        )
        jti = payload.get("jti")
        if jti:
            conn = get_db()
            conn.execute(
                "INSERT OR IGNORE INTO revoked_tokens (jti) VALUES (?)", (jti,)
            )
            conn.commit()
            conn.close()
    except JWTError:
        pass

# ── User DB helpers ───────────────────────────────────────────────────────────
def get_user(username: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(username: str, email: str, password: str) -> dict:
    conn = get_db()
    conn.execute(
        "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
        (username, email, hash_password(password)),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(row)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user
