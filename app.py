"""Math Education Web App — FastAPI entry point."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from config import STATIC_DIR, TEMPLATES_DIR
from db import init_webapp_db
from routers import auth_router, curriculum_router, exercise_router, admin_router

from contextlib import asynccontextmanager

def ensure_default_users():
    """Create or update default admin and student users on every startup."""
    from db import get_webapp_db
    from auth import hash_password
    conn = get_webapp_db()
    cur = conn.cursor()
    # Admin user — always update hash to match current SECRET_KEY
    cur.execute("SELECT id FROM users WHERE username='admin'")
    if cur.fetchone():
        cur.execute("UPDATE users SET password_hash=? WHERE username='admin'",
                    (hash_password("admin123"),))
    else:
        cur.execute(
            "INSERT INTO users (username, password_hash, display_name, role) VALUES (?,?,?,?)",
            ("admin", hash_password("admin123"), "Quản trị viên", "admin"))
    # Demo student
    cur.execute("SELECT id FROM users WHERE username='hocsinh'")
    if cur.fetchone():
        cur.execute("UPDATE users SET password_hash=? WHERE username='hocsinh'",
                    (hash_password("123456"),))
    else:
        cur.execute(
            "INSERT INTO users (username, password_hash, display_name, role, lop) VALUES (?,?,?,?,?)",
            ("hocsinh", hash_password("123456"), "Học sinh Demo", "student", 1))
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app):
    init_webapp_db()
    ensure_default_users()
    yield

app = FastAPI(title="Toán Tiểu Học — Math Education", version="1.0", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(curriculum_router.router, prefix="/api/curriculum", tags=["curriculum"])
app.include_router(exercise_router.router, prefix="/api/exercises", tags=["exercises"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["admin"])


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(TEMPLATES_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    with open(os.path.join(TEMPLATES_DIR, "login.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    with open(os.path.join(TEMPLATES_DIR, "admin.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
async def health():
    """Health check + version to verify deployment."""
    from db import get_webapp_db
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM users")
    user_count = cur.fetchone()["cnt"]
    cur.execute("SELECT username, role FROM users")
    users = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"version": "v3", "users": users, "user_count": user_count}


@app.get("/api/fix-admin")
async def fix_admin():
    """One-time fix: reset admin password hash to match current SECRET_KEY."""
    ensure_default_users()
    return {"status": "ok", "message": "Admin and hocsinh passwords reset"}


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  Toán Tiểu Học — Math Education Web App")
    print("  http://localhost:8000")
    print("=" * 50)

    # Create default admin if needed
    from db import get_webapp_db
    from auth import hash_password
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, display_name, role) VALUES (?,?,?,?)",
            ("admin", hash_password("admin123"), "Quản trị viên", "admin")
        )
        conn.commit()
        print("  Default admin: admin / admin123")
    # Create demo student
    cur.execute("SELECT id FROM users WHERE username='hocsinh'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, display_name, role, lop) VALUES (?,?,?,?,?)",
            ("hocsinh", hash_password("123456"), "Học sinh Demo", "student", 1)
        )
        conn.commit()
        print("  Demo student: hocsinh / 123456")
    conn.close()

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
