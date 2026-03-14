"""Exercise routes: fetch exercises, submit results."""
import json
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from db import get_webapp_db
from routers.auth_router import get_current_user

router = APIRouter()


@router.get("/week/{lop}/{tuan}")
async def get_week_exercises(lop: int, tuan: int):
    """Get all exercises for a grade/week."""
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, lop, tuan, section, sort_order, exercise_type,
               title_vi, title_en, instruction_vi, instruction_en,
               hint_vi, hint_en, config, images, yccd_ids
        FROM exercises
        WHERE lop = ? AND tuan = ? AND is_active = 1
        ORDER BY section, sort_order
    """, (lop, tuan))
    exercises = []
    for row in cur.fetchall():
        ex = dict(row)
        ex["config"] = json.loads(ex["config"]) if ex["config"] else {}
        ex["images"] = json.loads(ex["images"]) if ex["images"] else []
        exercises.append(ex)
    conn.close()
    return {"lop": lop, "tuan": tuan, "exercises": exercises}


@router.get("/{exercise_id}")
async def get_exercise(exercise_id: int):
    """Get a single exercise by ID."""
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Exercise not found")
    ex = dict(row)
    ex["config"] = json.loads(ex["config"]) if ex["config"] else {}
    ex["images"] = json.loads(ex["images"]) if ex["images"] else []
    return ex


class SubmitResult(BaseModel):
    exercise_id: int
    score: int
    total: int
    answers: dict = {}


@router.post("/submit")
async def submit_result(req: SubmitResult, authorization: str = Header(None)):
    """Student submits exercise result."""
    payload = get_current_user(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO results (user_id, exercise_id, score, total, answers) VALUES (?,?,?,?,?)",
        (payload["user_id"], req.exercise_id, req.score, req.total, json.dumps(req.answers))
    )
    conn.commit()
    result_id = cur.lastrowid
    conn.close()
    return {"id": result_id, "score": req.score, "total": req.total}


@router.get("/results/me")
async def my_results(authorization: str = Header(None)):
    """Get current student's results."""
    payload = get_current_user(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.exercise_id, r.score, r.total, r.completed_at,
               e.lop, e.tuan, e.title_vi, e.exercise_type
        FROM results r JOIN exercises e ON r.exercise_id = e.id
        WHERE r.user_id = ?
        ORDER BY r.completed_at DESC LIMIT 100
    """, (payload["user_id"],))
    results = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"results": results}


@router.get("/progress/{lop}")
async def get_progress(lop: int, authorization: str = Header(None)):
    """Get progress summary for a grade (which weeks completed)."""
    payload = get_current_user(authorization)
    conn = get_webapp_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.tuan,
               COUNT(DISTINCT e.id) as total_exercises,
               COUNT(DISTINCT r.exercise_id) as completed_exercises,
               COALESCE(SUM(r.score), 0) as total_score,
               COALESCE(SUM(r.total), 0) as total_possible
        FROM exercises e
        LEFT JOIN results r ON e.id = r.exercise_id AND r.user_id = ?
        WHERE e.lop = ? AND e.is_active = 1
        GROUP BY e.tuan
        ORDER BY e.tuan
    """, (payload["user_id"], lop))
    progress = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"lop": lop, "progress": progress}
