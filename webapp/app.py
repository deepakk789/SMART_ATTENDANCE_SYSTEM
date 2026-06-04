"""
app.py — Smart Attendance System  |  Recruiter Demo
Run: uvicorn app:app --port 8000
"""
import os, sys, uuid, io, csv, shutil, random, pickle, sqlite3
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# ── Paths ─────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR       = os.path.join(BASE_DIR, "src")
EMBEDDINGS_DIR= os.path.join(BASE_DIR, "data", "embeddings")
WEBAPP_DIR    = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR   = os.path.join(WEBAPP_DIR, "uploads")
DB_PATH       = os.path.join(WEBAPP_DIR, "demo.db")
GROUP_DIR     = os.path.join(BASE_DIR, "data", "group_images")

for d in [UPLOADS_DIR, GROUP_DIR]:
    os.makedirs(d, exist_ok=True)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# ── ML pipeline (optional) ────────────────────────────────────────
ml_ready = False
_detect = _embed = _load_db = _match = _draw = None
try:
    from attendance_system.detect_faces    import detect_faces
    from attendance_system.generate_embeddings import get_embeddings
    from attendance_system.match_faces     import load_database, match_faces
    from attendance_system.draw_results    import draw_results
    _detect, _embed, _load_db, _match, _draw = detect_faces, get_embeddings, load_database, match_faces, draw_results
    ml_ready = True
    print("[ML] Pipeline loaded OK")
except Exception as e:
    print("[ML] Not available:", e)

# ── Database ──────────────────────────────────────────────────────
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            date TEXT,
            image_filename TEXT,
            result_image_filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            student_name TEXT,
            status TEXT
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ── Helper: read students from embeddings ─────────────────────────
def get_all_students() -> list:
    try:
        lpath = os.path.join(EMBEDDINGS_DIR, "labels.pkl")
        if os.path.exists(lpath):
            with open(lpath, "rb") as f:
                return sorted(pickle.load(f))
        epath = os.path.join(EMBEDDINGS_DIR, "embeddings.pkl")
        if os.path.exists(epath):
            with open(epath, "rb") as f:
                return sorted(pickle.load(f).keys())
    except Exception as e:
        print("[DB] Could not read embeddings:", e)
    return ["Arjun Sharma", "Deepak Singh", "Kavya Reddy",
            "Priya Patel", "Rahul Verma", "Rohan Mehta", "Sneha Gupta"]

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(title="Smart Attendance Demo")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/static",  StaticFiles(directory=os.path.join(WEBAPP_DIR, "static")),  name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
templates = Jinja2Templates(directory=os.path.join(WEBAPP_DIR, "templates"))

# ── Routes ────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/api/students")
def students():
    return {"students": get_all_students(), "ml_ready": ml_ready}

@app.post("/api/mark-attendance")
async def mark_attendance(photo: UploadFile = File(...)):
    all_students = get_all_students()

    # Save uploaded photo
    ext      = os.path.splitext(photo.filename or "photo.jpg")[-1] or ".jpg"
    img_name = f"{uuid.uuid4()}{ext}"
    img_path = os.path.join(UPLOADS_DIR, img_name)
    with open(img_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)

    present      = []
    result_name  = None
    note         = None

    if ml_ready:
        try:
            import cv2
            gpath = os.path.join(GROUP_DIR, img_name)
            shutil.copy(img_path, gpath)

            faces, boxes, orig = _detect(gpath)
            if faces:
                embs     = _embed(faces)
                database = _load_db(EMBEDDINGS_DIR)
                names    = _match(embs, database)
                present  = [n for n in names if n != "Unknown"]
                result   = _draw(orig, boxes, names)

                result_name = f"result_{img_name}"
                cv2.imwrite(os.path.join(UPLOADS_DIR, result_name), result)
            else:
                note = "No faces detected in the photo."
        except Exception as e:
            note = f"ML error: {e}. Showing demo result."
            present = random.sample(all_students, k=max(1, int(len(all_students) * 0.8)))
    else:
        note    = "ML pipeline not set up — showing a demo result."
        present = random.sample(all_students, k=max(1, int(len(all_students) * 0.8)))

    absent = [s for s in all_students if s not in present]

    # Save session
    sid  = str(uuid.uuid4())
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    c = db()
    c.execute("INSERT INTO sessions (id,date,image_filename,result_image_filename) VALUES (?,?,?,?)",
              (sid, today, img_name, result_name))
    for s in present:
        c.execute("INSERT INTO records (id,session_id,student_name,status) VALUES (?,?,?,?)",
                  (str(uuid.uuid4()), sid, s, "present"))
    for s in absent:
        c.execute("INSERT INTO records (id,session_id,student_name,status) VALUES (?,?,?,?)",
                  (str(uuid.uuid4()), sid, s, "absent"))
    c.commit()
    c.close()

    return {
        "session_id":     sid,
        "date":           today,
        "present":        present,
        "absent":         absent,
        "total_present":  len(present),
        "total_absent":   len(absent),
        "total_students": len(all_students),
        "result_image":   f"/uploads/{result_name}" if result_name else None,
        "note":           note,
    }

@app.get("/api/history")
def history():
    c = db()
    sessions = c.execute(
        "SELECT id, date, result_image_filename FROM sessions ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    result = []
    for s in sessions:
        recs = c.execute(
            "SELECT student_name, status FROM records WHERE session_id=?", (s["id"],)
        ).fetchall()
        result.append({
            "id":           s["id"],
            "date":         s["date"],
            "result_image": f"/uploads/{s['result_image_filename']}" if s["result_image_filename"] else None,
            "records":      [{"name": r["student_name"], "status": r["status"]} for r in recs],
        })
    c.close()
    return result

@app.get("/api/history/export")
def export_csv():
    c = db()
    sessions = c.execute("SELECT id, date FROM sessions ORDER BY created_at").fetchall()
    students = get_all_students()

    out = io.StringIO()
    w   = csv.writer(out)
    w.writerow(["Student"] + [s["date"] for s in sessions] + ["Total Present", "Total", "%"])
    for student in students:
        row = [student]
        tp  = 0
        for s in sessions:
            rec = c.execute(
                "SELECT status FROM records WHERE session_id=? AND student_name=?",
                (s["id"], student)
            ).fetchone()
            status = rec["status"] if rec else "absent"
            row.append("P" if status == "present" else "A")
            if status == "present":
                tp += 1
        total = len(sessions)
        pct   = round(tp / total * 100, 1) if total else 0
        row  += [tp, total, f"{pct}%"]
        w.writerow(row)
    c.close()
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_report.csv"})

@app.get("/api/health")
def health():
    return {"status": "ok", "ml_ready": ml_ready,
            "students": len(get_all_students())}
