import cv2
import os

def align_faces(input_folder, output_folder, size=(160, 160)):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for img_name in os.listdir(input_folder):
        img_path = os.path.join(input_folder, img_name)
        img = cv2.imread(img_path)

        if img is None:
            continue

        face = cv2.resize(img, size)

        save_path = os.path.join(output_folder, img_name)
        cv2.imwrite(save_path, face)

    print(f"[INFO] Faces aligned and saved to {output_folder}")