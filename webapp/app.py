"""
app.py — FastAPI backend for Smart Attendance System web app.

Run with:
    cd webapp
    uvicorn app:app --reload --port 8000
"""

import os
import csv
import io
import uuid
import shutil
from datetime import datetime
from typing import Optional

from fastapi import (
    FastAPI, HTTPException, Depends, UploadFile,
    File, Form, Header, Request,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from database import (
    get_db, init_db, hash_password, verify_password,
    create_session, get_user_by_token, delete_session,
    get_existing_students,
)

# ── Init DB ──────────────────────────────────────────────────────────────────
init_db()

# ── ML pipeline (optional — loads heavy models once at startup) ──────────────
ml_ready = False
try:
    from attendance_system.detect_faces import detect_faces as _ml_detect
    from attendance_system.generate_embeddings import get_embeddings as _ml_embed
    from attendance_system.match_faces import load_database as _ml_load_db, match_faces as _ml_match
    from attendance_system.draw_results import draw_results as _ml_draw
    from dataset_creation.extract_frames import extract_frames as _ml_frames
    from dataset_creation.detect_faces import detect_and_crop_faces as _ml_crop
    from dataset_creation.align_faces import align_faces as _ml_align
    from dataset_creation.build_database import build_database as _ml_build
    ml_ready = True
    print("[ML] ✓ Pipeline loaded")
except Exception as exc:
    print(f"[ML] ✗ Not available: {exc}")

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(title="Smart Attendance System", version="1.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"],
    allow_headers=["*"], allow_credentials=True,
)

WEBAPP_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static",  StaticFiles(directory=os.path.join(WEBAPP_DIR, "static")),  name="static")
app.mount("/uploads", StaticFiles(directory=config.UPLOADS_DIR), name="uploads")
templates = Jinja2Templates(directory=os.path.join(WEBAPP_DIR, "templates"))


# ═══════════════════════════════════════════════════════════════════════════════
#  Pydantic models
# ═══════════════════════════════════════════════════════════════════════════════

class RegisterReq(BaseModel):
    name: str
    email: str
    password: str
    role: str           # 'teacher' | 'student'

class LoginReq(BaseModel):
    email: str
    password: str

class CreateClassroomReq(BaseModel):
    name: str
    subject: str

class AddStudentReq(BaseModel):
    student_name: str

class JoinClassroomReq(BaseModel):
    join_code: str


# ═══════════════════════════════════════════════════════════════════════════════
#  Auth dependency
# ═══════════════════════════════════════════════════════════════════════════════

def current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    user = get_user_by_token(authorization.split(" ")[1])
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user

def teacher_only(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "teacher":
        raise HTTPException(403, "Teacher access required")
    return user


# ═══════════════════════════════════════════════════════════════════════════════
#  Frontend — serve the SPA
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def serve_spa(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ═══════════════════════════════════════════════════════════════════════════════
#  Auth routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/auth/register")
def register(body: RegisterReq):
    if body.role not in ("teacher", "student"):
        raise HTTPException(400, "role must be 'teacher' or 'student'")
    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email=?", (body.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Email already registered")
    uid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users (id, name, email, password_hash, role) VALUES (?,?,?,?,?)",
        (uid, body.name, body.email, hash_password(body.password), body.role),
    )
    conn.commit()
    conn.close()
    token = create_session(uid)
    return {"token": token, "user": {"id": uid, "name": body.name, "email": body.email, "role": body.role}}

@app.post("/api/auth/login")
def login(body: LoginReq):
    conn = get_db()
    row = conn.execute(
        "SELECT id, name, email, role, password_hash FROM users WHERE email=?", (body.email,)
    ).fetchone()
    conn.close()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_session(row["id"])
    return {"token": token, "user": {"id": row["id"], "name": row["name"],
                                      "email": row["email"], "role": row["role"]}}

@app.get("/api/auth/me")
def me(user: dict = Depends(current_user)):
    return user

@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        delete_session(authorization.split(" ")[1])
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
#  Demo (no auth) — guest view of the pre-seeded classroom
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/demo/classroom")
def demo_classroom():
    conn = get_db()
    cls = conn.execute(
        "SELECT c.*, u.name AS teacher_name FROM classrooms c"
        " JOIN users u ON u.id = c.teacher_id WHERE c.id=?",
        (config.DEMO_CLASSROOM_ID,),
    ).fetchone()
    if not cls:
        conn.close()
        raise HTTPException(404, "Demo classroom not found")

    students = conn.execute(
        "SELECT student_name, video_uploaded, dataset_built FROM enrollments WHERE classroom_id=?",
        (config.DEMO_CLASSROOM_ID,),
    ).fetchall()

    sessions = conn.execute(
        "SELECT id, date, total_present, total_absent FROM attendance_sessions"
        " WHERE classroom_id=? ORDER BY date DESC",
        (config.DEMO_CLASSROOM_ID,),
    ).fetchall()

    session_data = []
    for s in sessions:
        records = conn.execute(
            "SELECT student_name, status FROM attendance_records WHERE session_id=?",
            (s["id"],),
        ).fetchall()
        session_data.append({
            "id": s["id"], "date": s["date"],
            "total_present": s["total_present"],
            "total_absent":  s["total_absent"],
            "records": [{"name": r["student_name"], "status": r["status"]} for r in records],
        })

    conn.close()
    return {
        "classroom": {
            "id": cls["id"], "name": cls["name"], "subject": cls["subject"],
            "teacher_name": cls["teacher_name"], "join_code": cls["join_code"],
            "dataset_ready": bool(cls["dataset_ready"]),
        },
        "students":  [{"name": s["student_name"], "video_uploaded": bool(s["video_uploaded"]),
                        "dataset_built": bool(s["dataset_built"])} for s in students],
        "sessions":  session_data,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Classroom routes (authenticated)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/classrooms")
def list_classrooms(user: dict = Depends(current_user)):
    conn = get_db()
    if user["role"] == "teacher":
        rows = conn.execute(
            "SELECT c.*, u.name AS teacher_name,"
            " (SELECT COUNT(*) FROM enrollments WHERE classroom_id=c.id) AS student_count"
            " FROM classrooms c JOIN users u ON u.id=c.teacher_id WHERE c.teacher_id=?"
            " ORDER BY c.created_at DESC",
            (user["id"],),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT c.*, u.name AS teacher_name,"
            " (SELECT COUNT(*) FROM enrollments WHERE classroom_id=c.id) AS student_count"
            " FROM classrooms c JOIN users u ON u.id=c.teacher_id"
            " JOIN enrollments e ON e.classroom_id=c.id"
            " WHERE e.student_user_id=? ORDER BY c.created_at DESC",
            (user["id"],),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/classrooms")
def create_classroom(body: CreateClassroomReq, user: dict = Depends(teacher_only)):
    cid  = str(uuid.uuid4())
    code = body.name[:3].upper() + str(uuid.uuid4())[:4].upper()
    conn = get_db()
    conn.execute(
        "INSERT INTO classrooms (id, name, subject, teacher_id, join_code) VALUES (?,?,?,?,?)",
        (cid, body.name, body.subject, user["id"], code),
    )
    conn.commit()
    conn.close()
    return {"id": cid, "name": body.name, "subject": body.subject,
            "join_code": code, "dataset_ready": False}

@app.get("/api/classrooms/{cid}")
def get_classroom(cid: str, user: dict = Depends(current_user)):
    conn = get_db()
    cls = conn.execute(
        "SELECT c.*, u.name AS teacher_name FROM classrooms c"
        " JOIN users u ON u.id=c.teacher_id WHERE c.id=?", (cid,)
    ).fetchone()
    if not cls:
        conn.close()
        raise HTTPException(404, "Classroom not found")

    students = conn.execute(
        "SELECT student_name, student_user_id, video_uploaded, dataset_built"
        " FROM enrollments WHERE classroom_id=?", (cid,)
    ).fetchall()

    sessions = conn.execute(
        "SELECT id, date, total_present, total_absent, result_image_filename"
        " FROM attendance_sessions WHERE classroom_id=? ORDER BY date DESC", (cid,)
    ).fetchall()

    conn.close()
    return {
        "classroom": dict(cls),
        "students":  [dict(s) for s in students],
        "sessions":  [dict(s) for s in sessions],
        "ml_ready":  ml_ready,
    }

@app.post("/api/classrooms/{cid}/students")
def add_student(cid: str, body: AddStudentReq, user: dict = Depends(teacher_only)):
    conn = get_db()
    cls = conn.execute("SELECT id FROM classrooms WHERE id=? AND teacher_id=?",
                       (cid, user["id"])).fetchone()
    if not cls:
        conn.close()
        raise HTTPException(403, "Not your classroom")
    eid = str(uuid.uuid4())
    try:
        conn.execute(
            "INSERT INTO enrollments (id, classroom_id, student_name) VALUES (?,?,?)",
            (eid, cid, body.student_name),
        )
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(400, "Student already enrolled")
    conn.close()
    return {"ok": True, "student_name": body.student_name}

@app.delete("/api/classrooms/{cid}/students/{name}")
def remove_student(cid: str, name: str, user: dict = Depends(teacher_only)):
    conn = get_db()
    conn.execute(
        "DELETE FROM enrollments WHERE classroom_id=? AND student_name=?", (cid, name)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

def _do_join(body: JoinClassroomReq, user: dict):
    conn = get_db()
    cls = conn.execute("SELECT id FROM classrooms WHERE join_code=?",
                       (body.join_code,)).fetchone()
    if not cls:
        conn.close()
        raise HTTPException(404, "Invalid join code")
    cid = cls["id"]
    existing = conn.execute(
        "SELECT id FROM enrollments WHERE classroom_id=? AND student_user_id=?",
        (cid, user["id"]),
    ).fetchone()
    if existing:
        conn.close()
        return {"ok": True, "classroom_id": cid}
    by_name = conn.execute(
        "SELECT id FROM enrollments WHERE classroom_id=? AND student_name=? AND student_user_id IS NULL",
        (cid, user["name"]),
    ).fetchone()
    if by_name:
        conn.execute("UPDATE enrollments SET student_user_id=? WHERE id=?",
                     (user["id"], by_name["id"]))
    else:
        conn.execute(
            "INSERT INTO enrollments (id, classroom_id, student_name, student_user_id) VALUES (?,?,?,?)",
            (str(uuid.uuid4()), cid, user["name"], user["id"]),
        )
    conn.commit()
    conn.close()
    return {"ok": True, "classroom_id": cid}

@app.post("/api/classrooms/join")
def join_classroom_by_code(body: JoinClassroomReq, user: dict = Depends(current_user)):
    return _do_join(body, user)

@app.post("/api/classrooms/{cid}/join")
def join_classroom(cid: str, body: JoinClassroomReq, user: dict = Depends(current_user)):
    return _do_join(body, user)


# ═══════════════════════════════════════════════════════════════════════════════
#  Attendance — take attendance via group photo upload
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/classrooms/{cid}/attendance")
async def take_attendance(
    cid: str,
    photo: UploadFile = File(...),
    user: dict = Depends(teacher_only),
):
    conn = get_db()
    cls = conn.execute(
        "SELECT id, dataset_ready FROM classrooms WHERE id=? AND teacher_id=?",
        (cid, user["id"]),
    ).fetchone()
    if not cls:
        conn.close()
        raise HTTPException(403, "Not your classroom")

    # Save uploaded image
    ext      = os.path.splitext(photo.filename)[-1] or ".jpg"
    img_name = f"{uuid.uuid4()}{ext}"
    img_path = os.path.join(config.UPLOADS_DIR, img_name)
    with open(img_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)

    result_img_name = None
    present_names   = []
    error_msg       = None

    # Run ML pipeline if available
    if ml_ready and bool(cls["dataset_ready"]):
        try:
            import cv2, shutil as _sh
            # Copy to group_images dir (pipeline expects it there)
            gimg_path = os.path.join(config.GROUP_IMAGES_DIR, img_name)
            _sh.copy(img_path, gimg_path)

            faces, boxes, orig_img  = _ml_detect(gimg_path)
            if faces:
                embeddings  = _ml_embed(faces)
                database    = _ml_load_db(config.EMBEDDINGS_DIR)
                names       = _ml_match(embeddings, database, config.DISTANCE_THRESHOLD)
                result_img  = _ml_draw(orig_img, boxes, names)
                present_names = [n for n in names if n != "Unknown"]

                result_img_name = f"result_{img_name}"
                result_path     = os.path.join(config.UPLOADS_DIR, result_img_name)
                cv2.imwrite(result_path, result_img)
            else:
                error_msg = "No faces detected in the photo."
        except Exception as exc:
            error_msg = f"ML error: {str(exc)}"
    else:
        error_msg = "ML pipeline not ready. Using demo mode — marking random students present."
        # Demo fallback: mark random students as present
        all_students = conn.execute(
            "SELECT student_name FROM enrollments WHERE classroom_id=?", (cid,)
        ).fetchall()
        import random
        names_list    = [r["student_name"] for r in all_students]
        present_names = random.sample(names_list, k=max(1, int(len(names_list) * 0.8)))

    # Save session + records to DB
    today      = datetime.now().strftime("%Y-%m-%d")
    session_id = str(uuid.uuid4())

    all_students = conn.execute(
        "SELECT student_name FROM enrollments WHERE classroom_id=?", (cid,)
    ).fetchall()
    all_names = [r["student_name"] for r in all_students]
    absent    = [n for n in all_names if n not in present_names]

    conn.execute(
        "INSERT INTO attendance_sessions"
        " (id, classroom_id, date, total_present, total_absent, image_filename, result_image_filename)"
        " VALUES (?,?,?,?,?,?,?)",
        (session_id, cid, today, len(present_names), len(absent), img_name, result_img_name),
    )
    for name in present_names:
        conn.execute(
            "INSERT INTO attendance_records (id, session_id, student_name, status)"
            " VALUES (?,?,?,?)",
            (str(uuid.uuid4()), session_id, name, "present"),
        )
    for name in absent:
        conn.execute(
            "INSERT INTO attendance_records (id, session_id, student_name, status)"
            " VALUES (?,?,?,?)",
            (str(uuid.uuid4()), session_id, name, "absent"),
        )
    conn.commit()
    conn.close()

    return {
        "session_id":        session_id,
        "date":              today,
        "present":           present_names,
        "absent":            absent,
        "total_present":     len(present_names),
        "total_absent":      len(absent),
        "result_image_url":  f"/uploads/{result_img_name}" if result_img_name else None,
        "error":             error_msg,
    }


@app.get("/api/classrooms/{cid}/attendance")
def get_attendance(cid: str, user: dict = Depends(current_user)):
    conn = get_db()
    sessions = conn.execute(
        "SELECT id, date, total_present, total_absent, result_image_filename"
        " FROM attendance_sessions WHERE classroom_id=? ORDER BY date DESC",
        (cid,),
    ).fetchall()

    result = []
    for s in sessions:
        records = conn.execute(
            "SELECT student_name, status FROM attendance_records WHERE session_id=?",
            (s["id"],),
        ).fetchall()
        result.append({
            "id":              s["id"],
            "date":            s["date"],
            "total_present":   s["total_present"],
            "total_absent":    s["total_absent"],
            "result_image_url": f"/uploads/{s['result_image_filename']}"
                                 if s["result_image_filename"] else None,
            "records": [{"name": r["student_name"], "status": r["status"]} for r in records],
        })
    conn.close()
    return result


@app.get("/api/classrooms/{cid}/attendance/export")
def export_csv(cid: str, user: dict = Depends(current_user)):
    """Download attendance as a CSV file (date × student grid)."""
    conn = get_db()
    cls = conn.execute("SELECT name FROM classrooms WHERE id=?", (cid,)).fetchone()
    if not cls:
        conn.close()
        raise HTTPException(404, "Classroom not found")

    students = [r["student_name"] for r in conn.execute(
        "SELECT student_name FROM enrollments WHERE classroom_id=? ORDER BY student_name",
        (cid,),
    ).fetchall()]

    sessions = conn.execute(
        "SELECT id, date FROM attendance_sessions WHERE classroom_id=? ORDER BY date",
        (cid,),
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student"] + [s["date"] for s in sessions] + ["Total Present", "Total Absent"])

    for student in students:
        row   = [student]
        total_present = 0
        total_absent  = 0
        for s in sessions:
            rec = conn.execute(
                "SELECT status FROM attendance_records WHERE session_id=? AND student_name=?",
                (s["id"], student),
            ).fetchone()
            status = rec["status"] if rec else "absent"
            row.append("P" if status == "present" else "A")
            if status == "present":
                total_present += 1
            else:
                total_absent += 1
        row += [total_present, total_absent]
        writer.writerow(row)

    conn.close()
    output.seek(0)
    filename = f"attendance_{cls['name'].replace(' ', '_')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Video upload — student uploads face video for dataset creation
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/classrooms/{cid}/students/{student_name}/video")
async def upload_video(
    cid: str,
    student_name: str,
    video: UploadFile = File(...),
    user: dict = Depends(teacher_only),
):
    conn = get_db()
    cls = conn.execute(
        "SELECT id FROM classrooms WHERE id=? AND teacher_id=?", (cid, user["id"])
    ).fetchone()
    if not cls:
        conn.close()
        raise HTTPException(403, "Not your classroom")

    # Save video
    student_video_dir = os.path.join(config.RAW_VIDEO_DIR, student_name)
    os.makedirs(student_video_dir, exist_ok=True)
    video_path = os.path.join(student_video_dir, "video.mp4")
    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    conn.execute(
        "UPDATE enrollments SET video_uploaded=1 WHERE classroom_id=? AND student_name=?",
        (cid, student_name),
    )
    conn.commit()

    # Run dataset creation pipeline if ML available
    if ml_ready:
        try:
            frame_out = os.path.join(config.FRAMES_DIR, student_name)
            face_out  = os.path.join(config.FACES_DIR,  student_name)
            os.makedirs(frame_out, exist_ok=True)
            os.makedirs(face_out,  exist_ok=True)

            _ml_frames(video_path, frame_out)
            _ml_crop(frame_out, face_out)
            _ml_align(face_out, face_out)
            _ml_build(config.FACES_DIR, config.EMBEDDINGS_DIR)

            conn.execute(
                "UPDATE enrollments SET dataset_built=1 WHERE classroom_id=? AND student_name=?",
                (cid, student_name),
            )
            conn.execute(
                "UPDATE classrooms SET dataset_ready=1 WHERE id=?", (cid,)
            )
            conn.commit()
            conn.close()
            return {"ok": True, "message": f"Dataset built for {student_name}"}
        except Exception as exc:
            conn.close()
            raise HTTPException(500, f"Pipeline error: {str(exc)}")

    conn.close()
    return {"ok": True, "message": "Video saved. ML pipeline not available — run manually."}


# ═══════════════════════════════════════════════════════════════════════════════
#  Health check
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return {"status": "ok", "ml_ready": ml_ready}
