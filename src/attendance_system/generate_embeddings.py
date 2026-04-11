import numpy as np
import cv2
from keras_facenet import FaceNet

embedder = FaceNet()

def get_embeddings(faces):
    embeddings = []

    for face in faces:
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        face = np.expand_dims(face, axis=0)

        embedding = embedder.embeddings(face)[0]
        embeddings.append(embedding)

    return embeddings