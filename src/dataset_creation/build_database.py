import os
import pickle
from .generate_embeddings import generate_embeddings

def build_database(processed_faces_dir, output_path):
    database = {}
    labels = []

    for person_name in os.listdir(processed_faces_dir):
        person_folder = os.path.join(processed_faces_dir, person_name)

        if not os.path.isdir(person_folder):
            continue

        print(f"[INFO] Processing {person_name}...")

        embeddings = generate_embeddings(person_folder)

        database[person_name] = embeddings
        labels.append(person_name)

    # Save database
    with open(os.path.join(output_path, "embeddings.pkl"), "wb") as f:
        pickle.dump(database, f)

    with open(os.path.join(output_path, "labels.pkl"), "wb") as f:
        pickle.dump(labels, f)

    print("[INFO] Database created successfully!")

def update_database(person_name, processed_faces_dir, output_path):
    person_folder = os.path.join(processed_faces_dir, person_name)
    
    if not os.path.isdir(person_folder):
        print(f"[ERROR] Processed faces for {person_name} not found!")
        return

    print(f"[INFO] Generating embeddings for {person_name}...")
    new_embeddings = generate_embeddings(person_folder)

    db_file = os.path.join(output_path, "embeddings.pkl")
    labels_file = os.path.join(output_path, "labels.pkl")
    
    database = {}
    labels = []
    
    if os.path.exists(db_file):
        with open(db_file, "rb") as f:
            database = pickle.load(f)
    if os.path.exists(labels_file):
        with open(labels_file, "rb") as f:
            labels = pickle.load(f)
            
    database[person_name] = new_embeddings
    if person_name not in labels:
        labels.append(person_name)
        
    with open(db_file, "wb") as f:
        pickle.dump(database, f)
    with open(labels_file, "wb") as f:
        pickle.dump(labels, f)
        
    print(f"[INFO] Database updated successfully for {person_name}!")