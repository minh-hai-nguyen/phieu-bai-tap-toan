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

@asynccontextmanager
async def lifespan(app):
    init_webapp_db()
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
