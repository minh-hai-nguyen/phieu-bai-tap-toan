"""Curriculum routes: read from yccd.db (read-only)."""
from fastapi import APIRouter, HTTPException
from db import get_yccd_db

router = APIRouter()


@router.get("/weeks/{lop}")
async def get_weeks(lop: int):
    """Get all weeks for a grade with lesson names and chu_de."""
    if lop < 1 or lop > 5:
        raise HTTPException(status_code=400, detail="Lớp phải từ 1 đến 5")

    conn = get_yccd_db()
    cur = conn.cursor()

    # Get week → lessons mapping
    cur.execute("""
        SELECT tuan, chu_de, GROUP_CONCAT(DISTINCT ten_bai) as bai_hoc
        FROM phan_phoi
        WHERE lop = ?
        GROUP BY tuan
        ORDER BY tuan
    """, (lop,))

    weeks = []
    for row in cur.fetchall():
        weeks.append({
            "tuan": row["tuan"],
            "chu_de": row["chu_de"],
            "bai_hoc": row["bai_hoc"],
        })

    conn.close()
    return {"lop": lop, "weeks": weeks}


@router.get("/chu-de/{lop}")
async def get_chu_de(lop: int):
    """Get all chu_de (topics) for a grade."""
    conn = get_yccd_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, thu_tu, ten, tiet_bat_dau, tiet_ket_thuc, so_tiet,
               tuan_bat_dau, tuan_ket_thuc
        FROM chu_de WHERE lop = ? ORDER BY thu_tu
    """, (lop,))
    topics = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"lop": lop, "chu_de": topics}


@router.get("/yccd/{lop}")
async def get_yccd(lop: int):
    """Get all YCCĐ (curriculum requirements) for a grade."""
    conn = get_yccd_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, mach_kien_thuc, chu_de_lon, chu_de_nho, noi_dung,
               tuan_hoc_bat_dau, tuan_hoc_ket_thuc, chinh_thuc
        FROM yccd WHERE lop = ? ORDER BY id
    """, (lop,))
    reqs = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"lop": lop, "yccd": reqs}


@router.get("/yccd-by-week/{lop}/{tuan}")
async def get_yccd_by_week(lop: int, tuan: int):
    """Get YCCĐ active during a specific week."""
    conn = get_yccd_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, mach_kien_thuc, noi_dung, tuan_hoc_bat_dau, tuan_hoc_ket_thuc
        FROM yccd
        WHERE lop = ? AND tuan_hoc_bat_dau <= ? AND tuan_hoc_ket_thuc >= ?
        ORDER BY id
    """, (lop, tuan, tuan))
    reqs = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"lop": lop, "tuan": tuan, "yccd": reqs}
