"""Admin routes: CRUD exercises, manage users, dashboard stats."""
import json
import os
import uuid
import shutil
from fastapi import APIRouter, HTTPException, Header, Query, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from db import get_webapp_db
from routers.auth_router import get_current_user
from auth import hash_password
from config import IMAGES_DIR

router = APIRouter()


def require_admin(authorization: str = Header(None)):
    payload = get_current_user(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return payload


# ═══════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════

class ExerciseCreate(BaseModel):
    lop: int
    tuan: int
    section: str = "practice"
    sort_order: int = 0
    exercise_type: str
    title_vi: str
    title_en: Optional[str] = ""
    instruction_vi: str
    instruction_en: Optional[str] = ""
    hint_vi: Optional[str] = ""
    hint_en: Optional[str] = ""
    config: dict = {}
    images: list = []
    yccd_ids: str = ""


class ExerciseUpdate(BaseModel):
    lop: Optional[int] = None
    tuan: Optional[int] = None
    title_vi: Optional[str] = None
    title_en: Optional[str] = None
    instruction_vi: Optional[str] = None
    instruction_en: Optional[str] = None
    hint_vi: Optional[str] = None
    hint_en: Optional[str] = None
    config: Optional[dict] = None
    images: Optional[list] = None
    yccd_ids: Optional[str] = None
    sort_order: Optional[int] = None
    section: Optional[str] = None
    exercise_type: Optional[str] = None
    is_active: Optional[int] = None


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str
    role: str = "student"
    lop: int = 1


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    lop: Optional[int] = None
    password: Optional[str] = None


# ═══════════════════════════════════════════
# DASHBOARD / STATS
# ═══════════════════════════════════════════

@router.get("/stats")
async def get_stats(authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    total_students = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    total_admins = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM exercises WHERE is_active=1")
    total_exercises = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM results")
    total_submissions = cur.fetchone()[0]

    # Exercises per grade
    cur.execute("""
        SELECT lop, COUNT(*) as cnt FROM exercises WHERE is_active=1 GROUP BY lop ORDER BY lop
    """)
    exercises_by_grade = [dict(r) for r in cur.fetchall()]

    # Exercises per week (top 10 most populated)
    cur.execute("""
        SELECT lop, tuan, COUNT(*) as cnt FROM exercises WHERE is_active=1
        GROUP BY lop, tuan ORDER BY cnt DESC LIMIT 20
    """)
    exercises_by_week = [dict(r) for r in cur.fetchall()]

    # Recent submissions (last 20)
    cur.execute("""
        SELECT r.id, r.score, r.total, r.completed_at,
               u.username, u.display_name,
               e.lop, e.tuan, e.title_vi, e.exercise_type
        FROM results r
        JOIN users u ON r.user_id = u.id
        JOIN exercises e ON r.exercise_id = e.id
        ORDER BY r.completed_at DESC LIMIT 20
    """)
    recent_submissions = [dict(r) for r in cur.fetchall()]

    # Weeks with zero exercises per grade
    empty_weeks = {}
    for lop in range(1, 6):
        cur.execute("""
            SELECT COUNT(DISTINCT tuan) FROM exercises WHERE lop=? AND is_active=1
        """, (lop,))
        filled = cur.fetchone()[0]
        empty_weeks[str(lop)] = 35 - filled

    conn.close()
    return {
        "total_students": total_students,
        "total_admins": total_admins,
        "total_exercises": total_exercises,
        "total_submissions": total_submissions,
        "exercises_by_grade": exercises_by_grade,
        "exercises_by_week": exercises_by_week,
        "recent_submissions": recent_submissions,
        "empty_weeks_by_grade": empty_weeks,
    }


# ═══════════════════════════════════════════
# EXERCISE CRUD
# ═══════════════════════════════════════════

@router.get("/exercises")
async def list_exercises(
    authorization: str = Header(None),
    lop: Optional[int] = Query(None),
    tuan: Optional[int] = Query(None),
    exercise_type: Optional[str] = Query(None),
    is_active: Optional[int] = Query(1),
):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()

    query = """
        SELECT id, lop, tuan, section, sort_order, exercise_type,
               title_vi, title_en, instruction_vi, instruction_en,
               hint_vi, hint_en, config, images, yccd_ids,
               is_active, created_at, updated_at
        FROM exercises WHERE 1=1
    """
    params = []

    if lop is not None:
        query += " AND lop = ?"
        params.append(lop)
    if tuan is not None:
        query += " AND tuan = ?"
        params.append(tuan)
    if exercise_type:
        query += " AND exercise_type = ?"
        params.append(exercise_type)
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(is_active)

    query += " ORDER BY lop, tuan, section, sort_order"
    cur.execute(query, params)
    exercises = []
    for row in cur.fetchall():
        ex = dict(row)
        ex["config"] = json.loads(ex["config"]) if ex["config"] else {}
        ex["images"] = json.loads(ex["images"]) if ex["images"] else []
        exercises.append(ex)
    conn.close()
    return {"exercises": exercises, "total": len(exercises)}


@router.post("/exercises")
async def create_exercise(req: ExerciseCreate, authorization: str = Header(None)):
    admin = require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO exercises (lop, tuan, section, sort_order, exercise_type,
            title_vi, title_en, instruction_vi, instruction_en,
            hint_vi, hint_en, config, images, yccd_ids, created_by)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        req.lop, req.tuan, req.section, req.sort_order, req.exercise_type,
        req.title_vi, req.title_en, req.instruction_vi, req.instruction_en,
        req.hint_vi, req.hint_en, json.dumps(req.config), json.dumps(req.images),
        req.yccd_ids, admin["user_id"]
    ))
    conn.commit()
    eid = cur.lastrowid
    conn.close()
    return {"id": eid, "message": "Exercise created"}


@router.put("/exercises/{exercise_id}")
async def update_exercise(exercise_id: int, req: ExerciseUpdate, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()

    updates = []
    values = []
    for field, val in req.dict(exclude_unset=True).items():
        if val is not None:
            if field in ("config", "images"):
                val = json.dumps(val)
            updates.append(f"{field} = ?")
            values.append(val)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(exercise_id)
    cur.execute(f"UPDATE exercises SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Updated"}


@router.delete("/exercises/{exercise_id}")
async def delete_exercise(exercise_id: int, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("UPDATE exercises SET is_active = 0 WHERE id = ?", (exercise_id,))
    conn.commit()
    conn.close()
    return {"message": "Deleted (soft)"}


@router.post("/exercises/{exercise_id}/restore")
async def restore_exercise(exercise_id: int, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("UPDATE exercises SET is_active = 1 WHERE id = ?", (exercise_id,))
    conn.commit()
    conn.close()
    return {"message": "Restored"}


@router.delete("/exercises/{exercise_id}/permanent")
async def permanent_delete_exercise(exercise_id: int, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM results WHERE exercise_id = ?", (exercise_id,))
    cur.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
    conn.commit()
    conn.close()
    return {"message": "Permanently deleted"}


# ═══════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════

@router.get("/users")
async def list_users(authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.username, u.display_name, u.role, u.lop, u.avatar, u.created_at,
               COUNT(r.id) as total_submissions,
               COALESCE(SUM(r.score), 0) as total_score,
               COALESCE(SUM(r.total), 0) as total_possible
        FROM users u LEFT JOIN results r ON u.id = r.user_id
        GROUP BY u.id ORDER BY u.role DESC, u.display_name
    """)
    users = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"users": users}


@router.get("/students")
async def list_students(authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.username, u.display_name, u.lop, u.created_at,
               COUNT(r.id) as total_submissions,
               COALESCE(SUM(r.score),0) as total_score
        FROM users u LEFT JOIN results r ON u.id = r.user_id
        WHERE u.role = 'student'
        GROUP BY u.id ORDER BY u.display_name
    """)
    students = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"students": students}


@router.post("/users")
async def create_user(req: UserCreate, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()

    # Check unique username
    cur.execute("SELECT id FROM users WHERE username = ?", (req.username,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    cur.execute("""
        INSERT INTO users (username, password_hash, display_name, role, lop)
        VALUES (?,?,?,?,?)
    """, (req.username, hash_password(req.password), req.display_name, req.role, req.lop))
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return {"id": uid, "message": "User created"}


@router.put("/users/{user_id}")
async def update_user(user_id: int, req: UserUpdate, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()

    updates = []
    values = []
    data = req.dict(exclude_unset=True)

    if "password" in data and data["password"]:
        updates.append("password_hash = ?")
        values.append(hash_password(data["password"]))
        del data["password"]

    for field, val in data.items():
        if val is not None:
            updates.append(f"{field} = ?")
            values.append(val)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(user_id)
    cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "User updated"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, authorization: str = Header(None)):
    admin = require_admin(authorization)
    if admin["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM results WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "User deleted"}


# ═══════════════════════════════════════════
# RESULTS / HISTORY
# ═══════════════════════════════════════════

@router.get("/results")
async def list_results(
    authorization: str = Header(None),
    user_id: Optional[int] = Query(None),
    lop: Optional[int] = Query(None),
    limit: int = Query(50),
):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()

    query = """
        SELECT r.id, r.user_id, r.exercise_id, r.score, r.total, r.completed_at,
               u.username, u.display_name,
               e.lop, e.tuan, e.title_vi, e.exercise_type
        FROM results r
        JOIN users u ON r.user_id = u.id
        JOIN exercises e ON r.exercise_id = e.id
        WHERE 1=1
    """
    params = []
    if user_id:
        query += " AND r.user_id = ?"
        params.append(user_id)
    if lop:
        query += " AND e.lop = ?"
        params.append(lop)
    query += " ORDER BY r.completed_at DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    results = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"results": results}


@router.delete("/results/{result_id}")
async def delete_result(result_id: int, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM results WHERE id = ?", (result_id,))
    conn.commit()
    conn.close()
    return {"message": "Result deleted"}


# ═══════════════════════════════════════════
# EXERCISE TEMPLATES (Kho dạng bài tập)
# ═══════════════════════════════════════════

class TemplateCreate(BaseModel):
    name: str
    slug: str
    description: str = ""
    exercise_type: str
    instruction_template: str = ""
    default_config: dict = {}
    sample_config: dict = {}
    applicable_grades: list = [1, 2, 3, 4, 5]
    tags: list = []


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    exercise_type: Optional[str] = None
    instruction_template: Optional[str] = None
    default_config: Optional[dict] = None
    sample_config: Optional[dict] = None
    applicable_grades: Optional[list] = None
    tags: Optional[list] = None
    is_active: Optional[int] = None


@router.get("/templates")
async def list_templates(authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, slug, description, exercise_type,
               instruction_template, default_config, sample_config,
               applicable_grades, tags, is_active, created_at, updated_at
        FROM exercise_templates
        WHERE is_active = 1
        ORDER BY name
    """)
    templates = []
    for row in cur.fetchall():
        t = dict(row)
        t["default_config"] = json.loads(t["default_config"]) if t["default_config"] else {}
        t["sample_config"] = json.loads(t["sample_config"]) if t["sample_config"] else {}
        t["applicable_grades"] = json.loads(t["applicable_grades"]) if t["applicable_grades"] else []
        t["tags"] = json.loads(t["tags"]) if t["tags"] else []
        templates.append(t)
    conn.close()
    return {"templates": templates}


@router.get("/templates/{template_id}")
async def get_template(template_id: int, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exercise_templates WHERE id = ?", (template_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    t = dict(row)
    t["default_config"] = json.loads(t["default_config"]) if t["default_config"] else {}
    t["sample_config"] = json.loads(t["sample_config"]) if t["sample_config"] else {}
    t["applicable_grades"] = json.loads(t["applicable_grades"]) if t["applicable_grades"] else []
    t["tags"] = json.loads(t["tags"]) if t["tags"] else []
    return t


@router.post("/templates")
async def create_template(req: TemplateCreate, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM exercise_templates WHERE slug = ?", (req.slug,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Slug already exists")
    cur.execute("""
        INSERT INTO exercise_templates
            (name, slug, description, exercise_type, instruction_template,
             default_config, sample_config, applicable_grades, tags)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        req.name, req.slug, req.description, req.exercise_type,
        req.instruction_template,
        json.dumps(req.default_config), json.dumps(req.sample_config),
        json.dumps(req.applicable_grades), json.dumps(req.tags)
    ))
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return {"id": tid, "message": "Template created"}


@router.put("/templates/{template_id}")
async def update_template(template_id: int, req: TemplateUpdate, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()

    updates = []
    values = []
    for field, val in req.dict(exclude_unset=True).items():
        if val is not None:
            if field in ("default_config", "sample_config", "applicable_grades", "tags"):
                val = json.dumps(val)
            updates.append(f"{field} = ?")
            values.append(val)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(template_id)
    cur.execute(f"UPDATE exercise_templates SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Template updated"}


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, authorization: str = Header(None)):
    require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("UPDATE exercise_templates SET is_active = 0 WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    return {"message": "Template deleted (soft)"}


@router.post("/templates/{template_id}/create-exercise")
async def create_exercise_from_template(template_id: int, req: ExerciseCreate, authorization: str = Header(None)):
    """Create a new exercise pre-filled from a template."""
    admin = require_admin(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exercise_templates WHERE id = ? AND is_active = 1", (template_id,))
    tpl = cur.fetchone()
    if not tpl:
        conn.close()
        raise HTTPException(status_code=404, detail="Template not found")

    cur.execute("""
        INSERT INTO exercises (lop, tuan, section, sort_order, exercise_type,
            title_vi, title_en, instruction_vi, instruction_en,
            hint_vi, hint_en, config, images, yccd_ids, created_by)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        req.lop, req.tuan, req.section, req.sort_order, req.exercise_type,
        req.title_vi, req.title_en, req.instruction_vi, req.instruction_en,
        req.hint_vi, req.hint_en, json.dumps(req.config), json.dumps(req.images),
        req.yccd_ids, admin["user_id"]
    ))
    conn.commit()
    eid = cur.lastrowid
    conn.close()
    return {"id": eid, "message": "Exercise created from template"}


# ═══════════════════════════════════════════
# IMAGE UPLOAD
# ═══════════════════════════════════════════

ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Form("general"),
    authorization: str = Header(None),
):
    """Upload an image. folder e.g. 'lop1/week15'."""
    require_admin(authorization)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    # Sanitize folder
    folder = folder.replace("\\", "/").strip("/")
    folder = "/".join(p for p in folder.split("/") if p and ".." not in p)

    save_dir = os.path.join(IMAGES_DIR, folder)
    os.makedirs(save_dir, exist_ok=True)

    # Generate unique filename
    short_id = uuid.uuid4().hex[:8]
    safe_name = file.filename.replace(" ", "_")
    filename = f"{short_id}_{safe_name}"
    filepath = os.path.join(save_dir, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    # Return relative path usable in exercises
    rel_path = f"{folder}/{filename}"
    url = f"/static/img/exercises/{rel_path}"
    return {"path": rel_path, "url": url, "filename": filename, "size": len(content)}


@router.post("/upload-images")
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    folder: str = Form("general"),
    authorization: str = Header(None),
):
    """Upload multiple images at once."""
    require_admin(authorization)

    folder = folder.replace("\\", "/").strip("/")
    folder = "/".join(p for p in folder.split("/") if p and ".." not in p)
    save_dir = os.path.join(IMAGES_DIR, folder)
    os.makedirs(save_dir, exist_ok=True)

    results = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTS:
            results.append({"filename": file.filename, "error": f"Type {ext} not allowed"})
            continue
        content = await file.read()
        if len(content) > MAX_SIZE:
            results.append({"filename": file.filename, "error": "Too large"})
            continue

        short_id = uuid.uuid4().hex[:8]
        safe_name = file.filename.replace(" ", "_")
        filename = f"{short_id}_{safe_name}"
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "wb") as f:
            f.write(content)

        rel_path = f"{folder}/{filename}"
        results.append({"path": rel_path, "url": f"/static/img/exercises/{rel_path}", "filename": filename, "size": len(content)})

    return {"uploaded": results}


@router.get("/images")
async def list_images(
    folder: str = Query(""),
    authorization: str = Header(None),
):
    """List images in a folder."""
    require_admin(authorization)

    folder = folder.replace("\\", "/").strip("/")
    folder = "/".join(p for p in folder.split("/") if p and ".." not in p)
    scan_dir = os.path.join(IMAGES_DIR, folder) if folder else IMAGES_DIR

    if not os.path.isdir(scan_dir):
        return {"images": [], "folders": []}

    images = []
    folders = []
    for entry in sorted(os.listdir(scan_dir)):
        full = os.path.join(scan_dir, entry)
        rel = f"{folder}/{entry}" if folder else entry
        if os.path.isdir(full):
            folders.append({"name": entry, "path": rel})
        elif os.path.isfile(full):
            ext = os.path.splitext(entry)[1].lower()
            if ext in ALLOWED_EXTS:
                images.append({
                    "name": entry,
                    "path": rel,
                    "url": f"/static/img/exercises/{rel}",
                    "size": os.path.getsize(full)
                })

    return {"images": images, "folders": folders, "current_folder": folder}


@router.delete("/images/{path:path}")
async def delete_image(path: str, authorization: str = Header(None)):
    require_admin(authorization)
    filepath = os.path.join(IMAGES_DIR, path)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    os.remove(filepath)
    return {"message": "Image deleted"}
