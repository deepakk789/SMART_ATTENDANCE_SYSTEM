import os
import cv2
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# Fix paths to allow running from src/
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from attendance_system.detect_faces import detect_faces
from attendance_system.generate_embeddings import get_embeddings
from attendance_system.match_faces import load_database, match_faces

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DATA_DIR = os.path.join(BASE_DIR, "data", "test_dataset")
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "data", "embeddings")
METRICS_DIR = os.path.join(BASE_DIR, "metrics")

os.makedirs(METRICS_DIR, exist_ok=True)

def evaluate_system():
    print("EVALUATING SMART ATTENDANCE SYSTEM")
    
    if not os.path.exists(TEST_DATA_DIR):
        print(f"[ERROR] Test dataset folder not found at {TEST_DATA_DIR}")
        print("Please create it and organize photos inside it like this:")
        print("data/test_dataset/student_A/img1.jpg")
        print("data/test_dataset/Unknown/img1.jpg")
        return

    # Load the trained database (embeddings)
    try:
        database = load_database(EMBEDDINGS_DIR)
        print(f"[INFO] Loaded database with {len(database)} students.")
    except Exception as e:
        print(f"[ERROR] Could not load database from {EMBEDDINGS_DIR}. Error: {e}")
        return

    y_true = []
    y_pred = []

    print("\n[INFO] Starting Evaluation...\n")
    
    # Loop through each folder (True Label) in test dataset
    for person_name in os.listdir(TEST_DATA_DIR):
        person_dir = os.path.join(TEST_DATA_DIR, person_name)
        
        if not os.path.isdir(person_dir):
            continue
            
        print(f"Evaluating folder: {person_name}")
        
        for img_name in os.listdir(person_dir):
            img_path = os.path.join(person_dir, img_name)
            
            # Detect faces in the test image
            try:
                faces, boxes, image = detect_faces(img_path)
            except Exception as e:
                print(f"  [WARNING] Could not process {img_name}: {e}")
                continue
                
            if len(faces) == 0:
                print(f"  [WARNING] No face found in {img_name}. Skipping.")
                continue
            
            # If multiple faces are in one individual photo, we just take the biggest/first one
            # for individual component testing
            face = [faces[0]] 
            
            # Get Embeddings
            embeddings = get_embeddings(face)
            
            # Match Faces
            identified_names = match_faces(embeddings, database)
            predicted_name = identified_names[0]
            
            y_true.append(person_name)
            y_pred.append(predicted_name)
            
            print(f"  - {img_name} -> Predicted: {predicted_name} | Actual: {person_name}")

    if len(y_true) == 0:
        print("\n[ERROR] No test images were successfully processed.")
        return

    # CALCULATE METRICS
    print("\nFINAL RESULTS")
    
    accuracy = accuracy_score(y_true, y_pred)
    print(f"\nOverall Accuracy: {accuracy * 100:.2f}%\n")
    
    print("Classification Report:")
    report = classification_report(y_true, y_pred, zero_division=0)
    print(report)
    
    # Save Classification Report to text file
    with open(os.path.join(METRICS_DIR, "classification_report.txt"), "w") as f:
        f.write(f"Overall Accuracy: {accuracy * 100:.2f}%\n\n")
        f.write("Classification Report:\n")
        f.write(report)
        
    # Generate Confusion Matrix
    labels = sorted(list(set(y_true) | set(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Face Recognition Confusion Matrix')
    plt.ylabel('Actual Label (Ground Truth)')
    plt.xlabel('Predicted Label')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    cm_path = os.path.join(METRICS_DIR, "confusion_matrix.png")
    plt.savefig(cm_path)
    print(f"\n[INFO] Metrics saved to {METRICS_DIR}")
    print(f"[INFO] Confusion Matrix image saved as: {cm_path}")

if __name__ == "__main__":
    evaluate_system()
