from mtcnn import MTCNN
import cv2

detector = MTCNN()

def detect_faces(image_path):
    img = cv2.imread(image_path)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    results = detector.detect_faces(rgb_img)

    faces = []
    boxes = []

    for result in results:
        x, y, w, h = result['box']

        x, y = max(0, x), max(0, y)

        face = img[y:y+h, x:x+w]
        face = cv2.resize(face, (160, 160))

        faces.append(face)
        boxes.append((x, y, w, h))

    return faces, boxes, img