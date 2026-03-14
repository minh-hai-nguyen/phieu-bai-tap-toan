"""Authentication routes: login, register."""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from db import get_webapp_db
from auth import hash_password, verify_password, create_token, decode_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str
    lop: int = 1


def get_current_user(authorization: str = Header(None)):
    """Dependency: extract user from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


@router.post("/login")
async def login(req: LoginRequest):
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, display_name, role, lop, avatar FROM users WHERE username=?",
                (req.username,))
    user = cur.fetchone()
    conn.close()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")

    token = create_token(user["id"], user["username"], user["role"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
            "lop": user["lop"],
            "avatar": user["avatar"],
        }
    }


@router.post("/register")
async def register(req: RegisterRequest):
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (req.username,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")

    cur.execute(
        "INSERT INTO users (username, password_hash, display_name, role, lop) VALUES (?,?,?,?,?)",
        (req.username, hash_password(req.password), req.display_name, "student", req.lop)
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()

    token = create_token(user_id, req.username, "student")
    return {
        "token": token,
        "user": {
            "id": user_id,
            "username": req.username,
            "display_name": req.display_name,
            "role": "student",
            "lop": req.lop,
            "avatar": "default",
        }
    }


@router.get("/me")
async def me(authorization: str = Header(None)):
    payload = get_current_user(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, display_name, role, lop, avatar FROM users WHERE id=?",
                (payload["user_id"],))
    user = cur.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)
