import cv2

def apply_clahe(img):
    # Convert BGR to LAB color space
    # L = Lightness (brightness), A and B = color channels
    # We only enhance the lightness channel to avoid color distortion
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # clipLimit=2.0  -> limits contrast amplification to prevent noise from being over-amplified
    # tileGridSize=(8,8) -> divides image into 8x8 tiles for localized contrast correction
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)

    # Merge enhanced lightness back with original color channels
    limg = cv2.merge((cl, a, b))

    # Convert back from LAB to BGR
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
