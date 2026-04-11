import numpy as np
import os
import cv2
from keras_facenet import FaceNet

embedder = FaceNet()

def generate_embeddings(input_folder):
    embeddings = []

    for img_name in os.listdir(input_folder):
        img_path = os.path.join(input_folder, img_name)
        img = cv2.imread(img_path)

        if img is None:
            continue

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Expand dimensions for model
        img = np.expand_dims(img, axis=0)

        embedding = embedder.embeddings(img)[0]
        embeddings.append(embedding)

    return embeddings