from mtcnn import MTCNN
import cv2
import os

detector = MTCNN()

def detect_and_crop_faces(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for img_name in os.listdir(input_folder):
        img_path = os.path.join(input_folder, img_name)
        img = cv2.imread(img_path)

        if img is None:
            continue

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = detector.detect_faces(rgb_img)
        # results is an object returned by detect faces which has bounding box[x,y,w,h]
        # and the confidence score like (0.998) and the 5 facial landmarks eye(l,r) mouth(lend,rend),nose

        for i, result in enumerate(results):
            # iterating over all detected faces
            x, y, w, h = result['box']

            # Fix negative values
            x, y = max(0, x), max(0, y)

            face = img[y:y+h, x:x+w]

            face_filename = os.path.join(output_folder, f"{img_name}_face{i}.jpg")
            cv2.imwrite(face_filename, face)

    print(f"[INFO] Faces saved to {output_folder}")