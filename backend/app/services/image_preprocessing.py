"""Image pre-processing pipeline using OpenCV.

Steps: decode -> grayscale -> noise reduction (denoising) -> adaptive thresholding.
"""
import cv2
import numpy as np


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Returns a cleaned, binarized (3-channel) image ready for OCR."""
    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Unable to decode image file.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    thresholded = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    # OCR engines generally expect a 3-channel image.
    return cv2.cvtColor(thresholded, cv2.COLOR_GRAY2BGR)
