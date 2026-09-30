"""Text extraction from pre-processed images using PaddleOCR or Tesseract."""
import threading
from typing import Tuple

import cv2
import numpy as np
import pytesseract
from paddleocr import PaddleOCR
from PIL import Image

from app.config import TESSERACT_CMD

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

_paddle_ocr_instance = None
_paddle_lock = threading.Lock()


def _get_paddle_ocr() -> PaddleOCR:
    global _paddle_ocr_instance
    if _paddle_ocr_instance is None:
        with _paddle_lock:
            if _paddle_ocr_instance is None:
                # cpu_threads=1 avoids an intermittent oneDNN "could not execute
                # a primitive" crash seen on repeated inference calls when
                # PaddleOCR auto-detects a higher CPU thread count.
                _paddle_ocr_instance = PaddleOCR(use_angle_cls=True, lang="en", cpu_threads=1)
    return _paddle_ocr_instance


def recognize_with_paddleocr(image: np.ndarray) -> Tuple[str, float]:
    ocr = _get_paddle_ocr()
    result = ocr.ocr(image, cls=True)

    lines, scores = [], []
    if result and result[0]:
        for _box, (text, score) in result[0]:
            text = text.strip()
            if text:
                lines.append(text)
                scores.append(score)

    text = "\n".join(lines)
    confidence = sum(scores) / len(scores) if scores else 0.0
    return text, confidence


def recognize_with_tesseract(image: np.ndarray) -> Tuple[str, float]:
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)

    words, confidences = [], []
    for word, conf in zip(data["text"], data["conf"]):
        word = word.strip()
        try:
            conf_value = float(conf)
        except (TypeError, ValueError):
            continue
        if word and conf_value >= 0:
            words.append(word)
            confidences.append(conf_value)

    text = " ".join(words)
    confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0
    return text, confidence


def extract_text_from_image(image: np.ndarray, engine: str = "paddleocr") -> Tuple[str, float]:
    if engine == "tesseract":
        return recognize_with_tesseract(image)
    return recognize_with_paddleocr(image)
