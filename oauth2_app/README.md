# OAuth2 Auth Demo — FastAPI + SQLite

A minimal but complete OAuth2 **Password Flow** implementation with:
- JWT access tokens (30 min expiry) + refresh tokens (7 days)
- Token revocation (logout invalidates the token server-side)
- Refresh token rotation (each refresh issues a brand-new pair)
- bcrypt password hashing
- SQLite persistence (zero config)
- Minimal dark-themed frontend (no framework, plain JS)

---

## Project structure

```
oauth2_app/
├── main.py          ← FastAPI app & all routes
├── auth.py          ← JWT creation/verification, password hashing, user helpers
├── database.py      ← SQLite setup
├── requirements.txt
└── templates/
    └── index.html   ← Frontend (register / login / dashboard)
```

---

## Setup & Run

### 1. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open the app

| URL | Purpose |
|-----|---------|
| http://localhost:8000 | Frontend UI |
| http://localhost:8000/docs | Swagger / interactive API docs |
| http://localhost:8000/redoc | ReDoc API reference |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | ✗ | Register new user |
| POST | `/auth/token` | ✗ | Login → access + refresh tokens |
| POST | `/auth/refresh` | ✗ | Rotate refresh token → new pair |
| POST | `/auth/logout` | Bearer | Revoke access token |
| GET  | `/users/me` | Bearer | Current user profile |
| GET  | `/dashboard` | Bearer | Protected dashboard data |

### Example curl flow

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123"}'

# Login (OAuth2 form body)
curl -X POST http://localhost:8000/auth/token \
  -d "username=alice&password=secret123"

# Use access token
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer <access_token>"

# Refresh
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'

# Logout
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

---

## Security notes

- **Change `SECRET_KEY`** in `auth.py` before deploying — use a random 32+ character string.  
  Generate one with: `python -c "import secrets; print(secrets.token_hex(32))"`
- In production, serve over **HTTPS** so tokens are encrypted in transit.
- The `revoked_tokens` table grows over time — add a scheduled job to purge rows older than 7 days.
