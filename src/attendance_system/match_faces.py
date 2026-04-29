import numpy as np
import pickle

def load_database(db_path):
    with open(f"{db_path}/embeddings.pkl", "rb") as f:
        database = pickle.load(f)

    return database


def match_faces(embeddings, database, threshold=0.6):
    identified = []
    
    # Check if database is empty to prevent errors
    if not database:
        return ["Unknown"] * len(embeddings)

    # 1. Flatten the database for vectorization
    # We do this to take advantage of Numpy's C-level optimizations
    db_labels = []
    db_matrix = []
    
    for person, db_embeds in database.items():
        for db_emb in db_embeds:
            db_labels.append(person)
            db_matrix.append(db_emb)
            
    db_matrix = np.array(db_matrix)
    db_labels = np.array(db_labels)

    # 2. Vectorized matching
    for emb in embeddings:
        # Calculate Euclidean distance against ALL database embeddings simultaneously
        distances = np.linalg.norm(db_matrix - emb, axis=1)
        
        # Find the index of the minimum distance
        min_idx = np.argmin(distances)
        min_dist = distances[min_idx]
        
        # Check if the closest match is within our confidence threshold
        if min_dist < threshold:
            identified.append(db_labels[min_idx])
        else:
            identified.append("Unknown")

    return identified