# Smart Attendance System

An automated classroom attendance system built on a two-phase deep learning pipeline. The system uses MTCNN for face detection and FaceNet for generating 512-dimensional face embeddings, achieving 95%+ recognition accuracy on high-quality, clear images.

---

## Overview

Traditional attendance systems are slow, error-prone, and require manual intervention. This project replaces that process with a fully automated pipeline: a student is enrolled once by recording a short video, and from that point forward their attendance is marked automatically from a single group classroom photograph.

The system is split into two self-contained phases:

- **Phase 1 — Enrolment:** Build a face embedding database from per-student video recordings.
- **Phase 2 — Recognition:** Process a group classroom image, match detected faces against the database, and log attendance to a CSV file.

---

## Pipeline Architecture

### Phase 1: Enrolment

```
Video Clips  ->  Frame Extraction (2 fps)  ->  Face Detection (MTCNN)
          ->  Face Alignment (160x160)  ->  FaceNet Embedding (512-D)
          ->  Embedding Database (.pkl)
```

1. A short 5-10 second video is recorded per student.
2. Frames are extracted at 2 FPS to avoid redundant data.
3. MTCNN detects and crops each face from every frame.
4. Cropped faces are aligned and resized to 160x160 pixels.
5. FaceNet generates a 512-dimensional embedding vector per face.
6. All embeddings are averaged and stored in a `.pkl` database keyed by student name.

### Phase 2: Recognition

```
Group Photo  ->  Face Detection (MTCNN)  ->  Face Alignment (160x160)
           ->  FaceNet Embedding (512-D)  ->  Nearest-Neighbour Matching (Euclidean)
           ->  CSV Attendance Log
```

1. A single group classroom photograph is provided as input.
2. MTCNN detects all faces in the image.
3. Each face is aligned and resized to 160x160 pixels.
4. FaceNet generates a 512-D embedding for each detected face.
5. Euclidean distance is computed between each face and every entry in the database.
6. If the nearest distance is within the threshold (<=0.6), the face is assigned the matched identity; otherwise it is labelled Unknown.
7. Duplicate detections are removed, and final attendance is written to a CSV file with a timestamp.
8. Bounding boxes and identity labels are drawn on the output image.

---

## Performance

| Condition                         | Accuracy  |
|-----------------------------------|-----------|
| High-quality, well-lit images     | 95%+      |
| Standard classroom lighting       | 85-90%    |
| Threshold (Euclidean distance)    | <= 0.6    |
| Embedding dimensions              | 512-D     |
| Frame extraction rate             | 2 FPS     |
| Face alignment resolution         | 160x160px |

---

## Project Structure

> **Note:** Large binary files (model weights, embeddings, raw data, attendance records, logs) are excluded from version control via `.gitignore`. Only source code and configuration are tracked.

```
SMART_ATTENDENCE_SYSTEM/
|
|-- src/
|   |-- main.py                        # Orchestrates Phase 1 and Phase 2
|   |-- dataset_creation/
|   |   |-- __init__.py
|   |   |-- extract_frames.py          # Video to frames at 2 FPS
|   |   |-- detect_faces.py            # MTCNN face detection and crop
|   |   |-- align_faces.py             # Face alignment and resize
|   |   |-- generate_embeddings.py     # FaceNet 512-D embedding generation
|   |   |-- build_database.py          # Builds and saves the .pkl database
|   |
|   |-- attendance_system/
|   |   |-- __init__.py
|   |   |-- detect_faces.py            # MTCNN detection on group photo
|   |   |-- generate_embeddings.py     # Embedding per detected face
|   |   |-- match_faces.py             # Euclidean nearest-neighbour matching
|   |   |-- mark_attendance.py         # Writes attendance CSV with timestamp
|   |   |-- draw_results.py            # Annotates output image with results
|   |
|   |-- utils/                         # Shared utility helpers
|
|-- notebooks/
|   |-- testing_pipeline.ipynb         # End-to-end pipeline testing
|   |-- visualization.ipynb            # Embedding and result visualisation
|
|-- config/
|   |-- config.yaml                    # Thresholds, paths, and pipeline settings
|
|-- paper/
|   |-- figures/                       # Architecture diagrams and result figures
|
|-- requirements.txt                   # Python dependencies
|-- .gitignore
|-- README.md
|-- TECHNICAL_DOCUMENTATION.md
```

> Directories that are **auto-generated at runtime** and therefore not in the repo:
> `data/`, `models/`, `attendance_records/`, `logs/`

---

## Setup

### Prerequisites

- Python 3.9 or higher
- A GPU is recommended for faster embedding generation but is not required

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/smart-attendance-system.git
cd smart-attendance-system/SMART_ATTENDENCE_SYSTEM

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

Model weights for MTCNN and FaceNet are downloaded automatically on first run via the `mtcnn` and `keras-facenet` packages. No manual download is required.

---

## Usage

All commands are run from inside the `src/` directory.

```bash
cd src
```

### Phase 1 — Build the Embedding Database

Prepare your raw videos:

```
data/raw_videos/
    student_name_1/
        video1.mp4
    student_name_2/
        video1.mp4
```

Then run:

```bash
python main.py
# Enter choice: 1
```

This will populate `data/embeddings/embeddings.pkl` and `data/embeddings/labels.pkl`.

### Phase 2 — Run Attendance on a Group Image

Place one or more classroom photos in `data/group_images/`, then run:

```bash
python main.py
# Enter choice: 2
```

The system processes every image in the folder, marks attendance for all recognised students, and saves the result to `attendance_records/`.

---

## Dependencies

| Package          | Purpose                              |
|------------------|--------------------------------------|
| mtcnn            | Multi-task CNN face detection        |
| keras-facenet    | Pre-trained FaceNet model (512-D)    |
| opencv-python    | Image I/O and drawing                |
| numpy            | Numerical operations                 |
| pandas           | Attendance CSV management            |
| tensorflow       | Backend for FaceNet inference        |
| joblib           | Serialisation utilities              |

Install all dependencies with:

```bash
pip install -r requirements.txt
```

---

## How the Matching Works

Face matching uses Euclidean distance in 512-dimensional embedding space:

```
distance = ||embedding_query - embedding_database||_2
```

- If `distance <= 0.6` : the face is assigned the identity of the nearest database entry.
- If `distance > 0.6`  : the face is marked as Unknown.

The threshold of 0.6 was selected empirically. It can be adjusted in the matching configuration to trade off between false positives (too permissive) and false negatives (too strict).

---

## Limitations and Known Constraints

- Accuracy drops under low lighting, heavy occlusion, or extreme pose angles.
- The system requires at least one clear, forward-facing video per student during enrolment.
- Very large class sizes (50+ students in a single image) may increase inference time.
- The `.pkl` database must be rebuilt if a new student is added.

---

## Future Work

- Incremental database updates without full rebuild.
- Real-time video stream support.
- Integration with a college ERP system via REST API.
- Fine-tuning FaceNet on a domain-specific student dataset to further improve accuracy.

---

## License

This project is intended for academic and research use.
