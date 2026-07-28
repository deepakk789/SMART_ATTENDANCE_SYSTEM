import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logging
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # Suppress oneDNN warning
import tensorflow as tf

# Phase 1 Imports
from dataset_creation.extract_frames import extract_frames
from dataset_creation.detect_faces import detect_and_crop_faces
from dataset_creation.align_faces import align_faces
from dataset_creation.build_database import build_database, update_database

# Phase 2 Imports
from attendance_system.detect_faces import detect_faces
from attendance_system.generate_embeddings import get_embeddings
from attendance_system.match_faces import load_database, match_faces
from attendance_system.mark_attendance import mark_attendance
from attendance_system.draw_results import draw_results

import cv2

# Path Resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Config
RAW_VIDEO_DIR = os.path.join(BASE_DIR, "data", "raw_videos")
FRAMES_DIR = os.path.join(BASE_DIR, "data", "extracted_frames")
FACES_DIR = os.path.join(BASE_DIR, "data", "processed_faces")
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "data", "embeddings")
GROUP_IMAGE_DIR = os.path.join(BASE_DIR, "data", "group_images")

# Ensure directories exist
for directory in [RAW_VIDEO_DIR, FRAMES_DIR, FACES_DIR, EMBEDDINGS_DIR, GROUP_IMAGE_DIR]:
    os.makedirs(directory, exist_ok=True)

# Phase 1
def create_dataset():
    print("\n[PHASE 1] Creating Dataset...\n")

    for student_name in os.listdir(RAW_VIDEO_DIR):
        video_folder = os.path.join(RAW_VIDEO_DIR, student_name)

        for video_file in os.listdir(video_folder):
            video_path = os.path.join(video_folder, video_file)

            # Step 1: Extract Frames
            frame_output = os.path.join(FRAMES_DIR, student_name)
            extract_frames(video_path, frame_output)

            # Step 2: Detect Faces
            face_output = os.path.join(FACES_DIR, student_name)
            detect_and_crop_faces(frame_output, face_output)

            # Step 3: Align Faces
            align_faces(face_output, face_output)

    # Step 4: Build Database
    build_database(FACES_DIR, EMBEDDINGS_DIR)

    print("\n[INFO] Dataset Ready!\n")


def add_single_student():
    student_name = input("Enter the student name to add: ").strip()
    if not student_name:
        print("[ERROR] Invalid student name!")
        return

    student_video_dir = os.path.join(RAW_VIDEO_DIR, student_name)
    
    if not os.path.exists(student_video_dir):
        print(f"[ERROR] Directory for {student_name} not found in {RAW_VIDEO_DIR}!")
        return

    print(f"\n[INFO] Adding single student: {student_name}...\n")
    
    for video_file in os.listdir(student_video_dir):
        video_path = os.path.join(student_video_dir, video_file)
        
        # Step 1: Extract Frames
        frame_output = os.path.join(FRAMES_DIR, student_name)
        extract_frames(video_path, frame_output)
        
        # Step 2: Detect Faces
        face_output = os.path.join(FACES_DIR, student_name)
        detect_and_crop_faces(frame_output, face_output)
        
        # Step 3: Align Faces
        align_faces(face_output, face_output)

    # Step 4: Update Database for single student
    update_database(student_name, FACES_DIR, EMBEDDINGS_DIR)


# Phase 2
def run_attendance(image_path):
    print("\n[PHASE 2] Running Attendance...\n")

    # Step 1: Detect Faces
    faces, boxes, image = detect_faces(image_path)

    # Step 2: Generate Embeddings
    embeddings = get_embeddings(faces)

    # Step 3: Load Database
    database = load_database(EMBEDDINGS_DIR)

    # Step 4: Match Faces
    names = match_faces(embeddings, database)

    # Step 5 is removed here to prevent duplicate attendance marking.
    # Attendance is now only marked once at the end of all processing.

    # Step 6: Draw Results
    result_image = draw_results(image, boxes, names)

    # Show result
    cv2.imshow("Attendance System", result_image)
    cv2.waitKey(3000) # Window will close automatically after 3 seconds
    cv2.destroyAllWindows()

    print("\n[INFO] Attendance Completed!\n")
    return names


# Main
if __name__ == "__main__":
    print("SMART ATTENDANCE SYSTEM")

    print("\n1. Create complete database from zero")
    print("2. Add new entry in db only")
    print("3. Mark attendance for all photos")
    print("4. Mark attendance for single photo")

    choice = input("\nEnter choice (1/2/3/4): ").strip()

    if choice == "1":
        create_dataset()

    elif choice == "2":
        add_single_student()

    elif choice == "3":
        images = os.listdir(GROUP_IMAGE_DIR)

        if len(images) == 0:
            print("[ERROR] No group images found!")
        else:
            detected_students = {}

            for img in images:
                image_path = os.path.join(GROUP_IMAGE_DIR, img)
                print(f"\n[INFO] Processing {img}...")
        
                names = run_attendance(image_path)
                
                for name in names:
                    if name != "Unknown" and name not in detected_students:
                        detected_students[name] = img

            from attendance_system.mark_attendance import mark_attendance
            mark_attendance(detected_students)

    elif choice == "4":
        images = os.listdir(GROUP_IMAGE_DIR)
        
        if len(images) == 0:
            print("[ERROR] No group images found!")
        else:
            print("\nAvailable images:")
            for idx, img in enumerate(images):
                print(f"{idx + 1}. {img}")
            
            img_choice = input("\nEnter image number to process: ").strip()
            
            try:
                img_idx = int(img_choice) - 1
                if 0 <= img_idx < len(images):
                    selected_img = images[img_idx]
                    image_path = os.path.join(GROUP_IMAGE_DIR, selected_img)
                    print(f"\n[INFO] Processing {selected_img}...")
                    
                    names = run_attendance(image_path)
                    
                    detected_students = {}
                    for name in names:
                        if name != "Unknown" and name not in detected_students:
                            detected_students[name] = selected_img
                            
                    if detected_students:
                        from attendance_system.mark_attendance import mark_attendance
                        mark_attendance(detected_students)
                    else:
                        print("\n[INFO] No known students detected in this photo.")
                else:
                    print("[ERROR] Invalid image number!")
            except ValueError:
                print("[ERROR] Please enter a valid number!")

    else:
        print("Invalid choice!")