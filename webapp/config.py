import os
import sys

# Root of SMART_ATTENDENCE_SYSTEM/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR  = os.path.join(BASE_DIR, "src")

# Inject src/ so ML pipeline imports work
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# ── ML pipeline data paths ──────────────────────────────
EMBEDDINGS_DIR    = os.path.join(BASE_DIR, "data", "embeddings")
GROUP_IMAGES_DIR  = os.path.join(BASE_DIR, "data", "group_images")
RAW_VIDEO_DIR     = os.path.join(BASE_DIR, "data", "raw_videos")
FRAMES_DIR        = os.path.join(BASE_DIR, "data", "extracted_frames")
FACES_DIR         = os.path.join(BASE_DIR, "data", "processed_faces")

# ── Web app paths ───────────────────────────────────────
WEBAPP_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(WEBAPP_DIR, "attendance.db")
UPLOADS_DIR = os.path.join(WEBAPP_DIR, "uploads")

# Ensure runtime dirs exist
for _d in [UPLOADS_DIR, GROUP_IMAGES_DIR, RAW_VIDEO_DIR]:
    os.makedirs(_d, exist_ok=True)

# ── ML tuning ───────────────────────────────────────────
FACE_SIZE              = 160
FPS_EXTRACT            = 2
CONFIDENCE_THRESHOLD   = 0.95
DISTANCE_THRESHOLD     = 0.6

# ── App constants ───────────────────────────────────────
SECRET_KEY          = "smart-attendance-deepak-2024"
DEMO_CLASSROOM_ID   = "demo-classroom-deepak-1"
DEMO_TEACHER_ID     = "teacher-deepak-001"
