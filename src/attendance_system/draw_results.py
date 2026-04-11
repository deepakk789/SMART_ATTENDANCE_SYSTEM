import cv2

def draw_results(image, boxes, names):
    for (box, name) in zip(boxes, names):
        x, y, w, h = box

        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

        cv2.rectangle(image, (x, y), (x+w, y+h), color, 2)
        cv2.putText(image, name, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    return image