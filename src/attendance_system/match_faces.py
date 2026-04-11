import numpy as np
import pickle

def load_database(db_path):
    with open(f"{db_path}/embeddings.pkl", "rb") as f:
        database = pickle.load(f)

    return database


def euclidean_distance(a, b):
    return np.linalg.norm(a - b)


def match_faces(embeddings, database, threshold=0.6):
    identified = []

    for emb in embeddings:
        name = "Unknown"
        min_dist = float("inf")

        for person, db_embeds in database.items():
            for db_emb in db_embeds:
                dist = euclidean_distance(emb, db_emb)

                if dist < min_dist:
                    min_dist = dist
                    name = person

        if min_dist > threshold:
            name = "Unknown"

        identified.append(name)

    return identified