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